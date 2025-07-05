import React from 'react';
import { Upload, Users, PlayCircle, FlaskConical, Sparkles, BarChart3 } from 'lucide-react';

const howItWorks = [
  {
    icon: <Upload className="h-8 w-8 mb-2 fill-blue-500 text-blue-600" fill="currentColor" />,
    title: 'Submit Project',
    desc: 'You submit your hackathon project.',
    role: 'user',
  },
  {
    icon: <FlaskConical className="h-8 w-8 mb-2 text-emerald-600" strokeWidth={2.2} />,
    title: 'AI Research',
    desc: 'Clank Tank AI analyzes your project.',
    role: 'auto',
  },
  {
    icon: <BarChart3 className="h-8 w-8 mb-2 text-emerald-600" strokeWidth={2.2} />,
    title: 'AI Scoring',
    desc: 'Judges and AI score your project.',
    role: 'auto',
  },
  {
    icon: <Users className="h-8 w-8 mb-2 fill-blue-500 text-blue-600" fill="currentColor" />,
    title: 'Community Voting',
    desc: <span>The community votes in our <a href="https://discord.gg/ai16z" target="_blank" rel="noopener noreferrer" className="text-blue-700 underline">Discord</a> (channel TBA).</span>,
    role: 'user',
  },
  {
    icon: <Sparkles className="h-8 w-8 mb-2 text-emerald-600" strokeWidth={2.2} />,
    title: 'Synthesis',
    desc: 'Final verdict and synthesis.',
    role: 'auto',
  },
  {
    icon: <PlayCircle className="h-8 w-8 mb-2 text-emerald-600" strokeWidth={2.2} />,
    title: 'Watch Episodes',
    desc: 'See results in leaderboard & episodes.',
    role: 'auto',
  },
];

const judges = [
  { name: 'Aimarc', avatar: '/avatars/aimarc.png', tag: 'ROI skeptic' },
  { name: 'Aishaw', avatar: '/avatars/aishaw.png', tag: 'Code purist' },
  { name: 'Peepo', avatar: '/avatars/peepo.png', tag: 'UX meme lord' },
  { name: 'Spartan', avatar: '/avatars/spartan.png', tag: 'DeFi maximalist' },
];

const faqs = [
  {
    q: 'How many rounds are there?',
    a: 'There are two main rounds: Round 1 (AI judge scoring) and Round 2 (community voting + judge synthesis).'
  },
  {
    q: 'How does community voting work?',
    a: <span>Voting happens in our <a href="https://discord.gg/ai16z" target="_blank" rel="noopener noreferrer" className="text-indigo-700 underline">Discord</a> (channel TBA). Anyone can join, react, and leave feedback on their favorite projects.</span>
  },
  {
    q: 'What do the judges look for?',
    a: 'Each judge has a unique style: Aimarc (business/ROI), Aishaw (technical depth), Peepo (user experience), Spartan (DeFi/crypto). See above for details.'
  },
  {
    q: 'How do I get featured in an episode?',
    a: 'Top projects from the leaderboard are selected for Clank Tank episodes and may be showcased on stream or in highlight videos.'
  },
  {
    q: 'Where can I ask questions or get help?',
    a: <span>Join our <a href="https://discord.gg/ai16z" target="_blank" rel="noopener noreferrer" className="text-indigo-700 underline">Discord</a> for support, updates, and community chat.</span>
  },
];

