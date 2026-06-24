import Hero from "@/components/Hero";
import Architecture from "@/components/Architecture";
import HowItWorks from "@/components/HowItWorks";
import Eval from "@/components/Eval";
import Demo from "@/components/Demo";
import Footer from "@/components/Footer";

const GITHUB_URL = "https://github.com/sathvik-lokesh/enterprise-agent-system";

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-5 pb-24">
      <Hero githubUrl={GITHUB_URL} />
      <Architecture />
      <HowItWorks />
      <Eval />
      <Demo />
      <Footer githubUrl={GITHUB_URL} />
    </main>
  );
}
