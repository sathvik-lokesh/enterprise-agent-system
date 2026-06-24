import { NextRequest, NextResponse } from "next/server";
import { runAgent } from "@/lib/agent";

export const runtime = "nodejs";
export const maxDuration = 30;

const MAX_INPUT_CHARS = 500;

// Best-effort in-memory rate limit (resets on cold start — fine for abuse control
// on a public demo). Per client: 15 requests / 10 minutes.
const WINDOW_MS = 10 * 60 * 1000;
const MAX_REQUESTS = 15;
const hits = new Map<string, number[]>();

function clientId(req: NextRequest): string {
  const fwd = req.headers.get("x-forwarded-for");
  return (fwd ? fwd.split(",")[0] : null)?.trim() || req.headers.get("x-real-ip") || "anon";
}

function rateLimited(id: string): boolean {
  const now = Date.now();
  const recent = (hits.get(id) ?? []).filter((t) => now - t < WINDOW_MS);
  recent.push(now);
  hits.set(id, recent);
  return recent.length > MAX_REQUESTS;
}

export async function POST(req: NextRequest) {
  let body: { message?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const message = typeof body.message === "string" ? body.message.trim() : "";
  if (!message) {
    return NextResponse.json({ error: "A 'message' string is required." }, { status: 400 });
  }
  if (message.length > MAX_INPUT_CHARS) {
    return NextResponse.json(
      { error: `Message too long (max ${MAX_INPUT_CHARS} characters).` },
      { status: 413 },
    );
  }

  if (rateLimited(clientId(req))) {
    return NextResponse.json(
      { error: "Rate limit reached for this demo. Please try again in a few minutes." },
      { status: 429 },
    );
  }

  if (!process.env.GROQ_API_KEY) {
    return NextResponse.json(
      {
        error:
          "The live demo isn't configured (no GROQ_API_KEY on the server). The full source runs locally — see the GitHub link.",
      },
      { status: 503 },
    );
  }

  try {
    const result = await runAgent(message);
    return NextResponse.json(result);
  } catch (e: any) {
    return NextResponse.json(
      { error: e?.message ?? "The demo backend hit an unexpected error." },
      { status: 502 },
    );
  }
}
