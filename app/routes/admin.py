from __future__ import annotations

from datetime import datetime, timezone
import hmac
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Question
from app.seeding import seed_questions_if_empty
from app.security import (
    ADMIN_SESSION_COOKIE,
    ADMIN_SESSION_MAX_AGE_SECONDS,
    get_admin_credentials,
    is_admin_authenticated,
    make_admin_session,
    require_admin,
)
from app.services.tokens import new_url_token

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))

CSRF_COOKIE = "csrf_token"


def _get_or_set_csrf(request: Request, response: Response) -> str:
    csrf = request.cookies.get(CSRF_COOKIE)
    if csrf:
        return csrf
    csrf = new_url_token(16)
    response.set_cookie(CSRF_COOKIE, csrf, httponly=True, samesite="lax")
    return csrf


def _require_csrf(request: Request, csrf_token: str) -> None:
    cookie = request.cookies.get(CSRF_COOKIE)
    if not cookie or cookie != csrf_token:
        raise HTTPException(status_code=403, detail="CSRF 校验失败")


def _safe_next(next_url: str | None) -> str:
    if not next_url:
        return "/admin/questions"
    if not next_url.startswith("/admin"):
        return "/admin/questions"
    return next_url


@router.get("/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    if is_admin_authenticated(request):
        return RedirectResponse(url=_safe_next(request.query_params.get("next")), status_code=303)

    response = templates.TemplateResponse(
        request,
        "admin_login.html",
        {"error_message": None, "next": _safe_next(request.query_params.get("next"))},
    )
    csrf = _get_or_set_csrf(request, response)
    response.context["csrf_token"] = csrf
    return response


@router.post("/login")
def admin_login_submit(
    request: Request,
    csrf_token: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/admin/questions"),
):
    _require_csrf(request, csrf_token)

    expected_username, expected_password = get_admin_credentials()
    if not expected_username or not expected_password:
        raise HTTPException(status_code=503, detail="管理员账号未配置")

    if not (
        hmac.compare_digest(username, expected_username)
        and hmac.compare_digest(password, expected_password)
    ):
        response = templates.TemplateResponse(
            request,
            "admin_login.html",
            {"error_message": "用户名或密码错误", "next": _safe_next(next)},
        )
        csrf = _get_or_set_csrf(request, response)
        response.context["csrf_token"] = csrf
        return response

    session_value = make_admin_session(expected_username)
    response = RedirectResponse(url=_safe_next(next), status_code=303)
    response.set_cookie(
        ADMIN_SESSION_COOKIE,
        session_value,
        httponly=True,
        samesite="lax",
        max_age=ADMIN_SESSION_MAX_AGE_SECONDS,
        path="/admin",
        secure=request.url.scheme == "https",
    )
    return response


@router.post("/logout")
def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(ADMIN_SESSION_COOKIE, path="/admin")
    return response


@router.get("", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def admin_index():
    return RedirectResponse(url="/admin/questions", status_code=303)


@router.get("/questions", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def list_questions(request: Request, db: Session = Depends(get_db), dimension: str | None = None):
    seed_questions_if_empty(db)
    q = db.query(Question)
    if dimension:
        q = q.filter(Question.dimension == dimension)
    questions = q.order_by(Question.id.desc()).limit(500).all()

    response = templates.TemplateResponse(
        request,
        "admin_questions.html",
        {"questions": questions, "dimension": dimension or "", "now": datetime.now(timezone.utc)},
    )
    csrf = _get_or_set_csrf(request, response)
    response.context["csrf_token"] = csrf
    return response


@router.get("/questions/new", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def new_question(request: Request):
    response = templates.TemplateResponse(
        request,
        "admin_edit_question.html",
        {"question": None, "mode": "new"},
    )
    csrf = _get_or_set_csrf(request, response)
    response.context["csrf_token"] = csrf
    return response


@router.post("/questions/new", dependencies=[Depends(require_admin)])
def create_question(
    request: Request,
    db: Session = Depends(get_db),
    csrf_token: str = Form(...),
    dimension: str = Form(...),
    agree_pole: str = Form(...),
    text: str = Form(...),
    is_active: bool = Form(False),
    source: str = Form("ai"),
):
    _require_csrf(request, csrf_token)
    q = Question(
        dimension=dimension.strip().upper(),
        agree_pole=agree_pole.strip().upper()[:1],
        text=text.strip(),
        is_active=bool(is_active),
        source=source.strip() or "ai",
    )
    db.add(q)
    db.commit()
    return RedirectResponse(url=f"/admin/questions/{q.id}", status_code=303)


@router.get("/questions/{question_id}", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def edit_question(question_id: int, request: Request, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == int(question_id)).one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    response = templates.TemplateResponse(
        request,
        "admin_edit_question.html",
        {"question": q, "mode": "edit"},
    )
    csrf = _get_or_set_csrf(request, response)
    response.context["csrf_token"] = csrf
    return response


@router.post("/questions/{question_id}", dependencies=[Depends(require_admin)])
def update_question(
    question_id: int,
    request: Request,
    db: Session = Depends(get_db),
    csrf_token: str = Form(...),
    dimension: str = Form(...),
    agree_pole: str = Form(...),
    text: str = Form(...),
    is_active: bool = Form(False),
    source: str = Form("ai"),
):
    _require_csrf(request, csrf_token)
    q = db.query(Question).filter(Question.id == int(question_id)).one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    q.dimension = dimension.strip().upper()
    q.agree_pole = agree_pole.strip().upper()[:1]
    q.text = text.strip()
    q.is_active = bool(is_active)
    q.source = source.strip() or "ai"
    db.commit()
    return RedirectResponse(url=f"/admin/questions/{q.id}", status_code=303)


@router.post("/questions/{question_id}/toggle", dependencies=[Depends(require_admin)])
def toggle_question(
    question_id: int,
    request: Request,
    db: Session = Depends(get_db),
    csrf_token: str = Form(...),
):
    _require_csrf(request, csrf_token)
    q = db.query(Question).filter(Question.id == int(question_id)).one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    q.is_active = not bool(q.is_active)
    db.commit()
    return RedirectResponse(url="/admin/questions", status_code=303)


@router.get("/export", dependencies=[Depends(require_admin)])
def export_questions(db: Session = Depends(get_db)):
    qs = db.query(Question).order_by(Question.id.asc()).all()
    data: list[dict[str, Any]] = []
    for q in qs:
        data.append(
            {
                "dimension": q.dimension,
                "agree_pole": q.agree_pole,
                "text": q.text,
                "is_active": bool(q.is_active),
                "source": q.source,
            }
        )
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        content=payload,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=questions.json"},
    )


@router.post("/import", dependencies=[Depends(require_admin)])
def import_questions(
    request: Request,
    db: Session = Depends(get_db),
    csrf_token: str = Form(...),
    file: UploadFile = File(...),
):
    _require_csrf(request, csrf_token)
    raw = file.file.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail="JSON 解析失败") from e

    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="JSON 顶层必须是数组")

    inserted = 0
    for row in data:
        if not isinstance(row, dict):
            continue
        dim = str(row.get("dimension", "")).strip().upper()
        pole = str(row.get("agree_pole", "")).strip().upper()[:1]
        text = str(row.get("text", "")).strip()
        if not dim or not pole or not text:
            continue
        q = Question(
            dimension=dim,
            agree_pole=pole,
            text=text,
            is_active=bool(row.get("is_active", True)),
            source=str(row.get("source", "ai"))[:20],
        )
        db.add(q)
        inserted += 1
    db.commit()
    return RedirectResponse(url="/admin/questions", status_code=303)

