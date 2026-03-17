function formatBeijingTime() {
  const now = new Date();
  return now.toLocaleString("zh-CN", {
    timeZone: "Asia/Shanghai",
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
  });
}

function updateBeijingTime() {
  const el = document.getElementById("beijing-time");
  if (el) {
    el.textContent = formatBeijingTime();
  }
}

function copyText(text) {
  if (!navigator.clipboard) {
    return;
  }
  navigator.clipboard.writeText(text).catch(() => {});
}

function bindCopyButtons() {
  const core = document.querySelector("[data-action='copy-core']");
  if (core) {
    core.addEventListener("click", () => {
      copyText(`http://127.0.0.1:${core.dataset.port || ""}`);
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  updateBeijingTime();
  setInterval(updateBeijingTime, 1000 * 30);
  bindCopyButtons();
});
