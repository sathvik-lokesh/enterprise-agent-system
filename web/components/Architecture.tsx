const DIAGRAM = `                         ┌──────────────────┐
            user ──────► │   Orchestrator   │  routes each request
                         └────────┬─────────┘
        ┌───────────────┬─────────┴────────┬────────────────┐
        ▼               ▼                  ▼                ▼
  ┌──────────┐   ┌──────────────┐   ┌─────────────┐  ┌────────────┐
  │ HR Agent │   │ Data Analyst │   │ IT Support  │  │  Research  │
  │ 3 tools  │   │ text-to-SQL  │   │ 4 MCP tools │  │ 4 live-API │
  └────┬─────┘   │   3 tools    │   └──────┬──────┘  │   tools    │
       │         └──────┬───────┘          │ MCP     └─────┬──────┘
       ▼                ▼                  ▼ (stdio)       ▼
   PostgreSQL       PostgreSQL        MCP server →     Open-Meteo,
   (employees)      (analytics)       PostgreSQL       Frankfurter,
                                      (tickets)        Nager.Date,
                                                       Wikipedia`;

export default function Architecture() {
  return (
    <section className="py-12">
      <h2 className="text-2xl font-semibold text-white">Architecture</h2>
      <p className="mt-2 max-w-2xl text-slate-400">
        One orchestrator agent delegates to four specialized sub-agents using Agent Framework&apos;s{" "}
        <code className="text-accent2">Agent.as_tool()</code> pattern. Each sub-agent owns its own
        tools and data source.
      </p>
      <div className="card glow-border mt-6 overflow-x-auto p-5">
        <pre className="font-mono text-[11px] leading-snug text-slate-300 sm:text-xs">{DIAGRAM}</pre>
      </div>
      <p className="mt-3 text-sm text-amber-300/80">
        The live demo below runs the <strong>Research agent</strong> path (the four keyless live-API
        tools) hosted on Groq. The other three agents need PostgreSQL / an MCP subprocess and run
        locally from the repo.
      </p>
    </section>
  );
}
