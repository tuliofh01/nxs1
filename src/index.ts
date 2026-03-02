import { logEvent } from "./utils/logger";
import { handleFingerprint } from "./utils/fingerprint";
import { setSecurityHeaders } from "./utils/security";

export interface Env {
  DB: D1Database;
  ASSETS: Fetcher;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const start = Date.now();
    const url = new URL(req.url);

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
    let response: Response;
    try {
      response = await env.ASSETS.fetch(req);
    } catch (e) {
      // Fallback for SPA routing if needed, or 404
      response = new Response("Not Found", { status: 404 });
    }

    // Log page visits
    if (response.status === 200 && (url.pathname === "/" || url.pathname.endsWith(".html"))) {
       const latency = Date.now() - start;
       // Non-blocking log
       env.DB.prepare(`
         INSERT INTO logs (event_type, latency_ms, details, created_at)
         VALUES (?, ?, ?, ?)
       `).bind("PAGE_VISIT", latency, JSON.stringify({ url: req.url }), Date.now()).run().catch(console.error);
    }

    return setSecurityHeaders(response);
  }
};
