import React from 'react';
import { Upload, Search, Sliders, Users, MessageCircle, Star, Trophy, MessageSquare, PlayCircle, FlaskConical, Sparkles, BarChart3 } from 'lucide-react';

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
      <div className="relative w-full flex items-center justify-center overflow-hidden bg-gradient-to-br from-indigo-600 to-slate-900 sm:py-28 py-20">
        {/* White noise overlay */}
        <div className="absolute inset-0 pointer-events-none" style={{ backgroundImage: 'url("/noise.png")', opacity: 0.05 }} />
        <div className="absolute inset-0 bg-black bg-opacity-40" />
        <div className="relative z-10 flex flex-col items-center justify-center text-center px-4 w-full">
          <h1 className="text-4xl md:text-6xl font-extrabold text-white drop-shadow-lg mb-4 tracking-tight max-w-3xl mx-auto">
            Clank Tank Hackathon
          </h1>
          <p className="text-lg md:text-2xl text-indigo-100 font-medium mb-8 max-w-2xl mx-auto">
            AI-powered, community-judged innovation tournament
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
      <section id="how-it-works" className="bg-slate-50 animate-fade-in">
        <div className="max-w-5xl mx-auto py-16 px-4">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 text-center md:text-left">How the Hackathon Works</h2>
            {/* Pill badge legend */}
            <div className="flex gap-2 items-center text-sm">
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-100 text-blue-700 font-semibold">● You</span>
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 font-semibold">● Automated</span>
            </div>
          </div>
          <div className="relative">
            {/* Dashed timeline for each row */}
            <div className="absolute inset-x-0 top-[23%] md:top-[22%] h-0.5 border-t border-dashed border-muted/40 z-0" style={{zIndex:0}} />
            <div className="absolute inset-x-0 top-[72%] md:top-[72%] h-0.5 border-t border-dashed border-muted/40 z-0" style={{zIndex:0}} />
            <div className="relative grid grid-rows-2 grid-cols-3 gap-8 z-10">
              {/* First row: Submit Project, AI Research, AI Scoring */}
              <div className="row-start-1 col-start-1">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-blue-50 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-blue-200/80 text-blue-700">1</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[0].icon, { strokeWidth: 2, className: `h-10 w-10 text-blue-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2 mt-2">{howItWorks[0].title}</h3>
                  <p className="text-base text-gray-700 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[0].desc}</p>
                </div>
              </div>
              <div className="row-start-1 col-start-2">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-emerald-50 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-200/80 text-emerald-700">2</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[1].icon, { strokeWidth: 2, className: `h-10 w-10 text-emerald-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2 mt-2">{howItWorks[1].title}</h3>
                  <p className="text-base text-gray-700 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[1].desc}</p>
                </div>
              </div>
              <div className="row-start-1 col-start-3">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-emerald-50 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-200/80 text-emerald-700">3</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[2].icon, { strokeWidth: 2, className: `h-10 w-10 text-emerald-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2 mt-2">{howItWorks[2].title}</h3>
                  <p className="text-base text-gray-700 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[2].desc}</p>
                </div>
              </div>
              {/* Second row: Community Voting, Synthesis, Watch Episodes */}
              <div className="row-start-2 col-start-1">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-blue-50 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-blue-200/80 text-blue-700">4</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[3].icon, { strokeWidth: 2, className: `h-10 w-10 text-blue-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2 mt-2">{howItWorks[3].title}</h3>
                  <p className="text-base text-gray-700 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[3].desc}</p>
                </div>
              </div>
              <div className="row-start-2 col-start-2">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-emerald-50 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-200/80 text-emerald-700">5</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[4].icon, { strokeWidth: 2, className: `h-10 w-10 text-emerald-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2 mt-2">{howItWorks[4].title}</h3>
                  <p className="text-base text-gray-700 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[4].desc}</p>
                </div>
              </div>
              <div className="row-start-2 col-start-3">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-emerald-50 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-200/80 text-emerald-700">6</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[5].icon, { strokeWidth: 2, className: `h-10 w-10 text-emerald-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2 mt-2">{howItWorks[5].title}</h3>
                  <p className="text-base text-gray-700 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[5].desc}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Judges Panel */}
      <section className="bg-white animate-fade-in">
        <div className="max-w-4xl mx-auto py-12 px-4">
          <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-6 text-center">Meet the Judges</h2>
          <div className="flex flex-wrap justify-center gap-8">
            {judges.map(j => (
              <div key={j.name} className="flex flex-col items-center">
                <img src={j.avatar} alt={j.name} className="h-16 w-16 rounded-full border border-gray-200 mb-2 bg-white object-cover" />
                <span className="font-semibold text-gray-800">{j.name}</span>
                <span className="text-xs text-indigo-600 mt-1" style={{ height: 32 }}>{j.tag}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-slate-50 animate-fade-in">
        <div className="max-w-3xl mx-auto py-16 px-4">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-10 text-center">FAQ</h2>
          <div className="space-y-8">
            {faqs.map((faq, i) => (
              <div key={i} className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold text-indigo-700 mb-2">{faq.q}</h3>
                <div className="text-gray-700 text-base leading-relaxed">{faq.a}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
} 