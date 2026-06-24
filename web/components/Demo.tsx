"use client";

import { useState } from "react";

type TraceStep =
  | { kind: "route"; from: string; to: string }
  | { kind: "tool_call"; name: string; args: Record<string, unknown> }
  | { kind: "tool_result"; name: string; result: string };

interface AgentResult {
  answer: string;
  trace: TraceStep[];
  model: string;
}

const EXAMPLES = [
  "What's the weather in Bengaluru?",
  "Convert 500 USD to INR",
  "What are the public holidays in Germany in 2026?",
  "Give me a quick summary of the Model Context Protocol",
];

function TraceView({ trace }: { trace: TraceStep[] }) {
  return (
    <div className="mt-3 space-y-1.5 font-mono text-[11px] leading-relaxed">
      {trace.map((s, i) => {
        if (s.kind === "route") {
          return (
            <div key={i} className="text-accent2">
              {s.from} <span className="text-slate-500">──▶</span> {s.to}
            </div>
          );
        }
        if (s.kind === "tool_call") {
          return (
            <div key={i} className="text-sky-300">
              <span className="text-slate-500">→ CALL</span> {s.name}
              <span className="text-slate-400"> {JSON.stringify(s.args)}</span>
            </div>
          );
        }
        const r = s.result.length > 220 ? s.result.slice(0, 220) + "…" : s.result;
        return (
          <div key={i} className="text-emerald-300/90">
            <span className="text-slate-500">← RESULT</span> <span className="text-slate-400">{r}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function Demo() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentResult | null>(null);

  async function ask(question: string) {
    const q = question.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: q }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Something went wrong.");
      } else {
        setResult(data as AgentResult);
      }
    } catch {
      setError("Network error — couldn't reach the demo backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="demo" className="scroll-mt-8 py-12">
      <h2 className="text-2xl font-semibold text-white">Live demo — Research agent</h2>
      <p className="mt-2 max-w-2xl text-slate-400">
        Ask about <strong>weather</strong>, <strong>currency conversion</strong>,{" "}
        <strong>public holidays</strong>, or a <strong>topic lookup</strong>. The model decides
        which tool to call and answers from live data. You&apos;ll see the routing trace below the
        answer, exactly like the system&apos;s own demo trace.
      </p>

      <div className="card glow-border mt-6 p-5">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(input);
          }}
          className="flex flex-col gap-3 sm:flex-row"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            maxLength={500}
            placeholder="e.g. What's the weather in Stuttgart?"
            className="flex-1 rounded-lg border border-edge bg-ink px-4 py-2.5 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-accent"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-ink transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? "Routing…" : "Ask"}
          </button>
        </form>

        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => {
                setInput(ex);
                ask(ex);
              }}
              disabled={loading}
              className="chip transition hover:border-slate-500 disabled:opacity-40"
            >
              {ex}
            </button>
          ))}
        </div>

        {error && (
          <div className="mt-5 rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-5 space-y-4">
            <div className="rounded-lg border border-edge bg-ink/60 p-4">
              <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">Answer</div>
              <div className="whitespace-pre-wrap text-sm text-slate-100">{result.answer}</div>
            </div>
            <details open className="rounded-lg border border-edge bg-ink/60 p-4">
              <summary className="cursor-pointer text-xs uppercase tracking-wide text-slate-500">
                Routing trace · model {result.model}
              </summary>
              <TraceView trace={result.trace} />
            </details>
          </div>
        )}
      </div>
    </section>
  );
}
