/**
 * Live-demo agent loop.
 *
 * The full system (Python repo) is a hierarchical orchestrator that routes to
 * four specialized sub-agents over the Microsoft Agent Framework. This hosted
 * demo runs the same tool-calling loop for the **research_agent** subset — the
 * four live, keyless external tools — against Groq (an OpenAI-compatible,
 * always-on provider) so the page works instantly with nothing to cold-start.
 *
 * It returns the final answer plus a routing trace (orchestrator → research_agent
 * → tool calls), mirroring demo_trace.py in the Python repo.
 */

import { TOOL_IMPLS, TOOL_SCHEMAS, ToolName } from "./tools";

const BASE_URL = process.env.GROQ_BASE_URL ?? "https://api.groq.com/openai/v1";
const MODEL = process.env.GROQ_MODEL ?? "llama-3.3-70b-versatile";

// Mirrors the research_agent instructions in agents/system.py.
const SYSTEM_PROMPT =
  "You are a research assistant with live data tools. Use them for weather, " +
  "currency, holidays and factual lookups. Quote the data you received; do not " +
  "guess. Be concise. If a question is outside these four capabilities (weather, " +
  "currency conversion, public holidays, general topic lookups), briefly say so " +
  "and mention that the full system also has HR, finance/text-to-SQL, and IT " +
  "support agents.";

export type TraceStep =
  | { kind: "route"; from: string; to: string }
  | { kind: "tool_call"; name: string; args: Record<string, unknown> }
  | { kind: "tool_result"; name: string; result: string };

export interface AgentResult {
  answer: string;
  trace: TraceStep[];
  model: string;
}

interface ChatMessage {
  role: "system" | "user" | "assistant" | "tool";
  content: string | null;
  tool_calls?: {
    id: string;
    type: "function";
    function: { name: string; arguments: string };
  }[];
  tool_call_id?: string;
}

const MAX_ITERATIONS = 5;

export async function runAgent(userMessage: string): Promise<AgentResult> {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    throw new Error("GROQ_API_KEY is not set on the server.");
  }

  const messages: ChatMessage[] = [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "user", content: userMessage },
  ];

  // The full system always routes external-data questions here; show that hop.
  const trace: TraceStep[] = [{ kind: "route", from: "orchestrator", to: "research_agent" }];

  for (let i = 0; i < MAX_ITERATIONS; i++) {
    const resp = await fetch(`${BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: MODEL,
        messages,
        tools: TOOL_SCHEMAS,
        tool_choice: "auto",
        temperature: 0.2,
      }),
    });

    if (!resp.ok) {
      const detail = await resp.text();
      throw new Error(`LLM provider error (${resp.status}): ${detail.slice(0, 300)}`);
    }

    const data = await resp.json();
    const choice = data.choices?.[0]?.message;
    if (!choice) throw new Error("Empty response from LLM provider.");

    const toolCalls = choice.tool_calls as ChatMessage["tool_calls"];

    // No tool calls → final answer.
    if (!toolCalls || toolCalls.length === 0) {
      return { answer: choice.content ?? "(no answer)", trace, model: MODEL };
    }

    // Record the assistant turn that requested the tools.
    messages.push({ role: "assistant", content: choice.content ?? null, tool_calls: toolCalls });

    // Execute every requested tool and feed results back.
    for (const call of toolCalls) {
      const name = call.function.name as ToolName;
      let args: Record<string, unknown> = {};
      try {
        args = JSON.parse(call.function.arguments || "{}");
      } catch {
        /* leave args empty on malformed JSON */
      }
      trace.push({ kind: "tool_call", name, args });

      const impl = TOOL_IMPLS[name];
      const result = impl
        ? await impl(args)
        : `Unknown tool '${name}'.`;
      trace.push({ kind: "tool_result", name, result });

      messages.push({ role: "tool", tool_call_id: call.id, content: result });
    }
  }

  return {
    answer:
      "I wasn't able to finish within the demo's step budget — try a more direct question " +
      "(weather, currency conversion, public holidays, or a topic lookup).",
    trace,
    model: MODEL,
  };
}
