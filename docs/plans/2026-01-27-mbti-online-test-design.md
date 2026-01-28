# MBTI 在线测试网站（FastAPI + SQLite + SSR）设计稿

日期：2026-01-27

## 目标

做一个中文 MBTI 在线测试网站：用户进入后选择题量模式（20/40/60），按“一题一页”完成作答；系统按题库抽题并计算四维度与最终 4 字母类型，生成“类型 + 四维百分比 + 完整分析报告（优势/盲点/建议/适合方向等）”的结果页；支持匿名分享结果链接；支持跨设备“续测链接 + 续测码”继续未完成测试；当某维度接近边界时自动加测该维度题目（最多 +10）。

## 范围与约束

- 技术栈：`FastAPI` + `Jinja2`（服务端渲染 SSR）+ `SQLite`。
- 答题形式：5 级量表（非常不同意/不同意/一般/同意/非常同意）。
- 流程：一题一页；支持上一题修改；支持保存退出并继续。
- 模式：20/40/60 题；题越多结果越稳。
- 自动加测：某维度差距 < 10% 触发；最多追加 +10；仍接近则在报告中标注边界。
- 管理后台：仅允许本机访问（`127.0.0.1` / `::1`），不做登录；用于维护题库（AI 生成题库为主）与导入导出。
- 分享页只展示“类型 + 四维百分比 + 完整报告”，不展示每题明细。

## 用户流程（SSR 一题一页）

1. 入口页 `/`
   - 选择模式：20/40/60。
   - 选择“续测有效期”（1/7/30 天/永久），用于跨设备续测与本次测试可继续的时长控制。
   - 若检测到当前浏览器存在未完成会话（Cookie），展示“继续上次测试 / 重新开始”。
   - 支持输入“续测码”进入续测绑定（跨设备）。

2. 答题页 `/test`
   - 一题一页显示：题干 + 5 级量表。
   - 操作：`上一题` / `下一题` / `保存并退出`。
   - 允许回填已保存答案并修改；以“最后一次保存”为准，最终结算时统一按最新答案计算。
   - 页面提示并展示：续测链接、续测码（方便跨设备继续）。

3. 完成页 `/finish`
   - 基础题完成后执行计分与边界判定；若需加测则跳回 `/test` 继续追加题。
   - 若不需加测或已达加测上限：让用户选择“分享链接有效期”（1/7/30 天/永久），点击生成报告。

4. 结果页 `/result/{share_token}`
   - 展示：类型（如 `INTJ`）+ 四维百分比条形图 + 完整分析报告 + 分享链接复制。
   - 过期：提示失效并引导重新测试。

5. 续测页
   - `/resume/{resume_token}`：通过长 token 绑定到当前浏览器继续。
   - `/resume`：通过短码输入绑定继续（需简单限流防爆破）。

## 抽题、计分与加测

### 抽题（均衡覆盖）

- 从 `questions.is_active=1` 的题库中按维度均衡抽取：每个维度各 `N/4` 题。
  - 20 → 每维 5 题
  - 40 → 每维 10 题
  - 60 → 每维 15 题
- 题单生成后随机打散（保持四维度总体均衡），避免连续多题同一维度。
- 为支持 60 题 + 加测，题库建议每维 ≥ 25 题（15 基础 + 10 追加）。

### 量表计分（1–5 → -2..+2）

- 每题 `value` 为 1–5，映射为 `delta = value - 3`（即 -2,-1,0,+1,+2）。
- 每题属于一个维度 `dimension ∈ {EI,SN,TF,JP}`，并有 `agree_pole` 表示“越同意越偏向哪一端”：
  - 例如：`dimension=EI, agree_pole=E` 表示越同意越外向
  - 例如：`dimension=EI, agree_pole=I` 表示越同意越内向
- 维度累计分：
  - 若 `agree_pole` 是该维度第一端（EI 的 E、SN 的 S、TF 的 T、JP 的 J），则 `score += delta`
  - 否则 `score -= delta`
- 归一化成百分比：
  - 若某维作答题数为 `k`，最大绝对分 `max_abs = 2k`
  - 计算 `p = (score / max_abs) * 50 + 50` 得到“第一端百分比”（0–100），另一端为 `100-p`
- 类型判定：四维分别取更高一端组成 4 字母类型。

### 自动加测

- 在基础题完成后，若某维度两端差距 `< 10%`（即第一端百分比距离 50% 小于 5%），触发加测。
- 加测策略：从该维度剩余题库中追加 1 题到题单末尾（标记 `is_extra=1`），重复判定；最多追加 +10。
- 若达到上限仍接近：在报告中标注“该维度接近边界”。

## 数据模型（SQLite）

### questions（题库）

- `id`
- `dimension`：`EI/SN/TF/JP`
- `agree_pole`：`E/I/S/N/T/F/J/P`
- `text`
- `is_active`
- `source`：`ai/manual`
- `created_at` / `updated_at`

### tests（一次测试会话）

- `id`
- `mode`：20/40/60
- `target_count`：基础题数量
- `extra_max`：10
- `status`：`in_progress/completed/expired`
- `resume_expires_at`：续测/会话可继续截止时间（用户选择）
- `test_token_hash`：浏览器会话 token（仅存 hash）
- `resume_token_hash`：续测长 token（仅存 hash）
- `resume_code_hash`：续测短码（仅存 hash）
- `share_token_hash`：分享 token（仅存 hash）
- `share_expires_at`
- `result_type`：如 `INTJ`
- `result_json`：四维分数、百分比、边界标记等
- `created_at` / `completed_at`

### test_items（题单与顺序）

- `test_id`
- `position`：从 1 开始
- `question_id`
- `is_extra`

### answers（作答）

- `test_id`
- `question_id`
- `value`：1–5
- `answered_at`

## 令牌与安全边界

- Cookie：`test_token`（HttpOnly、SameSite=Lax），用于同设备快速续答。
- 数据库仅存 token 的 hash（推荐 `sha256(secret + token)`）；避免数据库泄露后直接接管会话。
- 续测：
  - 生成 `resume_token`（URL）+ `resume_code`（短码）。
  - 访问续测入口后，将该测试绑定到当前浏览器并下发新的 `test_token`。
  - 对短码尝试做 IP 级限流（简单时间窗即可）。
- 分享：
  - 完成后生成 `share_token`，只读展示结果与报告，不暴露每题细节。
- 管理后台：
  - `/admin` 路由仅允许 `127.0.0.1/::1` 访问。

## 项目结构（建议）

- `app/main.py`：FastAPI 入口与路由挂载
- `app/db.py`：SQLite 连接/Session
- `app/models.py`：SQLAlchemy 模型
- `app/services/selection.py`：均衡抽题/追加题
- `app/services/scoring.py`：计分/百分比/类型/边界判定
- `app/services/reporting.py`：类型与维度报告生成
- `app/routes/public.py`：开始/答题/续测/结果
- `app/routes/admin.py`：题库管理/导入导出
- `app/templates/`：Jinja2 页面
- `app/static/`：CSS/少量 JS
- `scripts/seed_questions.py`：初始 AI 题库入库
- `tests/`：pytest（单元+关键流程集成）

## 错误处理与用户提示

- 题库不足：明确提示缺少哪个维度/数量，并引导到 `/admin` 补题。
- token/code 无效或过期：提示失效并提供重新开始入口。
- 并发/覆盖：答案以“最后一次保存”为准。

