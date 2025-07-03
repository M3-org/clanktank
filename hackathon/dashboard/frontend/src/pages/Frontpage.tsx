import React from 'react';
import { Upload, Search, Sliders, Users, MessageCircle, Star, Trophy, MessageSquare } from 'lucide-react';

const howItWorks = [
  {
    icon: <Upload className="h-8 w-8 text-indigo-600 mb-2" />,
    title: 'Submit',
    desc: 'Teams submit their projects with a description, code, and demo video.'
  },
  {
    icon: <Search className="h-8 w-8 text-indigo-600 mb-2" />,
    title: 'Research',
    desc: 'Automated research and GitHub analysis enrich each submission.'
  },
  {
    icon: <Sliders className="h-8 w-8 text-indigo-600 mb-2" />,
    title: 'Scoring',
    desc: 'AI judges score each project on innovation, technical execution, market potential, and user experience.'
  },
  {
    icon: <Users className="h-8 w-8 text-indigo-600 mb-2" />,
    title: 'Community Voting',
    desc: <span>The community votes and gives feedback in our <a href="https://discord.gg/ai16z" target="_blank" rel="noopener noreferrer" className="text-indigo-700 underline">Discord</a> (channel TBA).</span>
  },
  {
    icon: <MessageCircle className="h-8 w-8 text-indigo-600 mb-2" />,
    title: 'Synthesis',
    desc: 'Judges synthesize their verdicts, factoring in community sentiment.'
  },
  {
    icon: <Trophy className="h-8 w-8 text-indigo-600 mb-2" />,
    title: 'Leaderboard & Episodes',
    desc: 'Top projects are featured on the leaderboard and in Clank Tank episodes.'
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
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-10 text-center">How the Hackathon Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {howItWorks.map((step, i) => (
              <div key={step.title} className="flex flex-col items-center text-center p-6 bg-white rounded-xl shadow-sm h-full">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-indigo-50 mb-3">
                  <span className="text-xl font-bold text-indigo-600">{i + 1}</span>
                </div>
                {step.icon}
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{step.desc}</p>
              </div>
            ))}
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