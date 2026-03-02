interface LogEntry {
  created_at: number;
  event_type: string;
  ip: string;
  country: string;
  latency_ms: number;
}

const logsDiv = document.getElementById("logs") as HTMLDivElement;
const filterBtn = document.getElementById("filterBtn") as HTMLButtonElement;
const filterPopup = document.getElementById("filterPopup") as HTMLDivElement;
const filterInput = document.getElementById("filterInput") as HTMLInputElement;

if (filterBtn) {
  filterBtn.onclick = () => {
    filterPopup.classList.toggle("hidden");
  };
}

async function loadLogs() {
  try {
    const res = await fetch("/api/logs");
    const logs: LogEntry[] = await res.json();
    render(logs);
  } catch (error) {
    console.error("Failed to load logs", error);
  }
}

function render(logs: LogEntry[]) {
  const filter = filterInput ? filterInput.value.toLowerCase() : "";

  if (logsDiv) {
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
}

if (filterInput) {
  filterInput.oninput = loadLogs;
}

loadLogs();
