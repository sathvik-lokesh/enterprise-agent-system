// TODO: set your real LinkedIn URL (see web/README.md). Left blank so the page
// never ships a broken link.
const LINKEDIN_URL = "";

export default function Footer({ githubUrl }: { githubUrl: string }) {
  return (
    <footer className="mt-12 border-t border-edge pt-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm font-medium text-slate-200">Sathvik Lokesh</div>
          <div className="text-sm text-slate-500">
            M.Sc. Information Technology · University of Stuttgart
          </div>
        </div>
        <div className="flex flex-wrap gap-4 text-sm">
          <a
            href={githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            GitHub repo
          </a>
          {LINKEDIN_URL && (
            <a
              href={LINKEDIN_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline"
            >
              LinkedIn
            </a>
          )}
          <a href="mailto:sathvik44mysore@gmail.com" className="text-accent hover:underline">
            Email
          </a>
        </div>
      </div>
      <p className="mt-6 text-xs leading-relaxed text-slate-600">
        Live demo runs the Research-agent subset as a faithful TypeScript port of the Python
        tools, calling Groq (an OpenAI-compatible provider) so the page is always responsive. The
        full hierarchical system — Microsoft Agent Framework, embedded PostgreSQL, text-to-SQL, and
        the MCP stdio server — runs from the source repository.
      </p>
    </footer>
  );
}
