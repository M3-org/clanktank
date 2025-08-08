import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Users, PlayCircle, FlaskConical, Copy, Check, ChevronLeft, ChevronRight } from 'lucide-react';
import { VoteModal } from '../components/VoteModal';
import { SubmissionModal } from '../components/SubmissionModal';
import { hackathonApi } from '../lib/api';
import { LeaderboardEntry } from '../types';
import { useCopyToClipboard } from '../hooks/useCopyToClipboard';
import { TOAST_MESSAGES } from '../lib/constants';

const howItWorks = [
  // Round 1
  {
    icon: <Upload className="h-8 w-8 mb-2 fill-blue-500 text-blue-600" fill="currentColor" />,
    title: 'Submit Project',
    desc: 'You submit your hackathon project.',
    role: 'user',
  },
  {
    icon: <FlaskConical className="h-8 w-8 mb-2 text-emerald-600" strokeWidth={2.2} />,
    title: 'AI Research & Scoring',
    desc: 'AI analyzes and scores your project.',
    role: 'auto',
  },
  // Round 2
  {
    icon: <Users className="h-8 w-8 mb-2 fill-blue-500 text-blue-600" fill="currentColor" />,
    title: 'Community Voting',
    desc: 'The community votes on-chain with memos',
    role: 'user',
  },
  {
    icon: <PlayCircle className="h-8 w-8 mb-2 text-emerald-600" strokeWidth={2.2} />,
    title: 'Synthesis Episode',
    desc: 'Winners appear on Clank Tank.',
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
    a: 'There are two main rounds: Round 1 (AI judge scoring) and Round 2 (community voting + judge synthesis). Then the top 5 projects are featured on Clank Tank.'
  },
  {
    q: 'How does community voting work?',
    a: <span>Send ai16z tokens to the voting wallet with the project's submission ID as a memo. Your voting power is measured by your ai16z holding amount - any amount counts as a vote! Use Phantom wallet for best memo support.</span>
  },
  {
    q: 'What do the judges look for?',
    a: 'Each judge has a unique style: Aimarc (business/ROI), Aishaw (technical depth), Peepo (user experience), Spartan (DeFi/crypto). See above for details.'
  },
  {
    q: 'How do I get featured in an episode?',
    a: 'Top 5 projects will be featured on Clank Tank and live premiered for the final round.'
  },
  {
    q: 'Where can I ask questions or get help?',
    a: <span>Join our <a href="https://discord.gg/ai16z" target="_blank" rel="noopener noreferrer" className="text-indigo-700 underline">Discord</a> for support, updates, and community chat.</span>
  },
];

const VOTING_WALLET = '7ErPek9uyReCBwiLkTi3DbqNDRf2Kmz4BShGhXmWLebx'

