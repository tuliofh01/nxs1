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

    // API: Update Tunnel URL
    if (req.method === "POST" && url.pathname === "/api/tunnel") {
      const authHeader = req.headers.get("Authorization");
      if (env.TUNNEL_SECRET && !authHeader?.includes(env.TUNNEL_SECRET)) {
        return new Response("Unauthorized", { status: 401 });
      }

      let body;
      try {
        body = await req.json();
      } catch (e) {
        return new Response("Invalid JSON", { status: 400 });
      }
      
      const tunnelUrl = (body as any)?.tunnelUrl;
      if (!tunnelUrl) return new Response("Missing tunnelUrl", { status: 400 });

      try {
        await env.DB.prepare(
          "INSERT INTO config (key, value, updated_at) VALUES ('tunnel_url', ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at"
        ).bind(tunnelUrl, Date.now()).run();
        return new Response("Tunnel URL Updated", { status: 200 });
      } catch (e) {
        return new Response("DB Error: " + e, { status: 500 });
      }
    }

    // API: Get Tunnel Status
    if (req.method === "GET" && url.pathname === "/api/status") {
      let tunnelUrl = "Not Connected";
      try {
        const config = await env.DB.prepare("SELECT value FROM config WHERE key = 'tunnel_url'").first() as any;
        if (config?.value) tunnelUrl = config.value;
      } catch (e) { /* ignore */ }
      return Response.json({ tunnelUrl, isConnected: tunnelUrl !== "Not Connected" });
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

    // Static Asset Handling
    let assetPath = url.pathname;
    if (assetPath === "/") {
      assetPath = "/index.html";
    }

    let response: Response;
    try {
      response = await env.ASSETS.fetch(assetPath);
    } catch (e) {
      response = new Response("Not Found", { status: 404 });
    }

    // Log page visits
    if (response.status === 200 && (url.pathname === "/" || url.pathname === "/index.html")) {
       const latency = Date.now() - start;
       env.DB.prepare(`
         INSERT INTO logs (event_type, latency_ms, details, created_at)
         VALUES (?, ?, ?, ?)
       `).bind("PAGE_VISIT", latency, JSON.stringify({ url: req.url }), Date.now()).run().catch(console.error);
    }

    return setSecurityHeaders(response);
  }
};
