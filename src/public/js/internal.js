const logsDiv = document.getElementById("logs");
const filterBtn = document.getElementById("filterBtn");
const filterPopup = document.getElementById("filterPopup");
const filterInput = document.getElementById("filterInput");

filterBtn.onclick = () => {
  filterPopup.classList.toggle("hidden");
};

async function loadLogs() {
  const res = await fetch("/api/logs");
  const logs = await res.json();
  render(logs);
}

function render(logs) {
  const filter = filterInput.value.toLowerCase();

  logsDiv.innerHTML = logs
    .filter(l =>
      JSON.stringify(l).toLowerCase().includes(filter)
    )
    .map(l => `
      <div class="log-entry">
        [${new Date(l.created_at).toLocaleTimeString()}]
        ${l.event_type}
        ${l.ip} (${l.country})
        ${l.latency_ms}ms
      </div>
    `)
    .join("");
}

filterInput.oninput = loadLogs;

loadLogs();
