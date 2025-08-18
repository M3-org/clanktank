import { ExternalLink } from 'lucide-react'
import { Card, CardContent } from '../components/Card'

export default function About() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      {/* Header */}
      <header className="text-center space-y-3">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          About Clank Tank
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-300">
          A governance game‑show where AI does the diligence, people bring the vibe, and outcomes get packaged as watchable episodes.
        </p>
        <div className="flex justify-center">
          <a
            href="https://mirror.xyz/m3org.eth/VU_Pl00hI7vRkCQPQg73Mg8906elnkvbaEvM1E2zZaE"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 underline"
          >
            Read the full story
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </header>

      {/* Video */}
      <section className="mt-8 flex justify-center">
        <div className="aspect-video w-full max-w-2xl rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800 shadow-sm">
          <iframe
            width="100%"
            height="100%"
            src="https://www.youtube.com/embed/n_g7VaO-zVE"
            title="Clank Tank Demo"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="w-full h-full"
          />
        </div>
      </section>

      {/* Origin & Lore */}
      <section className="mt-10">
        <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
          <CardContent className="p-6 md:p-8 space-y-6">
            <h2 className="text-2xl font-semibold">Origin & Lore</h2>
            <p>
              Clank Tank grew out of a simple tension: <span className="font-medium">governance is important, but boring</span>. Builders were shipping, communities were vibing, yet proposal threads sat unread and votes drifted. We asked: what if due diligence felt less like homework and more like a Friday show you couldn’t miss?
            </p>
            <p>
              In the early days, Shaw live‑coded on stream, narrating the process and inviting chat to weigh in. That transparency set a tone: open notebooks, open wallets, open minds. Then came a weekly X Space—“What Did You Get Done This Week?”—two minutes per builder, rapid‑fire feedback, and a crowd listening for signal. It wasn’t billed as pitching, but it behaved like it.
            </p>
            <p>
              Meanwhile, Solana’s DAO landscape felt like a <span className="italic">playa</span>: wide‑open, under‑tooled, and perfect for improvisation. Instead of waiting for perfect governance primitives, we leaned into culture: stories, archetypes, and a camera pointed at the decision itself. <span className="font-medium">If DAOs are coordination games, Clank Tank is the spectator sport.</span>
            </p>
          </CardContent>
        </Card>
      </section>

      {/* How it works */}
      <section className="mt-8">
        <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
          <CardContent className="p-6 md:p-8">
            <h2 className="text-2xl font-semibold mb-4">How Clank Tank Works</h2>
            <ol className="list-decimal pl-5 space-y-3 text-gray-700 dark:text-gray-300">
              <li>
                <span className="font-medium">User submissions:</span> builders submit pitches—memecoins, hacks, grants, partnerships.
              </li>
              <li>
                <span className="font-medium">Auto‑generated news show:</span> a short segment tees up the docket and frames what matters.
              </li>
              <li>
                <span className="font-medium">Round 1 — AI research + human voting:</span> agent teams crawl sources, score on fundamentals (team, traction, token design, risks), and publish summaries; the community signal‑votes.
              </li>
              <li>
                <span className="font-medium">Round 2 — Synthesis into episode:</span> scores, evidence, and votes are merged into an on‑chain/observable verdict—<span className="font-semibold">Pump · Dump · Yawn</span>—revealed in a Clank Tank episode.
              </li>
            </ol>

            <div className="mt-6 grid gap-3 text-sm text-gray-600 dark:text-gray-400">
              <p>
                <span className="font-medium">Output:</span> a crisp, distributable video recap with receipts, letting outsiders follow along without reading forum walls.
              </p>
              <p>
                <span className="font-medium">Under the hood:</span> modular agents (swappable prompts/models), pluggable data feeds, and templateable scenes so teams can fork the format.
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Judges & Archetypes */}
      <section className="mt-8">
        <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
          <CardContent className="p-6 md:p-8 space-y-4">
            <h2 className="text-2xl font-semibold">Judges & Archetypes</h2>
            <p>
              Our panel channels the voices you already hear in every crypto group chat:
            </p>
            <ul className="list-disc pl-6 space-y-1 text-gray-700 dark:text-gray-300">
              <li><span className="font-medium">Peepo</span> — community vibes, culture fit, meme surface area.</li>
              <li><span className="font-medium">aixvc</span> — numbers, market structure, on‑chain flow.</li>
              <li><span className="font-medium">degenai</span> — risk‑on instinct, narrative timing.</li>
              <li><span className="font-medium">Shaw AI</span> — builder rigor, feasibility, shipping energy.</li>
            </ul>
            <p>
              Each archetype leaves a paper trail (notes, rubrics, citations). Together they form a <span className="font-medium">trust loop</span>: transparent research → public judgment → post‑mortems when markets disagree.
            </p>
          </CardContent>
        </Card>
      </section>

      {/* Why a Media Layer */}
      <section className="mt-8">
        <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
          <CardContent className="p-6 md:p-8 space-y-4">
            <h2 className="text-2xl font-semibold">Why a Media Layer?</h2>
            <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
              <li><span className="font-medium">Attention → Participation:</span> episodes convert lurkers into voters.</li>
              <li><span className="font-medium">Receipts → Legitimacy:</span> clips, links, and on‑chain refs make judgments auditable.</li>
              <li><span className="font-medium">Format → Forkability:</span> teams can remix scenes, scoring, and judges for their own DAOs or hackathons.</li>
            </ul>
          </CardContent>
        </Card>
      </section>

      {/* Roadmap */}
      <section className="mt-8">
        <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
          <CardContent className="p-6 md:p-8 space-y-3">
            <h2 className="text-2xl font-semibold">Roadmap</h2>
            <ul className="list-disc pl-6 space-y-1 text-gray-700 dark:text-gray-300">
              <li><span className="font-medium">Season 0:</span> internal judges, memecoin & hackathon pilots, rubric hardening.</li>
              <li><span className="font-medium">Season 1:</span> external judge pools competing (Shark‑Tank style), prize‑aligned scoring.</li>
              <li><span className="font-medium">Beyond tokens:</span> grants, partnerships, integrations—same format, new domains.</li>
            </ul>
            <p className="text-base text-gray-700 dark:text-gray-300">
              The next paradigm won’t just be <span className="font-semibold">voted</span> on—it’ll be <span className="font-semibold">watched</span>.
            </p>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="text-center text-sm text-gray-500 dark:text-gray-400 pt-6">
        <p>
          Originally published on{' '}
          <a
            href="https://mirror.xyz/m3org.eth/VU_Pl00hI7vRkCQPQg73Mg8906elnkvbaEvM1E2zZaE"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 underline"
          >
            Mirror
          </a>
        </p>
      </footer>
    </div>
  )
}
