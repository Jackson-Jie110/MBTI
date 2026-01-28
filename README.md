# MBTI 在线测试（FastAPI + SQLite/Postgres）

功能概览：
- 三种模式：20 / 40 / 60 题（按四个维度均衡抽题）
- 5 级量表，一题一页，支持上一题/下一题/保存退出
- 维度接近边界（差距 <10%）自动加测，最多 +10 题
- 匿名分享结果链接（有效期在提交时选择）
- 不提供跨设备续测（仅支持同一浏览器内继续答题）
- 管理后台（/admin）：题库维护、导入/导出 JSON（已加登录保护；未配置账号时仅本机可访问）

## 快速开始

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
```

初始化题库（写入 `mbti.db`）：

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

## 环境变量

- `MBTI_DATABASE_URL`
  - 默认：`sqlite:///./mbti.db`
  - 示例：`sqlite:///D:/data/mbti.db`
  - 也支持使用平台默认的 `DATABASE_URL`
- `MBTI_APP_SECRET`
  - 用于对 `test_token / share_token / admin_session` 做签名/哈希匹配。
  - 建议在部署时设置为固定的随机长字符串；变更该值会导致已有分享链接/登录态失效。
- `MBTI_ADMIN_USERNAME` / `MBTI_ADMIN_PASSWORD`
  - 配置后，访问 `/admin` 需要登录
  - 未配置时，仅允许本机访问管理后台（用于本地开发）

## 部署到 Render（推荐）

方式 A：使用蓝图（推荐）
1) 把仓库推到 GitHub/GitLab
2) Render 新建 Blueprint，选择仓库（会读取 `render.yaml`）
3) 在 Render 控制台填写环境变量：`MBTI_ADMIN_USERNAME`、`MBTI_ADMIN_PASSWORD`
4) 首次打开网站或 `/admin/questions` 会自动初始化数据库与题库

方式 B：手动创建 Web Service
1) 新建 Web Service（Python）
2) Build Command：`pip install -r requirements.txt`
3) Start Command：`uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"`
4) 新建 Render Postgres，并把连接串写入 `MBTI_DATABASE_URL`（或使用平台默认的 `DATABASE_URL`）
5) 设置 `MBTI_APP_SECRET`、`MBTI_ADMIN_USERNAME`、`MBTI_ADMIN_PASSWORD`

## 测试

```powershell
.\.venv\Scripts\pytest -q
```

## 免责声明

本测试仅用于自我了解与娱乐参考，不构成专业心理评估或诊断。
