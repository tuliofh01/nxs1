import { logEvent } from "./utils/logger";
import { handleFingerprint } from "./utils/fingerprint";

export interface Env {
  DB: D1Database;
  ASSETS: Fetcher;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const start = Date.now();
    const url = new URL(req.url);

    if (url.pathname.startsWith("/api/fingerprint")) {
      return handleFingerprint(req, env, start);
    }

    if (url.pathname.startsWith("/api/logs")) {
      const logs = await env.DB.prepare(
        "SELECT * FROM logs ORDER BY created_at DESC LIMIT 100"
      ).all();

      return Response.json(logs.results);
    }

    const response = await env.ASSETS.fetch(req);
    const latency = Date.now() - start;

    await logEvent(env, {
      event_type: "PAGE_VISIT",
      latency_ms: latency,
      req
    });

    return response;
  }
};
