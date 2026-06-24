export default function Eval() {
  return (
    <section className="py-12">
      <h2 className="text-2xl font-semibold text-white">Evaluation — text-to-SQL accuracy</h2>
      <p className="mt-2 max-w-2xl text-slate-400">
        The eval measures <em>execution accuracy</em>: for each question it runs a known-correct
        query directly against the database, then checks whether the SQL the agent actually ran
        returns the same answer. 12 questions × 2 runs = 24 trials.
      </p>

      <div className="card mt-6 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-edge text-left text-slate-400">
              <th className="px-5 py-3 font-medium">Model</th>
              <th className="px-5 py-3 font-medium">Backend</th>
              <th className="px-5 py-3 font-medium">Passed</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-edge/60">
              <td className="px-5 py-3 font-mono text-accent2">llama-3.3-70b-versatile</td>
              <td className="px-5 py-3 text-slate-300">Groq (hosted)</td>
              <td className="px-5 py-3 font-semibold text-white">22 / 24</td>
            </tr>
            <tr>
              <td className="px-5 py-3 font-mono text-accent2">qwen2.5:3b</td>
              <td className="px-5 py-3 text-slate-300">Ollama (local, CPU)</td>
              <td className="px-5 py-3 text-slate-400">
                often fails — usually doesn&apos;t run SQL, or makes up table names
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-sm text-slate-500">
        The local 3B model is the free default; a stronger hosted model gets the SQL right far more
        often. Per-question results are in <code>eval/RESULTS.md</code> in the repo.
      </p>
    </section>
  );
}
