# Vercel（GitHub + 自定义域名）部署方案

**目标：**把本项目部署到 Vercel（FastAPI 动态网站），使用 Postgres（推荐 Vercel Postgres），并绑定自定义域名、开启 HTTPS。

> 重点：Vercel 的运行环境是无状态的，**不建议线上使用 SQLite 文件数据库**。本项目本地可用 `mbti.db`，线上请用 Postgres。

## Task 0：准备 GitHub 仓库
1) 在项目根目录初始化并提交（如已做可跳过）：
```powershell
git init
git branch -M main
git add .
git commit -m "init: mbti web"
```
2) GitHub 新建空仓库（不要自动生成 README）。
3) 绑定远程并推送：
```powershell
git remote add origin <你的仓库地址>
git push -u origin main
```

## Task 1：让 Vercel 能识别 FastAPI 入口
**文件：**`pyproject.toml`

本项目 FastAPI 实例在 `app/main.py` 的 `app` 变量上。Vercel FastAPI 部署会读取：
```toml
[project.scripts]
app = "app.main:app"
```

你不需要改业务代码；此配置仅用于告诉 Vercel：ASGI 应用在哪里。

## Task 2：在 Vercel 创建项目（GitHub 导入）
1) 登录 Vercel → `Add New...` → `Project`
2) 选择 GitHub 仓库 → `Import`
3) Framework 选择：
   - 如果 Vercel 能自动识别 FastAPI，直接继续
   - 识别不出来也没关系，关键是 `pyproject.toml` 的 `[project.scripts]` 已指向应用入口
4) 点击 `Deploy`，等待首次部署完成（先不绑域名，先用默认域名验证功能）

## Task 3：创建数据库（推荐 Vercel Postgres）
### 选项 A（推荐）：Vercel Postgres
1) 进入该项目 → `Storage` → `Create` → `Postgres`
2) 创建完成后，Vercel 会自动把连接串写入项目的环境变量（通常包含 `POSTGRES_URL` 等）
3) 在项目环境变量里新增（或直接复制一份）：
   - `MBTI_DATABASE_URL` = 你的 Postgres 连接串（建议用带 SSL 的那条）

### 选项 B：外部 Postgres（Neon / Supabase / Render / Railway 等）
1) 创建一个 Postgres 实例
2) 把连接串填到 Vercel 项目的环境变量：
   - `MBTI_DATABASE_URL` = `postgres://...` 或 `postgresql://...`

## Task 4：设置必要环境变量（Production 环境）
在 Vercel 项目 → `Settings` → `Environment Variables`：
- `MBTI_APP_SECRET`：随机长字符串（用于分享链接/登录态签名）
- `MBTI_ADMIN_USERNAME`：后台用户名
- `MBTI_ADMIN_PASSWORD`：后台密码
- `MBTI_DATABASE_URL`：Postgres 连接串（见 Task 3）

> 建议把这些变量设置在 **Production**；如果你要 Preview 环境也可用后台，再额外给 Preview 配一份（但最好用独立数据库）。

## Task 5：部署后验证（用默认 *.vercel.app 域名）
1) 打开首页 `/`
2) 做一次 20 题测试 → 出结果页
3) 点击“分享链接”打开，确认可访问
4) 访问 `/admin` → 跳转 `/admin/login` → 登录后进入题库管理
5) 首次打开 `/start` 或 `/admin/questions` 会自动建表并自动初始化题库（来自 `app/data/seed_questions.json`）

## Task 6：绑定自定义域名 + HTTPS
1) Vercel 项目 → `Settings` → `Domains`
2) 添加域名：
   - 推荐添加两个：`example.com` + `www.example.com`
3) 设置一个 **Primary Domain**（强烈建议只用一个主域做最终访问入口，避免 cookie 分裂）
4) 按 Vercel 页面提示在你的 DNS 服务商添加解析记录（以 Vercel 页面显示为准）：
   - `www` 通常是 CNAME
   - 根域通常是 A / ALIAS / ANAME（取决于 DNS 服务商能力）
5) 等待域名验证完成后，Vercel 会自动签发 HTTPS 证书
6) 用 `https://你的域名/` 再做一次 Task 5 的全套验证

## Task 7：把非主域 301 到主域（推荐）
目的：避免用户在 `www`/根域/默认域名之间切换导致“保存并退出后继续”失效（cookie 不共享）。

做法：在 Vercel 的 Domains 页面把主域设为 Primary，并开启把别名域重定向到主域（按 Vercel UI 操作）。

## 常见问题排查
- **部署后 500 / 连接不上数据库**：优先检查 `MBTI_DATABASE_URL` 是否正确、是否带 SSL（很多云 Postgres 要求）。
- **/admin 进不去**：确认已在 Vercel 配置 `MBTI_ADMIN_USERNAME` / `MBTI_ADMIN_PASSWORD`（不配会退化成“仅本机访问”）。
- **分享链接是 http 而不是 https**：先确认你是用 `https://` 访问的；若仍异常，告诉我，我可以加一个 `MBTI_PUBLIC_BASE_URL` 来强制生成外链域名/协议。

