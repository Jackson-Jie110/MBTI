/* global marked */

function escapeHtml(raw) {
  return String(raw)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function cleanMarkdownText(text) {
  return String(text)
    // Strip known dirty tag
    .replace(/TAGS_SHORT_READ_WARNING\s+(true|false)\s*/g, "")
    // Strip internal AI error marker (used for front-end detection)
    .replace(/\s*AI_GENERATION_FAILED\s*/g, "")
    // 1) remove leading whitespace before headings
    .replace(/^\s+(#{1,6})/gm, "$1")
    // 2) normalize heading spaces (including full-width and nbsp)
    .replace(/(#{1,6})[\s\u3000\u00A0]+/gm, "$1 ")
    // 3) fix bold immediately after heading marker
    .replace(/(#{1,6} \*\*)[\s\u3000\u00A0]+/gm, "$1");
}

/**
 * 流式加载 Markdown 内容
 * @param {string} url - API 地址
 * @param {string} targetId - 内容显示容器 ID
 * @param {string} loadingId - 加载动画容器 ID
 * @param {object|null} payload - 可选：POST 的 JSON 数据；若提供则使用 POST
 */
async function loadStream(url, targetId, loadingId, payload = null, options = null) {
  const target = document.getElementById(targetId);
  const loading = document.getElementById(loadingId);
  if (!target) return false;

  const currentState = target.dataset.aiStreamState || "";
  if (currentState === "loading" || currentState === "done") {
    return currentState === "done";
  }
  target.dataset.aiStreamState = "loading";

  const onError = options && typeof options.onError === "function" ? options.onError : null;

  const showError = (msg) => {
    if (loading) {
      loading.style.display = "";
      loading.innerHTML = `<span style="color:#ef4444;font-weight:600">生成失败: ${escapeHtml(msg)}</span>`;
    }
  };

  const fetchOptions = payload
    ? {
        method: "POST",
        headers: { Accept: "text/plain", "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    : { method: "GET", headers: { Accept: "text/plain" } };

  try {
    const response = await fetch(url, fetchOptions);
    if (!response.ok) {
      const t = await response.text();
      throw new Error(`${response.status} ${t || response.statusText}`);
    }
    if (!response.body) {
      throw new Error("Streaming not supported in this browser");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let hasShown = false;
    let hasTriggeredStreamError = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      if (!chunk) continue;

      buffer += chunk;

      if (!hasTriggeredStreamError) {
        const hasErrorMarker = buffer.includes("AI_GENERATION_FAILED") || buffer.includes("❌ AI 生成失败");
        if (hasErrorMarker) {
          hasTriggeredStreamError = true;
          if (onError) {
            try {
              onError(new Error("AI_GENERATION_FAILED"));
            } catch {
              // ignore callback errors
            }
          }
        }
      }

      if (!hasShown) {
        hasShown = true;
        if (loading) loading.style.display = "none";
        target.classList.remove("hidden");
        target.style.display = "";
      }

      const cleanText = cleanMarkdownText(buffer);
      const safeText = escapeHtml(cleanText);

      if (typeof marked !== "undefined") {
        target.innerHTML = marked.parse(safeText);
      } else {
        target.innerHTML = safeText.replace(/\n/g, "<br/>");
      }
    }

    const success = !hasTriggeredStreamError;
    target.dataset.aiStreamState = success ? "done" : "error";
    return success;
  } catch (err) {
    target.dataset.aiStreamState = "error";
    console.error("Stream error:", err);
    if (onError) {
      try {
        onError(err);
      } catch {
        // ignore callback errors
      }
    }
    showError(err && err.message ? err.message : String(err));
    return false;
  }
}

function deriveResultAiUrl(pathname) {
  if (!pathname || /\/result\/ai_content\//.test(pathname)) {
    return "";
  }

  const replaced = pathname.replace(/\/result\/([^/]+)\/?$/, "/result/ai_content/$1");
  return replaced === pathname ? "" : replaced;
}

function getResultStreamConfig(overrideConfig = null) {
  const globalConfig =
    window.__resultAIStreamConfig && typeof window.__resultAIStreamConfig === "object"
      ? window.__resultAIStreamConfig
      : {};
  const override = overrideConfig && typeof overrideConfig === "object" ? overrideConfig : {};
  const merged = { ...globalConfig, ...override };

  const targetId = merged.targetId || "ai-result-box";
  const loadingId = merged.loadingId || "ai-loading-box";
  const target = document.getElementById(targetId);
  if (!target) {
    return null;
  }

  const url =
    merged.url ||
    merged.apiUrl ||
    target.getAttribute("data-stream-url") ||
    deriveResultAiUrl(window.location.pathname || "");
  if (!url) {
    return null;
  }

  const hasPayload = Object.prototype.hasOwnProperty.call(merged, "payload");
  const payload = hasPayload ? merged.payload : Object.fromEntries(new URLSearchParams(window.location.search));
  const onError =
    typeof merged.onError === "function"
      ? merged.onError
      : () => {
          if (typeof window.showAIErrorModal === "function") {
            window.showAIErrorModal();
          }
        };

  return {
    url,
    targetId,
    loadingId,
    payload,
    onError,
  };
}

async function autoStartResultStream(overrideConfig = null) {
  const config = getResultStreamConfig(overrideConfig);
  if (!config) {
    return false;
  }

  return loadStream(config.url, config.targetId, config.loadingId, config.payload, {
    onError: config.onError,
  });
}

function scheduleResultStreamStart(overrideConfig = null) {
  const run = () => {
    void autoStartResultStream(overrideConfig);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run, { once: true });
    return;
  }

  run();
}

function bindResultStreamLifecycle() {
  if (window.__resultStreamLifecycleBound) {
    return;
  }
  window.__resultStreamLifecycleBound = true;

  window.addEventListener("pageshow", () => {
    scheduleResultStreamStart();
  });

  document.addEventListener("htmx:load", () => {
    scheduleResultStreamStart();
  });

  document.addEventListener("htmx:afterSwap", () => {
    scheduleResultStreamStart();
  });
}

window.loadStream = loadStream;
window.autoStartResultStream = autoStartResultStream;
window.scheduleResultStreamStart = scheduleResultStreamStart;

bindResultStreamLifecycle();
scheduleResultStreamStart();
