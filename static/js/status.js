// const statusEl = document.getElementById("status");

// function renderStatus(status) {
//     if (!statusEl) return;

//     switch (status) {
//         case "STARTING":
//             statusEl.innerHTML = '<span style="color: orange;">● Waiting...</span>';
//             break;
//         case "RUNNING":
//             statusEl.innerHTML = '<span style="color: green;">● 起動中</span>';
//             break;
//         case "STOPPING":
//             statusEl.innerHTML = '<span style="color: orange;">● Stopping...</span>';
//             break;
//         case "STOPPED":
//         default:
//             statusEl.innerHTML = '<span style="color: red;">● 停止中</span>';
//     }
// }

// async function updateStatus() {
//     try {
//         const res = await fetch("/status", { cache: "no-store" });
//         if (!res.ok) return;

//         const data = await res.json();
//         renderStatus(data.status);
//     } catch (e) {
//         console.error("status fetch error:", e);
//     }
// }

// // 初回描画
// updateStatus();

// // 定期ポーリング
// setInterval(updateStatus, 500);

// // submit時は「即変更しない」
// // Flask側が status を STARTING / STOPPING に変えたのを検知する
// document.querySelectorAll("form").forEach(form => {
//     form.addEventListener("submit", () => {
//         console.log("action submitted:", form.action);
//     });
// });

function renderStatus(status) {
  if (status === "RUNNING") return { text: "● 起動中", color: "green" };
  if (status === "STARTING" || status === "STOPPING") return { text: "● Waiting...", color: "orange" };
  return { text: "● 停止中", color: "red" };
}

function setWaiting(projectId) {
  const el = document.getElementById(`status-${projectId}`);
  if (!el) return;
  el.textContent = "● Waiting...";
  el.style.color = "orange";
}

function applyOne(item) {
  const { id, status, pid } = item;
  const s = renderStatus(status);

  const statusEl = document.getElementById(`status-${id}`);
  const pidEl = document.getElementById(`pid-${id}`);

  if (statusEl) {
    statusEl.textContent = s.text;
    statusEl.style.color = s.color;
  }
  if (pidEl) {
    pidEl.textContent = (pid ?? "-");
  }

  // ボタン活性（品質が上がる）
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

    if (!Array.isArray(list)) {
      console.error("Status API format error: expected array", list);
      return;
    }

    list.forEach(applyOne);
  } catch (e) {
    console.error("status polling failed:", e);
  }
}

// submit直後にWaitingを即表示（体験改善）
document.querySelectorAll("form.lm-form").forEach(form => {
  form.addEventListener("submit", () => {
    const section = form.closest(".project");
    if (!section) return;
    const projectId = section.dataset.projectId;
    if (!projectId) return;
    setWaiting(projectId);
  });
});

// 初回＋定期更新
updateStatus();
setInterval(updateStatus, 1000);
