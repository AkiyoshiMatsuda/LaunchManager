document.addEventListener("DOMContentLoaded", () => {

  // =========================
  // Status
  // =========================
  function renderStatus(status) {
    if (status === "RUNNING") return { text: "● 起動中", color: "green" };
    if (status === "STARTING" || status === "STOPPING") return { text: "● Waiting...", color: "orange" };
    if (status === "ERROR") return { text: "● ERROR", color: "red" };
    return { text: "● 停止中", color: "gray" };
  }

  function setWaiting(projectId) {
    const el = document.getElementById(`status-${projectId}`);
    if (!el) return;
    el.textContent = "● Waiting...";
    el.style.color = "orange";
  }

  function applyOne(item) {
    const { id, status, pid, error } = item;

    const statusEl = document.getElementById(`status-${id}`);
    const pidEl = document.getElementById(`pid-${id}`);
    const errEl = document.getElementById(`error-${id}`);

    const s = renderStatus(status);

    if (statusEl) {
      statusEl.textContent = s.text;
      statusEl.style.color = s.color;
    }
    if (pidEl) {
      pidEl.textContent = pid ?? "-";
    }
    if (errEl) {
      errEl.textContent = error ? `ERROR: ${error}` : "";
    }

    const btnStart = document.getElementById(`btn-start-${id}`);
    const btnStop = document.getElementById(`btn-stop-${id}`);
    const btnRestart = document.getElementById(`btn-restart-${id}`);

    if (btnStart) btnStart.disabled = (status !== "STOPPED");
    if (btnStop) btnStop.disabled = (status !== "RUNNING");
    if (btnRestart) btnRestart.disabled = (status !== "RUNNING");
  }

  async function updateStatus() {
    try {
      const res = await fetch("/status", { cache: "no-store" });
      const list = await res.json();
      if (!Array.isArray(list)) return;
      list.forEach(applyOne);
    } catch (e) {
      console.error("status polling failed:", e);
    }
  }

  document.querySelectorAll("form.lm-form").forEach((form) => {
    form.addEventListener("submit", () => {
      const action = form.getAttribute("action") || "";
      if (action.startsWith("/toggle_autostart/")) return;

      const section = form.closest(".project");
      if (!section) return;
      const projectId = section.dataset.projectId;
      if (!projectId) return;
      setWaiting(projectId);
    });
  });

  // =========================
  // Log Modal + Filter
  // =========================
  const modal = document.getElementById("logModal");
  const modalTitle = document.getElementById("logModalTitle");
  const modalMeta = document.getElementById("logModalMeta");
  const modalBody = document.getElementById("logModalBody");

  const closeBtn = document.getElementById("logCloseBtn");
  const popoutBtn = document.getElementById("logPopoutBtn");
  const refreshBtn = document.getElementById("logRefreshBtn");
  const lineCountSel = document.getElementById("logLineCount");
  const wrapChk = document.getElementById("logWrap");

  const filterDebug = document.getElementById("filter-debug");
  const filterAccess = document.getElementById("filter-access");
  const filterWarning = document.getElementById("filter-warning");
  const filterError = document.getElementById("filter-error");

  let currentLog = { projectId: null, kind: null };
  let currentLines = [];

  function classifyLine(line) {
    if (line.includes("[GIN-debug]")) return "debug";
    if (line.includes("[GIN]")) return "access";
    if (line.includes("WARNING")) return "warning";
    if (line.includes("ERROR")) return "error";
    return "other";
  }

  function renderFilteredLogs() {
    if (!modalBody) return;
    modalBody.innerHTML = "";

    currentLines.forEach(line => {
      const type = classifyLine(line);

      if (type === "debug" && filterDebug && !filterDebug.checked) return;
      if (type === "access" && filterAccess && !filterAccess.checked) return;
      if (type === "warning" && filterWarning && !filterWarning.checked) return;
      if (type === "error" && filterError && !filterError.checked) return;

      const div = document.createElement("div");
      div.textContent = line;

      if (type === "warning") div.style.color = "#ffcc00";
      if (type === "error") div.style.color = "#ff5555";
      if (type === "access") div.style.color = "#66ffcc";
      if (type === "debug") div.style.color = "#888";

      modalBody.appendChild(div);
    });
  }

  async function loadModalLogs() {
    const { projectId, kind } = currentLog;
    if (!projectId || !kind) return;

    const n = lineCountSel?.value || "500";
    if (modalMeta) modalMeta.textContent = `last ${n} lines`;
    if (modalBody) modalBody.textContent = "Loading logs...";

    try {
      const res = await fetch(`/logs/${projectId}/${kind}?n=${encodeURIComponent(n)}`, { cache: "no-store" });
      const text = await res.text();
      currentLines = text.split("\n");
      renderFilteredLogs();
    } catch (e) {
      if (modalBody) modalBody.textContent = `Failed to load logs: ${e}`;
    }
  }

  function openModal(projectId, kind) {
    currentLog = { projectId, kind };
    if (modalTitle) modalTitle.textContent = `${projectId} / ${kind}`;
    if (modal) modal.style.display = "block";
    loadModalLogs();
  }

  function closeModal() {
    if (modal) modal.style.display = "none";
    currentLog = { projectId: null, kind: null };
  }

  closeBtn?.addEventListener("click", closeModal);
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  refreshBtn?.addEventListener("click", loadModalLogs);
  lineCountSel?.addEventListener("change", loadModalLogs);

  wrapChk?.addEventListener("change", () => {
    if (!modalBody) return;
    modalBody.style.whiteSpace = wrapChk.checked ? "pre-wrap" : "pre";
  });

  popoutBtn?.addEventListener("click", () => {
    const { projectId, kind } = currentLog;
    if (!projectId || !kind) return;
    const n = lineCountSel?.value || "500";
    window.open(`/logs/${projectId}/${kind}?n=${encodeURIComponent(n)}`, "_blank", "noopener,noreferrer");
  });

  [filterDebug, filterAccess, filterWarning, filterError]
    .forEach(el => el?.addEventListener("change", renderFilteredLogs));

  document.querySelectorAll(".project").forEach((section) => {
    const projectId = section.dataset.projectId;
    section.querySelectorAll("button.btn-logs").forEach((btn) => {
      btn.addEventListener("click", () => {
        const kind = btn.dataset.kind;
        openModal(projectId, kind);
      });
    });
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal && modal.style.display === "block") {
      closeModal();
    }
  });

  // =========================
  // Start polling
  // =========================
  updateStatus();
  setInterval(updateStatus, 1000);
});
