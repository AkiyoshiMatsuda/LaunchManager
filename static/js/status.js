// function setWaiting() {
//     const status = document.getElementById("status");
//     status.innerHTML = '<span style="color: orange;">● Waiting...</span>';
// }
// async function updateStatus() {
//   const res = await fetch("/status");
//   const data = await res.json();
//   document.getElementById("status").textContent = data.status;
// }

// updateStatus();
// setInterval(updateStatus, 1000); // 1秒ごと
// document.querySelectorAll("form").forEach(form => {
//     form.addEventListener("submit", () => {
//         setWaiting();
//         console.log("確認用log");
//     });
// });

const statusEl = document.getElementById("status");

function renderStatus(status) {
    if (!statusEl) return;

    switch (status) {
        case "STARTING":
            statusEl.innerHTML = '<span style="color: orange;">● Waiting...</span>';
            break;
        case "RUNNING":
            statusEl.innerHTML = '<span style="color: green;">● 起動中</span>';
            break;
        case "STOPPING":
            statusEl.innerHTML = '<span style="color: orange;">● Stopping...</span>';
            break;
        case "STOPPED":
        default:
            statusEl.innerHTML = '<span style="color: red;">● 停止中</span>';
    }
}

async function updateStatus() {
    try {
        const res = await fetch("/status", { cache: "no-store" });
        if (!res.ok) return;

        const data = await res.json();
        renderStatus(data.status);
    } catch (e) {
        console.error("status fetch error:", e);
    }
}

// 初回描画
updateStatus();

// 定期ポーリング
setInterval(updateStatus, 500);

// submit時は「即変更しない」
// Flask側が status を STARTING / STOPPING に変えたのを検知する
document.querySelectorAll("form").forEach(form => {
    form.addEventListener("submit", () => {
        console.log("action submitted:", form.action);
    });
});
