var i=document.getElementById("logs"),r=document.getElementById("filterBtn"),c=document.getElementById("filterPopup"),n=document.getElementById("filterInput");r&&(r.onclick=()=>{c.classList.toggle("hidden")});async function s(){try{let o=await(await fetch("/api/logs")).json();l(o)}catch(e){console.error("Failed to load logs",e)}}function l(e){let o=n?n.value.toLowerCase():"";i&&(i.innerHTML=e.filter(t=>JSON.stringify(t).toLowerCase().includes(o)).map(t=>`
        <div class="log-entry">
          [${new Date(t.created_at).toLocaleTimeString()}]
          ${t.event_type}
          ${t.ip} (${t.country})
          ${t.latency_ms}ms
        </div>
      `).join(""))}n&&(n.oninput=s);s();
//# sourceMappingURL=internal.js.map
