import { logEvent } from "./utils/logger";
import { handleFingerprint } from "./utils/fingerprint";
import { setSecurityHeaders } from "./utils/security";

export interface Env {
  DB: D1Database;
  ASSETS: Fetcher;
  TUNNEL_SECRET?: string;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const start = Date.now();
    const url = new URL(req.url);

    // API: Update Tunnel URL (Protected)
    if (req.method === "POST" && url.pathname === "/api/tunnel") {
      const authHeader = req.headers.get("Authorization");
      // Simple check: if secret is set, it must match. If not set, allow it (dev mode) or deny.
      if (env.TUNNEL_SECRET && !authHeader?.includes(env.TUNNEL_SECRET)) {
        return new Response("Unauthorized", { status: 401 });
      }

      const { tunnelUrl } = await req.json() as { tunnelUrl: string };
      if (!tunnelUrl) return new Response("Missing tunnelUrl", { status: 400 });

      try {
        await env.DB.prepare(
          "INSERT INTO config (key, value, updated_at) VALUES ('tunnel_url', ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at"
        ).bind(tunnelUrl, Date.now()).run();
        return new Response("Tunnel URL Updated", { status: 200 });
      } catch (e) {
        // Table might not exist yet, ignore or create
        return new Response("DB Error: " + e, { status: 500 });
      }
    }

    // API Routes
    if (url.pathname.startsWith("/api/fingerprint")) {
      const response = await handleFingerprint(req, env, start);
      return setSecurityHeaders(response);
    }

    if (url.pathname.startsWith("/api/logs")) {
      const logs = await env.DB.prepare(
        "SELECT * FROM logs ORDER BY created_at DESC LIMIT 100"
      ).all();
      const response = Response.json(logs.results);
      return setSecurityHeaders(response);
    }

    // Dynamic Tunnel Dashboard (Injects active tunnel URL)
    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
      let currentTunnelUrl = "Not Connected";
      try {
        const tunnelConfig = await env.DB.prepare("SELECT value FROM config WHERE key = 'tunnel_url'").first() as { value: string } | undefined;
        if (tunnelConfig?.value) currentTunnelUrl = tunnelConfig.value;
      } catch (e) {
        // Table might not exist
      }

      // Fetch static asset
      let response = await env.ASSETS.fetch(req);
      let html = await response.text();

      // Inject active tunnel data
      const isOnline = currentTunnelUrl !== "Not Connected";
      
      html = html.replace(
        '<!-- TUNNEL_STATUS -->', 
        `<div id="tunnel-status" class="card">
           <h2>Active Tunnel</h2>
           <p class="status ${isOnline ? 'online' : 'offline'}">
             ${isOnline ? 'Online' : 'Offline'}
           </p>
           <code class="tunnel-url">${currentTunnelUrl}</code>
           ${isOnline ? 
             `<div class="ssh-command">
                <p>Connect via SSH:</p>
                <pre>ssh user@${currentTunnelUrl.replace('https://', '').replace('http://', '')}</pre>
              </div>` : ''
           }
         </div>`
      );
      
      return setSecurityHeaders(new Response(html, {
        headers: response.headers
      }));
    }

    // Static Asset Handling
    let response: Response;
    try {
      response = await env.ASSETS.fetch(req);
    } catch (e) {
      response = new Response("Not Found", { status: 404 });
    }

    // Log page visits
    if (response.status === 200 && (url.pathname === "/" || url.pathname.endsWith(".html"))) {
       const latency = Date.now() - start;
       env.DB.prepare(`
         INSERT INTO logs (event_type, latency_ms, details, created_at)
         VALUES (?, ?, ?, ?)
       `).bind("PAGE_VISIT", latency, JSON.stringify({ url: req.url }), Date.now()).run().catch(console.error);
    }

    return setSecurityHeaders(response);
  }
};
