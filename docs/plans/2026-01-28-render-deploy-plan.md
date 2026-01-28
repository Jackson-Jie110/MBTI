# Render（GitHub + 自定义域名）部署方案

**目标：**把本项目部署到 Render，使用 Render Postgres，绑定自定义域名并自动 HTTPS，对外稳定访问。

**前提：**
- 你有一个已购买的域名，且能修改 DNS 解析（域名控制台 / Cloudflare 等）。
- 你有 GitHub 账号与 Render 账号。

## 方案选择（推荐）
- **推荐：Blueprint（自动读取 `render.yaml`）**：创建 Web Service + Postgres + 环境变量映射，一次到位。
- 备选：手动创建 Web Service + Postgres（步骤更多，容易漏配）。

## Step 1：推送到 GitHub（第一次需要做）
1) 在项目根目录初始化仓库（如果还没建）：
```powershell
git init
git branch -M main
```
2) 在 GitHub 新建仓库（空仓库，不要勾选 README/License）。
3) 绑定远程并推送：
```powershell
git add .
git commit -m "init: mbti web"
git remote add origin <你的仓库地址>
git push -u origin main
```
> 注意：不要把本地 `.venv/`、`mbti.db` 推上去（已通过 `.gitignore` 忽略）。

## Step 2：用 Blueprint 部署到 Render
1) Render 控制台 → New → **Blueprint**
2) 连接 GitHub（按提示安装 Render GitHub App）
3) 选择仓库后，Render 会读取 `render.yaml` 并展示要创建的资源：
   - Web Service：`mbti-test`
   - Postgres：`mbti-db`
4) 配置环境变量（必填）：
   - `MBTI_ADMIN_USERNAME`
   - `MBTI_ADMIN_PASSWORD`
   - `MBTI_APP_SECRET`：Blueprint 会自动生成；建议复制保存，避免未来误删重建导致分享链接/登录态失效。
5) 点击 Apply / Create，等待首次部署完成。

## Step 3：上线后校验（强烈建议逐项做）
1) 打开首页 `/` 能正常访问
2) 完成一次 20 题测试，进入结果页
3) 点击结果分享链接，确认能正常打开（链接应为 `https://...`）
4) 访问 `/admin` → 跳转 `/admin/login` → 登录成功后可看到题库列表
5) 导出/导入题库（可选）：
   - 本地 `/admin/export` 下载 JSON
   - 线上 `/admin` 登录后在题库页底部导入

## Step 4：绑定自定义域名（建议统一主域）
**建议：只选一个主域名作为最终访问入口**（否则 cookie 不共享，可能导致“保存并退出后继续”在两个域名间不一致）。

1) Render → Web Service → Settings → **Custom Domains**
2) 添加你要的域名（常见两种）：
   - 根域：`example.com`
   - www：`www.example.com`
3) Render 会给出需要添加的 DNS 记录（按界面提示复制粘贴）：
   - `www` 通常是 **CNAME** 指向 Render 提供的目标
   - 根域通常是 **A/ALIAS/ANAME**（取决于 DNS 服务商能力）
4) 等待 DNS 生效后，Render 会自动签发/续期 HTTPS 证书。
5) 可选：把非主域做 301 跳转到主域（避免 cookie 分裂）。