export default function Frontpage() {
  // Phase-based logic using SUBMISSION_DEADLINE
  const submissionDeadline = import.meta.env.VITE_SUBMISSION_DEADLINE
  const isAfterDeadline = submissionDeadline ? new Date() > new Date(submissionDeadline) : false
  const showLeaderboard = isAfterDeadline
  
  // Format deadline for display
  const deadlineDisplay = submissionDeadline 
    ? new Date(submissionDeadline).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric', 
        month: 'long', 
        day: 'numeric'
      })
    : 'TBD'

  // Leaderboard state and modals
  const [leaderboardEntries, setLeaderboardEntries] = useState<LeaderboardEntry[]>([])
  const [leaderboardLoading, setLeaderboardLoading] = useState(false)
  const [selectedSubmission, setSelectedSubmission] = useState<LeaderboardEntry | null>(null)
  const [votingSubmission, setVotingSubmission] = useState<LeaderboardEntry | null>(null)
  const { copied, copyToClipboard } = useCopyToClipboard()

  // Load leaderboard data only after deadline
  useEffect(() => {
    if (!showLeaderboard) return
    
    const loadLeaderboard = async () => {
      setLeaderboardLoading(true)
      try {
        const data = await hackathonApi.getLeaderboard()
        setLeaderboardEntries(data?.slice(0, 10) || []) // Top 10 for side-by-side tables
      } catch (error) {
        console.error('Failed to load leaderboard:', error)
        setLeaderboardEntries([])
      } finally {
        setLeaderboardLoading(false)
      }
    }
    loadLeaderboard()
  }, [showLeaderboard])

  const handleCopyVotingWallet = () => {
    copyToClipboard(VOTING_WALLET, TOAST_MESSAGES.ADDRESS_COPIED)
  }

  const getRankBadge = (rank: number) => {
    if (rank === 1) {
      return <div className="h-8 w-8 rounded-full bg-yellow-400 text-slate-900 font-bold flex items-center justify-center text-sm">1</div>
    } else if (rank === 2) {
      return <div className="h-8 w-8 rounded-full bg-gray-400 text-slate-900 font-bold flex items-center justify-center text-sm">2</div>
    } else if (rank === 3) {
      return <div className="h-8 w-8 rounded-full bg-amber-600 text-white font-bold flex items-center justify-center text-sm">3</div>
    } else {
      return <div className="h-8 w-8 rounded-full bg-slate-600 text-slate-300 font-bold flex items-center justify-center text-sm">{rank}</div>
    }
  }


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

  // Episodes pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const episodesPerPage = 6;

  // Touch state for lightbox navigation
  const [touchStart, setTouchStart] = useState(0);
  const [touchEnd, setTouchEnd] = useState(0);

  // Video navigation functions
  const getCurrentVideoIndex = useCallback(() => {
    return latestEpisodes.findIndex(ep => ep.id === openVideo);
  }, [latestEpisodes, openVideo]);

  const navigateToVideo = useCallback((index: number) => {
    if (index >= 0 && index < latestEpisodes.length) {
      setOpenVideo(latestEpisodes[index].id);
    }
  }, [latestEpisodes]);

  const goToPreviousVideo = useCallback(() => {
    const currentIndex = getCurrentVideoIndex();
    if (currentIndex > 0) {
      navigateToVideo(currentIndex - 1);
    }
  }, [getCurrentVideoIndex, navigateToVideo]);

  const goToNextVideo = useCallback(() => {
    const currentIndex = getCurrentVideoIndex();
    if (currentIndex < latestEpisodes.length - 1) {
      navigateToVideo(currentIndex + 1);
    }
  }, [getCurrentVideoIndex, navigateToVideo, latestEpisodes.length]);

  // Keyboard navigation for lightbox
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!openVideo) return;
      
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        goToPreviousVideo();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        goToNextVideo();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setOpenVideo(null);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [openVideo, goToPreviousVideo, goToNextVideo]);

  // Touch handlers for lightbox swipe
  const handleLightboxTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.targetTouches[0].clientX);
  };

  const handleLightboxTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const handleLightboxTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > 50;
    const isRightSwipe = distance < -50;

    if (isLeftSwipe) {
      goToNextVideo();
    } else if (isRightSwipe) {
      goToPreviousVideo();
    }

    setTouchStart(0);
    setTouchEnd(0);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Video Section */}
      <section className="w-full relative bg-gradient-to-b from-slate-950 via-slate-900 to-slate-800 overflow-hidden">
        {/* Responsive aspect ratio container */}
        <div className="relative w-full" style={{ paddingBottom: '56.25%' /* 16:9 aspect ratio */ }}>
          <div className="absolute inset-0">
            <video
              src="/loop.mp4"
              autoPlay
              loop
              muted
              playsInline
              className="w-full h-full object-cover"
            />
            {/* 
            Future YouTube embed structure (commented for reference):
            <iframe
              src="https://www.youtube.com/embed/VIDEO_ID?autoplay=1&mute=1&loop=1&playlist=VIDEO_ID&controls=0&showinfo=0&rel=0&iv_load_policy=3&modestbranding=1"
              title="Hero Video"
              frameBorder="0"
              allow="autoplay; encrypted-media"
              allowFullScreen
              className="w-full h-full"
              style={{ 
                width: '100%', 
                height: '100%',
                aspectRatio: '16/9'
              }}
            />
            */}
          </div>
          
          {/* Overlay content - Phase-based - Constrained to video bounds */}
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center overflow-hidden">
            <div className="text-center px-4 sm:px-6 max-w-4xl mx-auto w-full h-full flex flex-col justify-center items-center">
              {showLeaderboard ? (
                /* After deadline - Watch & Vote */
                <>
                  <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-4 leading-tight">
                    Watch & Vote
                  </h1>
                  <p className="text-base sm:text-lg md:text-xl text-white/90 max-w-2xl mx-auto leading-relaxed">
                    AI judges have scored the submissions. Now it's your turn to vote!
                  </p>
                </>
              ) : (
                /* Before deadline - Original content */
                <>
                  <div className="relative inline-block mb-4 sm:mb-6">
                    {/* Left gear */}
                    <svg
                      className="absolute -left-4 sm:-left-6 md:-left-8 -top-1 sm:-top-2 -translate-x-1/4 sm:-translate-x-1/3 -translate-y-1/2 h-8 sm:h-10 md:h-12 lg:h-16 w-8 sm:w-10 md:w-12 lg:w-16 opacity-90 animate-spin-slow z-0 text-gray-300"
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
                    <img src="/clanktank_white.png" alt="Clank Tank Logo" className="relative z-10 h-12 sm:h-16 md:h-20 lg:h-24 w-auto mx-auto drop-shadow-lg" />
                    
                    {/* Right gear */}
                    <svg
                      className="absolute -right-4 sm:-right-6 md:-right-8 top-1/4 translate-x-1/4 sm:translate-x-1/2 -translate-y-1/3 h-8 sm:h-10 md:h-12 lg:h-16 w-8 sm:w-10 md:w-12 lg:w-16 opacity-90 animate-spin-slow z-0 text-gray-300"
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
                  
                  <div className="text-sm sm:text-base md:text-xl lg:text-2xl font-extrabold text-indigo-200 tracking-widest uppercase drop-shadow-lg mb-3 sm:mb-4" style={{ textShadow: '2px 2px 8px rgba(0,0,0,0.7)' }}>AI-powered Game Show</div>
                  
                  <div className="flex flex-col items-center gap-3 sm:gap-4 mt-2 sm:mt-4">
                    <button
                      onClick={() => setOpenVideo('gLlIs-a1nkw')}
                      className="flex items-center justify-center p-2 bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/20 text-white rounded-full transition-all duration-200 hover:scale-110"
                      title="Watch Trailer"
                    >
                      <PlayCircle className="h-8 w-8 sm:h-10 sm:w-10" />
                    </button>
                    
                    <h2 className="text-sm sm:text-base md:text-lg lg:text-xl font-medium text-white/90 leading-tight px-2 sm:px-0" style={{ WebkitTextStroke: '1px rgba(255,255,255,0.3)', textShadow: '0 0 10px rgba(255,255,255,0.3), 2px 2px 8px rgba(0,0,0,0.8)' }}>
                      Submission Deadline: {deadlineDisplay}
                    </h2>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Conditional Leaderboard Section - Only show after deadline - Position 2 */}
      {showLeaderboard && (
        <section className="bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-gray-100 py-12 animate-fade-in relative overflow-hidden">
          {/* Subtle geometric background pattern */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_40%,rgba(120,119,198,0.3),transparent_50%)] dark:bg-[radial-gradient(circle_at_30%_40%,rgba(120,119,198,0.1),transparent_50%)]"></div>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(168,85,247,0.2),transparent_50%)] dark:bg-[radial-gradient(circle_at_70%_80%,rgba(168,85,247,0.05),transparent_50%)]"></div>
          <div className="max-w-7xl mx-auto px-4 relative z-10">
            {/* Header with voting instructions */}
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 lg:gap-4 mb-6 border-b border-slate-800 pb-4">
              <h2 className="text-2xl md:text-3xl font-bold text-white">Top 10 Leaderboard</h2>
              
              <div className="bg-slate-800/30 rounded-lg p-2.5 border border-slate-700 lg:bg-transparent lg:border-0 lg:p-0">
                <div className="flex flex-col sm:flex-row sm:items-center lg:flex-row lg:items-center gap-2 text-sm lg:flex-wrap lg:justify-end">
                  <div className="flex items-center gap-1 flex-wrap lg:whitespace-nowrap">
                    <span className="font-semibold text-indigo-400">Vote:</span>
                    <span>Send</span>
                    <span className="font-semibold text-indigo-400">ai16z</span>
                    <span>to</span>
                  </div>
                  
                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      onClick={handleCopyVotingWallet}
                      className="flex items-center gap-1 px-2 py-1 bg-slate-700/80 hover:bg-slate-600/80 rounded border border-slate-600 hover:border-indigo-400 transition-all duration-200 group"
                      title="Copy wallet address"
                    >
                      <span className="text-slate-300 font-mono text-xs">
                        <span className="hidden md:inline">{VOTING_WALLET.slice(0, 8)}…{VOTING_WALLET.slice(-8)}</span>
                        <span className="md:hidden">{VOTING_WALLET.slice(0, 6)}…{VOTING_WALLET.slice(-6)}</span>
                      </span>
                      {copied ? (
                        <Check className="w-3 h-3 text-green-400" />
                      ) : (
                        <Copy className="w-3 h-3 text-indigo-400 group-hover:text-indigo-300" />
                      )}
                    </button>
                    <span className="whitespace-nowrap">with Memo <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-xs font-mono">ID</kbd></span>
                  </div>
                </div>
              </div>
            </div>

            {leaderboardLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto"></div>
              </div>
            ) : leaderboardEntries.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                No submissions found
              </div>
            ) : (
              /* Single leaderboard table */
              <div className="bg-slate-800/30 rounded-lg border border-slate-700 overflow-hidden">
                {/* Table Header - Hidden on mobile */}
                <div className="hidden md:grid grid-cols-[64px_1fr_100px_100px_280px] gap-4 px-4 py-3 text-xs font-semibold text-gray-400 bg-slate-800/50 border-b border-slate-700">
                  <span className="text-center">#</span>
                  <span>Project</span>
                  <span className="text-center">AI Score</span>
                  <span className="text-center">Human Score</span>
                  <span className="text-center">Vote Instructions</span>
                </div>

                {/* Table Rows */}
                <div className="divide-y divide-slate-700">
                  {leaderboardEntries.map((entry, index) => {
                    const rank = index + 1
                    return (
                      <div
                        key={entry.submission_id}
                        className="grid grid-cols-1 md:grid-cols-[64px_1fr_100px_100px_280px] gap-4 hover:bg-slate-700/30 transition-colors cursor-pointer"
                        onClick={() => setSelectedSubmission(entry)}
                      >
                        {/* Mobile: Card-style layout */}
                        <div className="md:hidden p-4 space-y-4">
                          {/* Header with rank, avatar, project info */}
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0">
                              {getRankBadge(rank)}
                            </div>
                            <a
                              href={`/profile?user=${encodeURIComponent(entry.discord_username || 'user')}`}
                              onClick={(e) => { e.stopPropagation() }}
                            >
                              <img 
                                src={entry.discord_avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(entry.discord_username || 'User')}&size=40&background=6366f1&color=ffffff`}
                                className="h-10 w-10 rounded-full object-cover flex-shrink-0"
                                alt="Profile"
                              />
                            </a>
                            <div className="flex-1 min-w-0">
                              <h3 className="font-semibold text-white text-base leading-tight mb-1">
                                {entry.project_name}
                              </h3>
                              <p className="text-sm text-slate-300 mb-1">{entry.category}</p>
                              <p className="text-xs text-slate-400">
                                <a
                                  href={`/profile?user=${encodeURIComponent(entry.discord_username || 'user')}`}
                                  onClick={(e) => { e.stopPropagation() }}
                                  className="hover:underline"
                                >
                                  @{entry.discord_username || 'Unknown'}
                                </a>
                              </p>
                            </div>
                          </div>

                          {/* Scores Row */}
                          <div className="flex items-center justify-center gap-6 py-2">
                            <div className="text-center">
                              <div className="text-xl font-bold text-white mb-1">
                                {entry.final_score?.toFixed(1) || '—'}
                              </div>
                              <div className="text-xs text-slate-400 uppercase tracking-wide font-medium">AI Score</div>
                            </div>
                            <div className="w-px h-8 bg-slate-600"></div>
                            <div className="text-center">
                              <div className="text-xl font-bold text-white mb-1">
                                {entry.community_score?.toFixed(1) || '—'}
                              </div>
                              <div className="text-xs text-slate-400 uppercase tracking-wide font-medium">Community</div>
                            </div>
                          </div>

                          {/* Vote Button */}
                          <button
                            className="w-full bg-slate-800 hover:bg-slate-700 border border-slate-600 hover:border-indigo-400 rounded-lg p-3 transition-all duration-200 active:scale-[0.98]"
                            onClick={(e) => {
                              e.stopPropagation()
                              setVotingSubmission(entry)
                            }}
                          >
                            <div className="text-sm text-center space-y-1">
                              <div className="text-slate-200">
                                Send <span className="font-semibold text-indigo-400">ai16z</span> to vote
                              </div>
                              <div className="flex items-center justify-center gap-2 text-xs text-slate-300">
                                <span>Memo:</span>
                                <kbd className="px-2 py-1 bg-slate-700 rounded font-mono text-indigo-300 font-semibold">
                                  {entry.submission_id}
                                </kbd>
                              </div>
                            </div>
                          </button>
                        </div>

                        {/* Desktop: Table layout */}
                        <div className="hidden md:flex items-center justify-center px-4 py-4">
                          {getRankBadge(rank)}
                        </div>

                        <div className="hidden md:flex items-center gap-3 min-w-0 px-4 py-4">
                          <a
                            href={`/profile?user=${encodeURIComponent(entry.discord_username || 'user')}`}
                            onClick={(e) => { e.stopPropagation() }}
                          >
                            <img 
                              src={entry.discord_avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(entry.discord_username || 'User')}&size=40&background=6366f1&color=ffffff`}
                              className="h-10 w-10 rounded-full object-cover flex-shrink-0"
                              alt="Profile"
                            />
                          </a>
                          <div className="min-w-0">
                            <h3 className="font-medium truncate text-white">{entry.project_name}</h3>
                            <p className="text-sm text-gray-400 truncate">{entry.category}</p>
                          </div>
                        </div>

                        <div className="hidden md:flex items-center justify-center px-4 py-4">
                          <div className="text-center">
                            <div className="text-lg font-semibold text-white">
                              {entry.final_score?.toFixed(1) || '—'}
                            </div>
                          </div>
                        </div>

                        <div className="hidden md:flex items-center justify-center px-4 py-4">
                          <div className="text-center">
                            <div className="text-lg font-semibold text-white">
                              {entry.community_score?.toFixed(1) || '—'}
                            </div>
                          </div>
                        </div>

                        <div 
                          className="hidden md:flex items-center justify-center cursor-pointer hover:bg-slate-700/20 transition-colors"
                          onClick={(e) => {
                            e.stopPropagation()
                            setVotingSubmission(entry)
                          }}
                        >
                          <div className="text-xs bg-slate-800/50 hover:bg-slate-700/50 transition-colors w-full h-full flex items-center justify-center border-l border-slate-700">
                            <div className="flex items-center gap-1 flex-wrap justify-center">
                              <span>Send</span>
                              <span className="font-semibold text-indigo-400">ai16z</span>
                              <span>→</span>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleCopyVotingWallet()
                                }}
                                className="font-mono text-indigo-400 hover:text-indigo-300 underline decoration-dotted"
                              >
                                {VOTING_WALLET.slice(0, 6)}…{VOTING_WALLET.slice(-6)}
                              </button>
                              <span>with Memo</span>
                              <kbd className="bg-slate-700 rounded font-mono px-1 py-0.5">{entry.submission_id}</kbd>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
                
                {/* View All Link - subtle, right-aligned */}
                <div className="border-t border-slate-700 px-4 py-2 text-right">
                  <a 
                    href="/dashboard" 
                    className="text-xs text-slate-400 hover:text-indigo-400 transition-colors"
                  >
                    View all →
                  </a>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Latest Episodes Section */}
      <section className="bg-gradient-to-b from-slate-800 via-slate-50 to-white dark:from-slate-800 dark:via-slate-900 dark:to-slate-950 py-12 animate-fade-in">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8 text-center">Latest Episodes</h2>
          
          {/* Episodes Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {latestEpisodes
              .slice((currentPage - 1) * episodesPerPage, currentPage * episodesPerPage)
              .map((ep) => (
              <div
                key={ep.id}
                onClick={() => setOpenVideo(ep.id)}
                className="group rounded-xl overflow-hidden shadow-lg bg-slate-50 dark:bg-gray-800 hover:shadow-2xl transition-all duration-200 border border-gray-200 dark:border-gray-700 cursor-pointer"
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
                  {/* Play button overlay */}
                  <div className="absolute inset-0 bg-black/20 group-hover:bg-black/30 transition-colors duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100">
                    <PlayCircle className="h-16 w-16 text-white drop-shadow-lg" />
                  </div>
                </div>
                <div className="p-4">
                  <div className="font-semibold text-base text-gray-900 dark:text-gray-100 mb-1 line-clamp-2 min-h-[2.5em]">{ep.title}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">{ep.view_count} views</div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {Math.ceil(latestEpisodes.length / episodesPerPage) > 1 && (
            <div className="flex justify-center items-center gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 rounded bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Prev
              </button>
              
              {Array.from({ length: Math.ceil(latestEpisodes.length / episodesPerPage) }).map((_, index) => (
                <button
                  key={index + 1}
                  onClick={() => setCurrentPage(index + 1)}
                  className={`px-3 py-1 rounded font-semibold transition-colors ${
                    currentPage === index + 1
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  {index + 1}
                </button>
              ))}
              
              <button
                onClick={() => setCurrentPage(prev => Math.min(Math.ceil(latestEpisodes.length / episodesPerPage), prev + 1))}
                disabled={currentPage === Math.ceil(latestEpisodes.length / episodesPerPage)}
                className="px-3 py-1 rounded bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Lightbox Video Player */}
      {openVideo && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80"
          onClick={() => setOpenVideo(null)}
          onTouchStart={handleLightboxTouchStart}
          onTouchMove={handleLightboxTouchMove}
          onTouchEnd={handleLightboxTouchEnd}
        >
          {/* Navigation Arrows */}
          {getCurrentVideoIndex() > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                goToPreviousVideo();
              }}
              className="absolute left-2 md:left-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 hover:bg-opacity-70 text-white p-2 md:p-3 rounded-full transition-all duration-200 z-10"
              aria-label="Previous video"
            >
              <ChevronLeft className="w-5 h-5 md:w-6 md:h-6" />
            </button>
          )}
          
          {getCurrentVideoIndex() < latestEpisodes.length - 1 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                goToNextVideo();
              }}
              className="absolute right-2 md:right-4 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 hover:bg-opacity-70 text-white p-2 md:p-3 rounded-full transition-all duration-200 z-10"
              aria-label="Next video"
            >
              <ChevronRight className="w-5 h-5 md:w-6 md:h-6" />
            </button>
          )}

          <div
            className="relative w-full max-w-3xl mx-2 md:mx-0"
            onClick={e => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={() => setOpenVideo(null)}
              className="absolute top-2 right-2 text-white text-2xl z-10 bg-black bg-opacity-50 rounded-full w-10 h-10 flex items-center justify-center hover:bg-opacity-80 transition"
              aria-label="Close"
            >
              ×
            </button>

            {/* Video Counter */}
            <div className="absolute top-2 left-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded z-10">
              {getCurrentVideoIndex() + 1} of {latestEpisodes.length}
            </div>

            {/* Video Container */}
            <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden">
              <iframe
                src={`https://www.youtube.com/embed/${openVideo}?autoplay=1&rel=0&modestbranding=1`}
                title="Clank Tank Video"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
                className="w-full h-full"
              />
            </div>

            {/* Video Title */}
            {(() => {
              const currentEpisode = latestEpisodes.find(ep => ep.id === openVideo);
              return currentEpisode ? (
                <div className="mt-4 text-center">
                  <h3 className="text-white text-lg font-semibold mb-2">{currentEpisode.title}</h3>
                  <div className="text-gray-300 text-sm flex items-center justify-center gap-4">
                    <span>{currentEpisode.view_count} views</span>
                    <span>{Math.floor(currentEpisode.duration / 60)}:{(currentEpisode.duration % 60).toString().padStart(2, '0')}</span>
                  </div>
                </div>
              ) : null;
            })()}

            {/* Keyboard Navigation Hint */}
            <div className="hidden md:block absolute -bottom-12 left-1/2 transform -translate-x-1/2 text-gray-400 text-xs text-center">
              <div className="flex items-center gap-2">
                <kbd className="px-2 py-1 bg-gray-800 rounded border text-xs">←</kbd>
                <span>Previous</span>
                <kbd className="px-2 py-1 bg-gray-800 rounded border text-xs">→</kbd>
                <span>Next</span>
                <kbd className="px-2 py-1 bg-gray-800 rounded border text-xs">ESC</kbd>
                <span>Close</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* How it Works Section */}
      <section id="how-it-works" className="bg-gradient-to-br from-indigo-50 via-blue-50 to-cyan-50 dark:from-slate-900 dark:via-indigo-950 dark:to-blue-950 animate-fade-in">
        <div className="max-w-5xl mx-auto py-16 px-4">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 text-center md:text-left">How the Hackathon Works</h2>
            {/* Pill badge legend */}
            <div className="flex gap-2 items-center text-sm">
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-100 font-semibold">● You</span>
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-100 font-semibold">● Automated</span>
            </div>
          </div>
          
          {/* Round 1 */}
          <div className="mb-12">
            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-6 text-center">Round 1</h3>
            <div className="relative">
              <div className="absolute inset-x-0 top-1/2 h-0.5 border-t border-dashed border-muted/40 z-0" />
              <div className="relative grid grid-cols-1 md:grid-cols-2 gap-8 z-10">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-blue-50 dark:bg-blue-900 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-blue-200/80 text-blue-700">1</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[0].icon, { strokeWidth: 2, className: `h-10 w-10 text-blue-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 mt-2">{howItWorks[0].title}</h3>
                  <p className="text-base text-gray-700 dark:text-gray-300 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[0].desc}</p>
                </div>
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-emerald-50 dark:bg-emerald-900 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-200/80 text-emerald-700">2</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[1].icon, { strokeWidth: 2, className: `h-10 w-10 text-emerald-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 mt-2">{howItWorks[1].title}</h3>
                  <p className="text-base text-gray-700 dark:text-gray-300 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[1].desc}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Round 2 */}
          <div>
            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-6 text-center">Round 2</h3>
            <div className="relative">
              <div className="absolute inset-x-0 top-1/2 h-0.5 border-t border-dashed border-muted/40 z-0" />
              <div className="relative grid grid-cols-1 md:grid-cols-2 gap-8 z-10">
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-blue-50 dark:bg-blue-900 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-blue-200/80 text-blue-700">3</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[2].icon, { strokeWidth: 2, className: `h-10 w-10 text-blue-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 mt-2">{howItWorks[2].title}</h3>
                  <p className="text-base text-gray-700 dark:text-gray-300 leading-relaxed max-w-[18ch] mx-auto font-medium">
                    The community votes on-chain with memos
                  </p>
                </div>
                <div className="relative flex flex-col items-center text-center p-6 h-48 md:h-56 bg-emerald-50 dark:bg-emerald-900 rounded-xl shadow-sm justify-center gap-3 hover:-translate-y-1 hover:shadow-lg transition">
                  <div className="absolute left-3 top-3 w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-200/80 text-emerald-700">4</div>
                  <div className="mb-2 flex items-center justify-center">{React.cloneElement(howItWorks[3].icon, { strokeWidth: 2, className: `h-10 w-10 text-emerald-600` })}</div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 mt-2">{howItWorks[3].title}</h3>
                  <p className="text-base text-gray-700 dark:text-gray-300 leading-relaxed max-w-[18ch] mx-auto font-medium">{howItWorks[3].desc}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Judges Panel */}
      <section className="bg-gradient-to-b from-slate-50 via-gray-50 to-slate-100 dark:from-slate-900 dark:via-slate-850 dark:to-slate-800 animate-fade-in relative">
        {/* Very subtle accent */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.03),transparent_60%)] dark:bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.02),transparent_60%)]"></div>
        <div className="max-w-4xl mx-auto py-12 px-4 relative z-10">
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



      {/* FAQ Section */}
      <section className="bg-gradient-to-t from-slate-100 via-gray-50 to-white dark:from-slate-800 dark:via-slate-900 dark:to-slate-950 animate-fade-in">
        <div className="max-w-3xl mx-auto py-16 px-4 pb-24">
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

      {/* Submission Detail Modal */}
      {selectedSubmission && (
        <SubmissionModal
          submissionId={selectedSubmission.submission_id}
          onClose={() => setSelectedSubmission(null)}
          allSubmissionIds={leaderboardEntries.map(e => e.submission_id)}
        />
      )}

      {/* Vote Modal */}
      {votingSubmission && (
        <VoteModal
          submission={votingSubmission}
          onClose={() => setVotingSubmission(null)}
        />
      )}

    </div>
  );
}