export default function Frontpage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Header */}
      <div className="relative w-full flex items-center justify-center overflow-hidden sm:py-28 py-20">
        {/* Hero background: looping video */}
        <div className="absolute inset-0 w-full h-full z-0">
          <video
            src="/loop.mp4"
            autoPlay
            loop
            muted
            playsInline
            className="w-full h-full object-cover object-center"
            style={{ filter: 'brightness(0.5) contrast(1.1)' }}
          />
          {/* Dither/noise overlay */}
          <div className="absolute inset-0 pointer-events-none" style={{ background: 'url("/noise.png")', opacity: 0.12, mixBlendMode: 'overlay' }} />
          {/* Extra darken overlay for text readability */}
          <div className="absolute inset-0 bg-black bg-opacity-60" />
        </div>
        <div className="relative z-10 flex flex-col items-center justify-center text-center px-4 w-full">
          <img src="/clanktank_white.png" alt="Clank Tank Logo" className="h-38 md:h-80 w-auto mx-auto mb-2 drop-shadow-lg" style={{ maxWidth: '90vw' }} />
          <div className="text-2xl md:text-3xl font-extrabold text-indigo-200 tracking-widest uppercase drop-shadow mb-6">hackathon edition</div>
 
          <p className="text-xl md:text-2xl font-semibold text-indigo-100 drop-shadow mb-8 max-w-2xl mx-auto">
            AI-Powered Vibe Coding Competition
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="#how-it-works" className="inline-block text-lg font-semibold px-6 py-3 rounded-full bg-indigo-600 text-white shadow-lg hover:bg-indigo-700 transition">
              How it works
            </a>
            <a href="/leaderboard" className="inline-block text-lg font-semibold px-6 py-3 rounded-full border border-indigo-300 text-indigo-100 bg-white/10 hover:bg-indigo-100 hover:text-indigo-700 transition">
              View Leaderboard
            </a>
          </div>
        </div>
      </div>

      {/* How it Works Section */}
      <section id="how-it-works" className="bg-slate-50 dark:bg-gray-950 animate-fade-in">
        <div className="max-w-5xl mx-auto py-16 px-4">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 text-center md:text-left">How the Hackathon Works</h2>
            {/* Pill badge legend */}
            <div className="flex gap-2 items-center text-sm">
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-100 font-semibold">● You</span>
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-100 font-semibold">● Automated</span>
            </div>
          </div>
          <div className="relative">
            {/* Dashed timeline for each row */}
            <div className="absolute inset-x-0 top-[23%] md:top-[22%] h-0.5 border-t border-dashed border-muted/40 z-0" style={{zIndex:0}} />
            <div className="absolute inset-x-0 top-[72%] md:top-[72%] h-0.5 border-t border-dashed border-muted/40 z-0" style={{zIndex:0}} />
            <div className="relative grid grid-rows-2 grid-cols-3 gap-8 z-10">
              {/* First row: Submit Project, AI Research, AI Scoring */}
              <div className="row-start-1 col-start-1">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-blue-50 dark:bg-blue-900 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-blue-200/80 text-blue-700">1</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[0].icon, { strokeWidth: 2, className: `h-10 w-10 text-blue-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 mt-2">{howItWorks[0].title}</h3>
                  <p className="text-base text-gray-700 dark:text-gray-300 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[0].desc}</p>
                </div>
              </div>
              <div className="row-start-1 col-start-2">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-emerald-50 dark:bg-emerald-900 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-200/80 text-emerald-700">2</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[1].icon, { strokeWidth: 2, className: `h-10 w-10 text-emerald-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 mt-2">{howItWorks[1].title}</h3>
                  <p className="text-base text-gray-700 dark:text-gray-300 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[1].desc}</p>
                </div>
              </div>
              <div className="row-start-1 col-start-3">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-emerald-50 dark:bg-emerald-900 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-200/80 text-emerald-700">3</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[2].icon, { strokeWidth: 2, className: `h-10 w-10 text-emerald-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 mt-2">{howItWorks[2].title}</h3>
                  <p className="text-base text-gray-700 dark:text-gray-300 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[2].desc}</p>
                </div>
              </div>
              {/* Second row: Community Voting, Synthesis, Watch Episodes */}
              <div className="row-start-2 col-start-1">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-blue-50 dark:bg-blue-900 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-blue-200/80 text-blue-700">4</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[3].icon, { strokeWidth: 2, className: `h-10 w-10 text-blue-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 mt-2">{howItWorks[3].title}</h3>
                  <p className="text-base text-gray-700 dark:text-gray-300 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[3].desc}</p>
                </div>
              </div>
              <div className="row-start-2 col-start-2">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-emerald-50 dark:bg-emerald-900 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-200/80 text-emerald-700">5</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[4].icon, { strokeWidth: 2, className: `h-10 w-10 text-emerald-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 mt-2">{howItWorks[4].title}</h3>
                  <p className="text-base text-gray-700 dark:text-gray-300 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[4].desc}</p>
                </div>
              </div>
              <div className="row-start-2 col-start-3">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-emerald-50 dark:bg-emerald-900 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-200/80 text-emerald-700">6</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[5].icon, { strokeWidth: 2, className: `h-10 w-10 text-emerald-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 mt-2">{howItWorks[5].title}</h3>
                  <p className="text-base text-gray-700 dark:text-gray-300 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[5].desc}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Judges Panel */}
      <section className="bg-white dark:bg-gray-900 animate-fade-in">
        <div className="max-w-4xl mx-auto py-12 px-4">
          <h2 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6 text-center">Meet the Judges</h2>
          <div className="flex flex-wrap justify-center gap-8">
            {judges.map(j => (
              <div key={j.name} className="flex flex-col items-center">
                <img src={j.avatar} alt={j.name} className="h-28 w-28 rounded-full border border-gray-200 dark:border-gray-700 mb-2 bg-white dark:bg-gray-900 object-cover" />
                <span className="font-bold text-xl text-gray-800 dark:text-gray-100 mt-1">{j.name}</span>
                <span className="text-xs text-indigo-600 dark:text-indigo-300 mt-1" style={{ height: 32 }}>{j.tag}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-slate-50 dark:bg-gray-950 animate-fade-in">
        <div className="max-w-3xl mx-auto py-16 px-4">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-10 text-center">FAQ</h2>
          <div className="space-y-8">
            {faqs.map((faq, i) => (
              <div key={i} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold text-indigo-700 dark:text-indigo-300 mb-2">{faq.q}</h3>
                <div className="text-gray-700 dark:text-gray-300 text-base leading-relaxed">{faq.a}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
} 