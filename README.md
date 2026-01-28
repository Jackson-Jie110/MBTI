# MBTI 在线测试（FastAPI）

一个轻量的 MBTI 在线测试网站：用户选择题量模式（20/40/60 题），系统从题库中按四个维度均衡抽题，支持上一题/下一题/保存退出（同一浏览器继续），完成后生成「类型 + 四维百分比 + 完整报告」，并可生成匿名分享链接。

## 功能
- 三种模式：20 / 40 / 60 题（EI / SN / TF / JP 均衡抽题）
- 5 级量表：一题一页，支持上一题/下一题/保存并退出
- 自动加测：维度接近边界（差距 <10%）最多额外 +10 题
- 报告输出：仅展示「类型 + 四维百分比 + 完整报告」（不展示逐题明细）
- 结果分享：生成匿名分享链接（有效期在提交时选择）
- 管理后台：`/admin` 维护题库（新增/编辑/启用停用/导入导出 JSON）
- 不提供跨设备续测：仅支持同一浏览器内继续答题（cookie 会话）

## 技术栈
- 后端：FastAPI
- 模板：Jinja2（SSR 服务端渲染）
- ORM：SQLAlchemy 2.x
- 数据库：本地开发 SQLite；线上部署推荐 Postgres
- 测试：pytest + httpx TestClient

## 本地运行（Windows / PowerShell）
在项目根目录执行：
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
```

初始化题库（写入本地 `mbti.db`，可选；应用也会在库为空时自动初始化）：
```powershell
.\.venv\Scripts\python scripts\seed_questions.py
```

启动服务：
```powershell
.\.venv\Scripts\uvicorn app.main:app --reload
```

访问：
- 首页：`http://127.0.0.1:8000/`
- 管理后台：`http://127.0.0.1:8000/admin`

## 管理后台（/admin）
- 若配置了 `MBTI_ADMIN_USERNAME` / `MBTI_ADMIN_PASSWORD`：访问 `/admin` 需要登录
- 若未配置：为方便本地开发，管理后台仅允许本机访问（线上等同于“无法访问”，请务必配置账号）

## 环境变量
- `MBTI_DATABASE_URL`（推荐线上配置）
  - 默认：`sqlite:///./mbti.db`
  - 线上建议：Postgres 连接串（`postgres://...` 或 `postgresql://...` 均可）
  - 也支持平台默认的 `DATABASE_URL`
- `MBTI_APP_SECRET`
  - 用于分享链接/登录态的签名与哈希匹配
  - 建议线上设置为固定的随机长字符串；变更会导致已有分享链接、已登录会话失效
- `MBTI_ADMIN_USERNAME` / `MBTI_ADMIN_PASSWORD`
  - 管理后台登录账号密码

## 部署到 Vercel（GitHub + 自定义域名）
> 详细步骤见：`docs/plans/2026-01-28-vercel-deploy-plan.md`

1) 推送到 GitHub 后，在 Vercel 创建项目：`Add New...` → `Project` → Import 你的仓库 → Deploy
2) 创建数据库（推荐 Vercel Postgres）：项目 → `Storage` → `Create` → `Postgres`
3) 在 Vercel 项目环境变量（Production）中设置：
   - `MBTI_DATABASE_URL`：Postgres 连接串
   - `MBTI_APP_SECRET`：随机长字符串
   - `MBTI_ADMIN_USERNAME` / `MBTI_ADMIN_PASSWORD`
4) Redeploy 后验证：访问 `/`、完成一次测试、生成分享链接、登录 `/admin`
5) 绑定自定义域名：项目 → `Settings` → `Domains` 添加域名，并按页面提示配置 DNS；建议设置一个 Primary Domain 并把别名域 301 到主域，避免 cookie 分裂影响“继续答题”。

## 测试
```powershell
.\.venv\Scripts\pytest -q
```

## 免责声明
本测试仅用于自我了解与娱乐参考，不构成专业心理评估或诊断。
