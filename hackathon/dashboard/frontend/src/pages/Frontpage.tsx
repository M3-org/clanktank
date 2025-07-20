import React from 'react';
import { Upload, Users, PlayCircle, FlaskConical, Sparkles, BarChart3, Plus } from 'lucide-react';
import { CountdownTimer } from '../components/CountdownTimer';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { PrizePool } from '../components/PrizePool';

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
    desc: 'AI judges score your project.',
    role: 'auto',
  },
  {
    icon: <Users className="h-8 w-8 mb-2 fill-blue-500 text-blue-600" fill="currentColor" />,
    title: 'Community Voting',
    desc: <span>The community votes in our <a href="https://discord.gg/ai16z" target="_blank" rel="noopener noreferrer" className="text-blue-700 underline">Discord</a>.</span>,
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
  const { authState } = useAuth()
  const navigate = useNavigate()

  // Hardcoded video data for all 8 episodes
  const latestEpisodes = [
    {
      id: 'R-oObQtsksw',
      title: 'Clank Tank Season 1 Episode 1',
      url: 'https://www.youtube.com/watch?v=R-oObQtsksw',
      thumbnail: 'https://i.ytimg.com/vi/R-oObQtsksw/hqdefault.jpg',
      view_count: 2200,
      duration: 653,
    },
    {
      id: 'ldYcVK4X6Qk',
      title: 'Clank Tank Season 1 Episode 2',
      url: 'https://www.youtube.com/watch?v=ldYcVK4X6Qk',
      thumbnail: 'https://i.ytimg.com/vi/ldYcVK4X6Qk/hqdefault.jpg',
      view_count: 375,
      duration: 514,
    },
    {
      id: 'mY6gEcoC-fE',
      title: 'Clank Tank Season 1 Episode 3',
      url: 'https://www.youtube.com/watch?v=mY6gEcoC-fE',
      thumbnail: 'https://i.ytimg.com/vi/mY6gEcoC-fE/hqdefault.jpg',
      view_count: 232,
      duration: 3197,
    },
    {
      id: 'ZEsQPhNjLBQ',
      title: 'Clank Tank S1E3: Nounspace Tom, Social',
      url: 'https://www.youtube.com/watch?v=ZEsQPhNjLBQ',
      thumbnail: 'https://i.ytimg.com/vi/ZEsQPhNjLBQ/hqdefault.jpg',
      view_count: 50,
      duration: 1137,
    },
    {
      id: 'J0UC8JgKD4Y',
      title: 'Clank Tank S1E4: Silkroad, Eido, Rita',
      url: 'https://www.youtube.com/watch?v=J0UC8JgKD4Y',
      thumbnail: 'https://i.ytimg.com/vi/J0UC8JgKD4Y/hqdefault.jpg',
      view_count: 287,
      duration: 824,
    },
    {
      id: 'gLlIs-a1nkw',
      title: 'Clank Tank Launch Trailer / Intro',
      url: 'https://www.youtube.com/watch?v=gLlIs-a1nkw',
      thumbnail: 'https://i.ytimg.com/vi/gLlIs-a1nkw/hqdefault.jpg',
      view_count: 2,
      duration: 35,
    },
    {
      id: 'Q6PATiyZmI0',
      title: 'Clank Tank Episode 4 Sizzler',
      url: 'https://www.youtube.com/watch?v=Q6PATiyZmI0',
      thumbnail: 'https://i.ytimg.com/vi/Q6PATiyZmI0/hqdefault.jpg',
      view_count: 0,
      duration: 39,
    },
    {
      id: 'n_g7VaO-zVE',
      title: 'Clank Tank Announcement Trailer',
      url: 'https://www.youtube.com/watch?v=n_g7VaO-zVE',
      thumbnail: 'https://i.ytimg.com/vi/n_g7VaO-zVE/hqdefault.jpg',
      view_count: 3,
      duration: 43,
    },
  ].slice().reverse();

  // Lightbox state
  const [openVideo, setOpenVideo] = React.useState<string | null>(null);

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
          <div className="relative inline-block">
            {/* Left gear - adjusted for smaller logo */}
            <svg
              className="absolute -left-8 -top-2 -translate-x-1/3 -translate-y-1/2 h-16 md:h-20 w-16 md:w-20 opacity-90 animate-spin-slow z-0 text-gray-300"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 8 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 8a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 8 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09c0 .66.38 1.26 1 1.51a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 8c.66 0 1.26.38 1.51 1H21a2 2 0 0 1 0 4h-.09c-.25 0-.49.09-.68.26z" />
            </svg>
            
            {/* Main logo */}
            <img src="/clanktank_white.png" alt="Clank Tank Logo" className="relative z-10 h-20 md:h-32 w-auto mx-auto mb-2 drop-shadow-lg" style={{ maxWidth: '90vw' }} />
            
            {/* Right gear - adjusted for smaller logo */}
            <svg
              className="absolute -right-8 top-1/4 translate-x-1/2 -translate-y-1/3 h-16 md:h-20 w-16 md:w-20 opacity-90 animate-spin-slow z-0 text-gray-300"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 8 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 8a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 8 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09c0 .66.38 1.26 1 1.51a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 8c.66 0 1.26.38 1.51 1H21a2 2 0 0 1 0 4h-.09c-.25 0-.49.09-.68.26z" />
            </svg>
          </div>
          <div className="text-2xl md:text-3xl font-extrabold text-indigo-200 tracking-widest uppercase drop-shadow mb-6">hackathon edition</div>
 
          <p className="text-xl md:text-2xl font-semibold text-indigo-100 drop-shadow mb-8 max-w-2xl mx-auto">
            AI-Powered Vibe Coding Competition
          </p>
          
          {/* Countdown and Submit */}
          <div className="mt-8 flex flex-col items-center gap-6">
            <div className="max-w-md mx-auto">
              <CountdownTimer variant="banner" showLabel={true} />
            </div>
            
            <button
              onClick={() => authState.isAuthenticated ? navigate('/submit') : navigate('/auth')}
              className="flex items-center gap-2 px-6 py-3 bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/20 text-white font-medium rounded-lg transition-all duration-200 hover:scale-105"
            >
              <Plus className="h-5 w-5" />
              Submit Project
            </button>
          </div>
        </div>
      </div>

      {/* Latest Episodes Section */}
      <section className="bg-white dark:bg-gray-900 py-12 animate-fade-in">
        <div className="max-w-5xl mx-auto px-4">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8 text-center">Latest Episodes</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8">
            {latestEpisodes.map((ep) => (
              <div
                key={ep.id}
                onClick={() => setOpenVideo(ep.id)}
                className="group rounded-xl overflow-hidden shadow-lg bg-slate-50 dark:bg-gray-800 hover:shadow-2xl transition border border-gray-200 dark:border-gray-700 cursor-pointer"
                role="button"
                tabIndex={0}
                onKeyPress={e => { if (e.key === 'Enter') setOpenVideo(ep.id); }}
                aria-label={`Play ${ep.title}`}
              >
                <div className="relative aspect-video w-full overflow-hidden">
                  <img
                    src={ep.thumbnail}
                    alt={ep.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                    {Math.floor(ep.duration / 60)}:{(ep.duration % 60).toString().padStart(2, '0')}
                  </div>
                </div>
                <div className="p-4">
                  <div className="font-semibold text-base text-gray-900 dark:text-gray-100 mb-1 line-clamp-2 min-h-[2.5em]">{ep.title}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">{ep.view_count} views</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Lightbox Video Player */}
      {openVideo && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80"
          onClick={() => setOpenVideo(null)}
        >
          <div
            className="relative w-full max-w-3xl aspect-video"
            onClick={e => e.stopPropagation()}
          >
            <button
              onClick={() => setOpenVideo(null)}
              className="absolute top-2 right-2 text-white text-2xl z-10 bg-black bg-opacity-50 rounded-full w-10 h-10 flex items-center justify-center hover:bg-opacity-80 transition"
              aria-label="Close"
            >
              ×
            </button>
            <iframe
              src={`https://www.youtube.com/embed/${openVideo}?autoplay=1`}
              title="Clank Tank Video"
              allow="autoplay; encrypted-media"
              allowFullScreen
              className="w-full h-full rounded-lg"
            />
          </div>
        </div>
      )}

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
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[5].icon, { strokeWidth: 2, className: 'h-10 w-10 text-emerald-600' })}</div>
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
                <img 
                  src={j.avatar} 
                  alt={j.name} 
                  className="h-28 w-28 rounded-full border border-gray-200 dark:border-gray-700 mb-2 bg-white dark:bg-gray-900 object-cover"
                  width="112"
                  height="112"
                  loading="lazy"
                />
                <span className="font-bold text-xl text-gray-800 dark:text-gray-100 mt-1">{j.name}</span>
                <span className="text-xs text-indigo-600 dark:text-indigo-300 mt-1" style={{ height: 32 }}>{j.tag}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Prize Pool Section */}
      <section className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-950 animate-fade-in">
        <div className="max-w-6xl mx-auto py-16 px-4">
          <PrizePool goal={10} variant="card" />
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