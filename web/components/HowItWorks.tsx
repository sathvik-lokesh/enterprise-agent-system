const CARDS = [
  {
    title: "Hierarchical orchestration",
    body: "An orchestrator routes each request to exactly the right sub-agent via the agents-as-tools pattern. Cross-domain requests fan out to multiple agents and the answers are combined.",
  },
  {
    title: "Text-to-SQL with a guard",
    body: "The Data Analyst agent introspects the live PostgreSQL schema, writes a SELECT from plain English, runs it through a read-only guard, retries on SQL errors, and answers with the real rows.",
  },
  {
    title: "MCP integration",
    body: "The IT tools aren't imported into the agent — they run in a separate Model Context Protocol stdio server process and are called over MCPStdioTool, so tools live in their own process.",
  },
  {
    title: "Live external data",
    body: "The Research agent calls four free, keyless APIs — Open-Meteo (weather), Frankfurter/ECB (FX), Nager.Date (holidays), and Wikipedia (lookups). This is the path you can try below.",
  },
  {
    title: "Local-first, hosted-capable",
    body: "Defaults to local Ollama (qwen2.5:3b) at zero cost and no API key. One env var switches the whole system to any OpenAI-compatible provider — e.g. Groq — with no code change.",
  },
  {
    title: "Read-only by design",
    body: "execute_sql_query only permits SELECT. Mutations would require a human-approval step, kept as an explicit, deliberate boundary rather than an afterthought.",
  },
];

export default function HowItWorks() {
  return (
    <section className="py-12">
      <h2 className="text-2xl font-semibold text-white">How it works</h2>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {CARDS.map((c) => (
          <div key={c.title} className="card p-5">
            <h3 className="font-medium text-accent">{c.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">{c.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
