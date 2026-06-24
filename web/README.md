# Enterprise Multi-Agent System — Showcase + Live Demo

A Next.js page that showcases the [Enterprise Multi-Agent System](../README.md)
and includes a **live demo** of its Research agent. Designed to be deployed to
Vercel and shared as a portfolio link.

- **Showcase:** architecture diagram, how it works, and the text-to-SQL eval
  results (22/24 on Groq `llama-3.3-70b-versatile`).
- **Live demo:** ask about weather, currency, public holidays, or a topic
  lookup. A Vercel serverless route runs the same tool-calling loop as the
  Python `research_agent`, against [Groq](https://groq.com) (free, OpenAI-
  compatible, always-on), and returns the answer plus the routing trace.

The four demo tools (`lib/tools.ts`) are a faithful TypeScript port of
`tools/research_tools.py` — same free, keyless endpoints (Open-Meteo,
Frankfurter/ECB, Nager.Date, Wikipedia), same arguments, same JSON shapes. The
other three agents (HR, Data Analyst/text-to-SQL, IT/MCP) need PostgreSQL and an
MCP subprocess and run from the Python repo, not on Vercel.

## Run locally

```bash
cd web
npm install
cp .env.example .env.local        # then paste your Groq key into GROQ_API_KEY
npm run dev                        # http://localhost:3000
```

Get a free key at <https://console.groq.com>. Without a key the page still
loads; the demo box returns a friendly "not configured" message.

| Env var | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | — (required for the demo) | Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | model used by the demo |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | OpenAI-compatible endpoint |

## Deploy to Vercel

1. Push this repo to GitHub (the `web/` folder lives inside the main
   `enterprise-agent-system` repo).
2. On <https://vercel.com> → **Add New… → Project** → import the repo.
3. **Important:** set **Root Directory** to `web` (this app is a subfolder).
   Framework preset auto-detects as **Next.js**; leave build/output defaults.
4. Under **Environment Variables**, add `GROQ_API_KEY` (and optionally
   `GROQ_MODEL`). Apply to Production + Preview.
5. **Deploy.** You get a `*.vercel.app` URL to share. Add a custom domain later
   under Project → Settings → Domains if you want.

### CLI alternative

```bash
cd web
npx vercel            # first deploy (set root dir to current when prompted)
npx vercel env add GROQ_API_KEY
npx vercel --prod
```

## Before sharing — quick checklist

- [ ] `GROQ_API_KEY` set in Vercel env vars (demo works on the live URL).
- [ ] Set your LinkedIn URL: `LINKEDIN_URL` in `components/Footer.tsx`
      (left blank so the page never ships a broken link).
- [ ] Confirm the GitHub link in `app/page.tsx` (`GITHUB_URL`) is correct.
- [ ] Try each example chip on the deployed URL.

## Notes

- The demo has a best-effort in-memory rate limit (15 requests / 10 min per IP)
  and a 500-character input cap, so a public link can't run up Groq usage.
- Rebuilt on Next.js 14.2.35 (latest patched 14.2.x). The `/api/chat` route runs
  on the Node.js runtime with a 30s max duration — comfortably within Vercel's
  free Hobby limits.
