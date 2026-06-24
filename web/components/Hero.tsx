function GitHubIcon() {
  return (
    <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden>
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

export default function Hero({ githubUrl }: { githubUrl: string }) {
  return (
    <section className="pt-16 pb-12">
      <span className="chip mb-5">Portfolio project · Sathvik Lokesh</span>
      <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">
        Enterprise Multi-Agent System
      </h1>
      <p className="mt-5 max-w-2xl text-lg leading-relaxed text-slate-300">
        A hierarchical multi-agent system that automates internal enterprise workflows — built with{" "}
        <span className="text-accent">Microsoft Agent Framework</span>,{" "}
        <span className="text-accent">PostgreSQL</span>, and the{" "}
        <span className="text-accent">Model Context Protocol (MCP)</span>. An orchestrator routes
        each request to one of four specialized sub-agents across 14 tools.
      </p>

      <div className="mt-7 flex flex-wrap gap-3">
        <a
          href="#demo"
          className="rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-ink transition hover:bg-sky-300"
        >
          Try the live demo ↓
        </a>
        <a
          href={githubUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-lg border border-edge bg-panel px-5 py-2.5 text-sm font-medium text-slate-200 transition hover:border-slate-500"
        >
          <GitHubIcon /> View source
        </a>
      </div>

      <div className="mt-9 flex flex-wrap gap-2">
        {[
          "Hierarchical orchestration",
          "Agents-as-tools",
          "14 tools",
          "Text-to-SQL",
          "MCP (stdio)",
          "Local-first (Ollama) · hosted-capable (Groq)",
        ].map((t) => (
          <span key={t} className="chip">
            {t}
          </span>
        ))}
      </div>
    </section>
  );
}
