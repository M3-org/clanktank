import { useEffect, useState, useCallback } from 'react'
import { useParams, Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { SubmissionDetail as SubmissionDetailType } from '../types'
import { formatDate } from '../lib/utils'
import { Card, CardHeader, CardContent } from '../components/Card'
import { Button } from '../components/Button'
import { Markdown } from '../components/Markdown'
import { useAuth } from '../contexts/AuthContext'
import { LikeDislike } from '../components/LikeDislike'
import { DiscordAvatar } from '../components/DiscordAvatar'
import { useCopyToClipboard } from '../hooks/useCopyToClipboard'
import { 
  ArrowLeft, 
  Github, 
  Video, 
  RefreshCw,
  Star,
  Code,
  TrendingUp,
  Users,
  Calendar,
  Hash,
  Heart,
  
  Edit3,
  ChevronDown,
  ChevronRight,
  FileText,
  Copy,
} from 'lucide-react'

const solanaLogo = (
  <img
    src="https://solana.com/src/img/branding/solanaLogoMark.svg"
    alt="Solana Logo"
    className="inline-block w-4 h-4 mr-2 align-middle"
    style={{ verticalAlign: 'middle' }}
  />
)

function truncateSolanaAddress(address: string) {
  if (!address || address.length <= 12) return address;
  return `${address.slice(0, 5)}...${address.slice(-5)}`;
}

export default function SubmissionDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const { authState } = useAuth()
  
  // Check if displayed in modal
  const isModal = searchParams.get('modal') === 'true'
  const [submission, setSubmission] = useState<SubmissionDetailType | null>(null)
  const [, setFeedback] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [discordData, setDiscordData] = useState<{discord_id?: string, discord_avatar?: string} | null>(null)
  // Per-category reasoning expansion (collapsed by default)
  const [expandedReason, setExpandedReason] = useState<Record<string, boolean>>({})
  const [showJudgeScores, setShowJudgeScores] = useState<boolean>(true)
  const isResearchTab = searchParams.get('tab') === 'research'
  const [expandedJudges, setExpandedJudges] = useState<Record<string, boolean>>({})
  const { copied, copyToClipboard } = useCopyToClipboard()

  // Check if user is authenticated
  const isAuthenticated = authState.authMethod === 'discord' || authState.authMethod === 'invite'

  // Toggle expanded sections
  // No-op: reasoning expansion removed for compact mode

  // Handle back navigation
  const handleBack = () => {
    // If the user came from the dashboard (has state or referrer), go back
    if (location.state?.from === 'dashboard' || document.referrer.includes('/dashboard')) {
      navigate(-1)
    } else {
      // Otherwise go to dashboard
      navigate('/dashboard')
    }
  }

  const loadDiscordDataAsync = useCallback(async () => {
    if (!id) return null
    // Only get Discord data from cache or skip it; detail already contains user info
    return null
  }, [id])

  const loadAllData = useCallback(async () => {
    if (!id) return
    
    try {
      // Make all API calls in parallel instead of sequential
      const [submissionData, feedbackData, discordDataResult] = await Promise.allSettled([
        hackathonApi.getSubmission(id),
        hackathonApi.getSubmissionFeedback(id),
        loadDiscordDataAsync()
      ])
      
      // Handle submission data
      if (submissionData.status === 'fulfilled') {
        setSubmission(submissionData.value)
      } else {
        console.error('Failed to load submission:', submissionData.reason)
      }
      
      // Handle feedback data
      if (feedbackData.status === 'fulfilled' && feedbackData.value) {
        setFeedback(feedbackData.value)
      }
      
      // Handle discord data
      if (discordDataResult.status === 'fulfilled') {
        setDiscordData(discordDataResult.value)
      }
      
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }, [id, loadDiscordDataAsync])

  useEffect(() => {
    if (id) {
      // Load all data in parallel to avoid blocking the UI
      loadAllData()
    }
  }, [id, loadAllData])

  

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (!submission) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="max-w-lg mx-auto mt-16">
          <CardContent className="text-center py-12">
            <div className="rounded-full bg-gray-100 h-16 w-16 flex items-center justify-center mx-auto mb-4">
              <Code className="h-8 w-8 text-gray-400" />
            </div>
            <p className="text-gray-500 mb-6">Submission not found</p>
            {!isModal && (
              <Button variant="secondary" size="sm" onClick={handleBack}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  // Only compute these after submission is loaded

  const scoreIcons = {
    innovation: Star,
    technical_execution: Code,
    market_potential: TrendingUp,
    user_experience: Users
  }

  // Add mapping for judge avatars
  const judgeAvatarMap: Record<string, string> = {
    'eliza': '/avatars/eliza.png',
    'aimarc': '/avatars/aimarc.png',
    'aishaw': '/avatars/aishaw.png',
    'spartan': '/avatars/spartan.png',
    'peepo': '/avatars/peepo.png',
  }

  // Normalize various judge name strings to avatar keys
  function normalizeJudgeKey(name: string): string {
    const n = name.trim().toLowerCase()
    // broad contains checks to handle variations (e.g., "Marc (AI)")
    if (n.includes('marc')) return 'aimarc'
    if (n.includes('shaw')) return 'aishaw'
    if (n.includes('spartan')) return 'spartan'
    if (n.includes('peepo')) return 'peepo'
    if (n.includes('eliza')) return 'eliza'
    return n
  }

  function getJudgeAvatar(name: string): string {
    const key = normalizeJudgeKey(name)
    return judgeAvatarMap[key] || judgeAvatarMap['eliza']
  }

  // Add mapping for judge specialties (matching Frontpage.tsx)
  const judgeSpecialtyMap: Record<string, string> = {
    'aimarc': 'ROI skeptic',
    'aishaw': 'Code purist', 
    'peepo': 'UX meme lord',
    'spartan': 'DeFi maximalist',
    'eliza': 'AI Judge', // fallback for eliza or unknown judges
  }

  // Parse technical assessment data
  const getTechnicalAssessment = () => {
    if (!submission?.research?.technical_assessment) return null
    try {
      return typeof submission.research.technical_assessment === 'string' 
        ? JSON.parse(submission.research.technical_assessment)
        : submission.research.technical_assessment
    } catch (e) {
      return null
    }
  }

  // Removed overall summary extraction since summary preview was dropped

  // Convert research data to clean markdown
  const convertToMarkdown = (data: any, depth = 0): string => {
    if (!data) return ''
    
    let markdown = ''
    
    if (typeof data === 'string') {
      return data
    }
    
    if (typeof data === 'number' || typeof data === 'boolean') {
      return data.toString()
    }
    
    if (Array.isArray(data)) {
      if (data.length === 0) return 'None'
      return data.map(item => `- ${convertToMarkdown(item, depth)}`).join('\n')
    }
    
    if (typeof data === 'object') {
      for (const [key, value] of Object.entries(data)) {
        // Skip empty values
        if (value === null || value === undefined || value === '') continue
        
        const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
        
        if (typeof value === 'object' && !Array.isArray(value) && value !== null) {
          // Only use headers for top-level sections
          if (depth === 0) {
            markdown += `## ${formattedKey}\n\n`
          } else {
            markdown += `**${formattedKey}:**\n\n`
          }
          markdown += `${convertToMarkdown(value, depth + 1)}\n\n`
        } else if (Array.isArray(value)) {
          markdown += `**${formattedKey}:**\n`
          markdown += `${convertToMarkdown(value, depth + 1)}\n\n`
        } else {
          markdown += `**${formattedKey}:** ${convertToMarkdown(value, depth)}\n\n`
        }
      }
    }
    
    return markdown.trim() || 'No data available'
  }






  return (
    <div className="max-w-7xl mx-auto px-0 sm:px-0 lg:px-0 py-8">
      {/* Hero Banner - full width, overlayed info */}
      <div className="relative w-full h-72 md:h-96 mb-8 overflow-hidden">
        {/* Background: image/video or gray placeholder */}
        {submission.project_image ? (
          <img
            src={submission.project_image}
            alt={submission.project_name + ' project image'}
            className="absolute inset-0 w-full h-full object-cover"
            style={{ zIndex: 1 }}
          />
        ) : (
          <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gray-100 dark:bg-gray-800">
            <span className="text-gray-400 dark:text-gray-500 text-lg">No project image</span>
          </div>
        )}
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" style={{ zIndex: 2 }} />
        {/* Overlayed content: only title and team name, bottom left with margin */}
        <div className="absolute left-0 bottom-0 p-8 z-10 flex flex-col gap-2 w-auto">
          <h1 className="text-2xl md:text-4xl font-bold text-white drop-shadow mb-1">{submission.project_name}</h1>
          <div className="flex items-center gap-3">
            <p className="text-lg text-white/80">by</p>
            <Link
              to={`/p/${encodeURIComponent(submission.discord_username || submission.discord_handle || 'user')}${searchParams.get('modal') === 'true' ? '?modal=true' : ''}`}
              className="text-lg font-semibold text-white hover:underline"
            >
              {submission.discord_username || submission.discord_handle}
            </Link>
            <Link
              to={`/p/${encodeURIComponent(submission.discord_username || submission.discord_handle || 'user')}${searchParams.get('modal') === 'true' ? '?modal=true' : ''}`}
              className="inline-flex"
            >
            <DiscordAvatar 
              discord_id={discordData?.discord_id || submission.discord_id}
              discord_avatar={discordData?.discord_avatar || submission.discord_avatar}
                discord_handle={submission.discord_username || submission.discord_handle}
              size="md"
              variant="dark"
            />
            </Link>
          </div>
        </div>
      </div>

      {/* The rest of the page content follows here, in normal flow */}
      {/* Action Buttons - Hide back button in modal */}
      {!isModal && (
        <div className="flex justify-between items-center mb-6 px-4 sm:px-6 lg:px-8">
          <Button variant="ghost" size="sm" className="dark:text-gray-200 dark:hover:text-white" onClick={handleBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
        
          {submission?.can_edit && isAuthenticated && (
            <Link to={`/submission/${id}/edit`}>
              <Button variant="secondary" size="sm">
                <Edit3 className="h-4 w-4 mr-2" />
                Edit Submission
              </Button>
            </Link>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 px-4 sm:px-6 lg:px-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
            <CardHeader>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Description</h2>
            </CardHeader>
            <CardContent>
              <Markdown className="prose prose-sm dark:prose-invert max-w-none" content={submission.description} />
            </CardContent>
          </Card>

          {/* Details */}
          <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
            <CardHeader>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Project Details</h2>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {submission.problem_solved && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    Problem Solved
                  </h3>
                  <Markdown className="prose prose-sm dark:prose-invert max-w-none ml-5" content={submission.problem_solved} />
                </div>
              )}
              
              {submission.favorite_part && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    Favorite Part
                  </h3>
                  <Markdown className="prose prose-sm dark:prose-invert max-w-none ml-5" content={submission.favorite_part} />
                </div>
              )}
              
            </CardContent>
          </Card>

          {/* Research moved to sidebar below Judge Scores */}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Information */}
          <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
            <CardHeader>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Information</h3>
                <button
                  onClick={() => copyToClipboard(JSON.stringify(submission, null, 2))}
                  className="inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                  title="Copy full submission data"
                >
                  <Copy className="h-3 w-3" />
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </CardHeader>
            <CardContent>
              <dl className="space-y-4">
                <div className="flex items-center justify-between">
                  <dt className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <Hash className="h-4 w-4 mr-2" />
                    Submission ID
                  </dt>
                  <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">{submission.submission_id}</dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <Calendar className="h-4 w-4 mr-2" />
                    Created
                  </dt>
                  <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {formatDate(submission.created_at)}
                  </dd>
                </div>
                {submission.github_url && (
                  <div className="flex items-center justify-between">
                    <dt className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                      <Github className="h-4 w-4 mr-2" />
                      GitHub
                    </dt>
                    <dd className="text-sm font-medium text-indigo-700 dark:text-indigo-400 truncate max-w-[160px]">
                      <a href={submission.github_url} target="_blank" rel="noopener noreferrer" className="underline hover:text-indigo-900 dark:hover:text-indigo-200">Repo ↗</a>
                    </dd>
                  </div>
                )}
                {submission.demo_video_url && (
                  <div className="flex items-center justify-between">
                    <dt className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                      <Video className="h-4 w-4 mr-2" />
                      Demo Video
                    </dt>
                    <dd className="text-sm font-medium text-indigo-700 dark:text-indigo-400 truncate max-w-[160px]">
                      <a href={submission.demo_video_url} target="_blank" rel="noopener noreferrer" className="underline hover:text-indigo-900 dark:hover:text-indigo-200">Watch ↗</a>
                    </dd>
                  </div>
                )}
                {submission.solana_address && (
                  <div className="flex items-center justify-between">
                    <dt className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                      {solanaLogo}
                      <span className="ml-2">Solana Address</span>
                    </dt>
                    <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      <button
                        onClick={() => copyToClipboard(submission.solana_address || '')}
                        className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                        title="Copy Solana address"
                      >
                        {truncateSolanaAddress(submission.solana_address)}
                      </button>
                    </dd>
                  </div>
                )}
                {submission.discord_id && (
                  <div className="flex items-center justify-between">
                    <dt className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                      <Users className="h-4 w-4 mr-2" />
                      Discord
                    </dt>
                    <dd className="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center gap-2">
                      {discordData?.discord_avatar && (
                        <DiscordAvatar 
                          discord_id={submission.discord_id} 
                          discord_avatar={discordData.discord_avatar}
                          size="sm"
                        />
                      )}
                      {submission.discord_id}
                    </dd>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <dt className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <Heart className="h-4 w-4 mr-2" />
                    Likes
                  </dt>
                  <dd className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {0}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {/* Judge Scores (clickable header, collapsed by default) */}
          {submission.scores && submission.scores.length > 0 && (
            <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
              <CardHeader>
                <button
                  type="button"
                  onClick={() => setShowJudgeScores(s => !s)}
                  className="w-full flex items-center justify-between px-2 py-1 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <span className="text-xl font-semibold text-gray-900 dark:text-gray-100">Judge Scores</span>
                  <span className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                    <span className="text-xs hidden sm:inline">{submission.scores.length}</span>
                    {showJudgeScores ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  </span>
                </button>
              </CardHeader>
              {showJudgeScores && (
              <CardContent>
                {/* Compact summary: 4-up mini-cards; avatar on top, big R1 score full row underneath */}
                <div className="mb-4 grid grid-cols-4 gap-3">
                  {Array.from(new Set((submission.scores || []).map(s => normalizeJudgeKey(s.judge_name)))).map((judgeKey) => {
                    const round1 = (submission.scores || []).find(s => s.judge_name && s.round === 1 && s.judge_name.trim().toLowerCase() === judgeKey)
                    const round2 = (submission.scores || []).find(s => s.judge_name && s.round === 2 && s.judge_name.trim().toLowerCase() === judgeKey)
                    const judgeName = round1?.judge_name || round2?.judge_name || judgeKey
                    const avatarSrc = getJudgeAvatar(judgeName)
                    const r1 = round1 ? (round1.weighted_total / 4).toFixed(1) : null
                    // const r2 = round2 ? (round2.weighted_total / 4).toFixed(1) : null // reserved for future display
                    const colorFor = (val: number) => val >= 8 ? 'bg-emerald-500' : val >= 6 ? 'bg-amber-500' : val >= 4 ? 'bg-orange-500' : 'bg-red-500'
                    return (
                      <button
                        key={judgeKey}
                        type="button"
                        onClick={() => {
                          setExpandedJudges(prev => ({ ...prev, [judgeKey]: !prev[judgeKey] }))
                          setShowJudgeScores(true)
                        }}
                        className="group rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-center w-full"
                        aria-label={`Toggle details for ${judgeName}`}
                      >
                        <img
                          src={avatarSrc}
                          alt=""
                          className="h-12 w-12 rounded-full border border-gray-200 dark:border-gray-700 object-cover mx-auto transition-transform group-hover:scale-105"
                          width="48"
                          height="48"
                          loading="lazy"
                        />
                        <div className="mt-2">
                          {r1 ? (
                            <div
                              className={`w-full rounded-md px-2 py-1 text-lg font-extrabold text-white ${colorFor(parseFloat(r1))}`}
                              title="Round 1 score"
                            >
                              {r1}
                            </div>
                          ) : (
                            <div className="w-full rounded-md px-2 py-1 text-xs text-gray-400 bg-gray-100 dark:bg-gray-800">
                              —
                            </div>
                          )}
                        </div>
                      </button>
                    )
                  })}
                </div>

                {/* Expanded judge details (render only for expanded judges) */}
                <div className="space-y-8">
                  {Array.from(new Set((submission.scores || []).map(s => normalizeJudgeKey(s.judge_name))))
                    .filter(judgeKey => !!expandedJudges[judgeKey])
                    .map((judgeKey, index) => {
                    const round1 = (submission.scores || []).find(s => s.judge_name && s.round === 1 && s.judge_name.trim().toLowerCase() === judgeKey)
                    const round2 = (submission.scores || []).find(s => s.judge_name && s.round === 2 && s.judge_name.trim().toLowerCase() === judgeKey)
                    // Keep computations local to preview; detailed sections compute again where needed
                    const judgeName = round1?.judge_name || round2?.judge_name || judgeKey
                    const avatarSrc = getJudgeAvatar(judgeName)
                                    return (
                      <div key={judgeName}>
                        {index > 0 && <div className="border-t border-gray-200 dark:border-gray-700 mb-8"></div>}
                        <div className="pb-2">
                        {/* Judge header (visible only in expanded view) */}
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <img
                              src={avatarSrc}
                              alt={judgeName + ' avatar'}
                              className="h-8 w-8 rounded-full border border-gray-200 dark:border-gray-700 object-cover bg-white dark:bg-gray-800"
                              style={{ minWidth: 32, minHeight: 32 }}
                              width="32"
                              height="32"
                              loading="lazy"
                            />
                            <div>
                              <h4 className="font-medium text-gray-900 dark:text-gray-100 capitalize">
                                {judgeName.replace('ai', 'AI ')}
                              </h4>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {judgeSpecialtyMap[judgeKey] || 'AI Judge'}
                              </p>
                            </div>
                          </div>
                              <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => setExpandedJudges(prev => ({ ...prev, [judgeKey]: false }))}
                              className="text-xs px-2 py-1 rounded border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                            >
                              Close
                            </button>
                          </div>
                        </div>
                        {/* Metrics + comments grid */}
                        <div className="flex flex-col gap-6">
                          {/* Round 1 */}
                          <div>
                            <div className="mb-2 flex items-center gap-2">
                              <span className="inline-block h-2 w-2 rounded-full bg-indigo-500"></span>
                              <span className="text-xs font-semibold text-indigo-700 dark:text-indigo-400">Round 1</span>
                            </div>
                            {round1 ? (
                              <>
                                {round1.notes?.overall_comment && (
                                <div className="mb-3 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded border-l-4 border-indigo-300 dark:border-indigo-600">
                                  <p className="text-sm text-indigo-900 dark:text-indigo-100 leading-relaxed italic">"{round1.notes.overall_comment}"</p>
                                  </div>
                                )}
                                <div className="space-y-2">
                                  {[
                                    ['innovation', round1.innovation, 'Innovation'],
                                    ['technical_execution', round1.technical_execution, 'Technical Execution'],
                                    ['market_potential', round1.market_potential, 'Market Potential'],
                                    ['user_experience', round1.user_experience, 'User Experience'],
                                  ].map(([key, value, displayName]) => {
                                    const Icon = scoreIcons[key as keyof typeof scoreIcons]
                                    const numValue = value as number
                                    const percentage = (numValue / 10) * 100
                                const getReasoningKey = (k: string) => {
                                  switch (k) {
                                        case 'technical_execution': return 'technical'
                                        case 'market_potential': return 'market'
                                        case 'user_experience': return 'experience'
                                    default: return k
                                      }
                                    }
                                    const reasoningKey = `${getReasoningKey(key as string)}_reasoning`
                                    const reasoningText = (round1.notes as any)?.[reasoningKey] as string || 
                                                         (round1.notes?.reasons as any)?.[getReasoningKey(key as string)] as string
                                    const hasReasoning = Boolean(reasoningText)
                                const sectionKey = `${judgeName}-${key}-reasoning`
                                    return (
                                      <div key={key as string}>
                                        <button
                                      type="button"
                                          onClick={(e) => {
                                            e.preventDefault()
                                            e.stopPropagation()
                                            if (hasReasoning) {
                                          setExpandedReason(prev => ({ ...prev, [sectionKey]: !prev[sectionKey] }))
                                            }
                                          }}
                                      className={`w-full grid grid-cols-[1fr_auto_auto] items-center gap-3 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors ${hasReasoning ? 'cursor-pointer' : 'cursor-default'}`}
                                          disabled={!hasReasoning}
                                        >
                                          <div className="flex items-center gap-2 min-w-0">
                                            <Icon className={`h-4 w-4 flex-shrink-0 ${
                                              numValue >= 8 ? 'text-emerald-600 dark:text-emerald-400' :
                                              numValue >= 6 ? 'text-amber-600 dark:text-amber-400' :
                                              numValue >= 4 ? 'text-orange-600 dark:text-orange-400' :
                                              'text-red-600 dark:text-red-400'
                                            }`} />
                                            <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                              {displayName as string}
                                            </span>
                                          </div>
                                      <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                            <div 
                                              className={`h-full rounded-full transition-all duration-500 ${
                                                numValue >= 8 ? 'bg-emerald-500' :
                                                numValue >= 6 ? 'bg-amber-500' :
                                                numValue >= 4 ? 'bg-orange-500' :
                                                'bg-red-500'
                                              }`}
                                              style={{ width: `${percentage}%` }}
                                            />
                                          </div>
                                      <span className={`text-sm font-semibold text-right w-10 ${
                                            numValue >= 8 ? 'text-emerald-600 dark:text-emerald-400' :
                                            numValue >= 6 ? 'text-amber-600 dark:text-amber-400' :
                                            numValue >= 4 ? 'text-orange-600 dark:text-orange-400' :
                                            'text-red-600 dark:text-red-400'
                                          }`}>
                                            {numValue}/10
                                          </span>
                                        </button>
                                    {hasReasoning && expandedReason[sectionKey] && (
                                          <div className="ml-6 mt-2 mb-3 p-3 bg-gray-50/50 dark:bg-gray-800/30 rounded border-l-4 border-gray-200 dark:border-gray-600">
                                        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed italic">"{reasoningText}"</p>
                                          </div>
                                        )}
                                      </div>
                                    )
                                  })}
                                </div>
                              </>
                            ) : (
                              <div className="text-xs text-gray-400 dark:text-gray-500 italic">No round 1 data</div>
                            )}
                          </div>
                          {/* Round 2 */}
                          <div>
                            <div className="mb-2 flex items-center gap-2">
                              <span className="inline-block h-2 w-2 rounded-full bg-green-500"></span>
                              <span className="text-xs font-semibold text-green-700 dark:text-green-400">Round 2</span>
                            </div>
                            {round2 ? (
                              <div className="text-sm text-gray-700 dark:text-gray-300">Overall: {(round2.weighted_total / 4).toFixed(1)}/10</div>
                            ) : (
                              <div className="text-xs text-gray-400 dark:text-gray-500 italic">No round 2 data</div>
                            )}
                          </div>
                        </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
              )}
            </Card>
          )}

          {/* Research (clickable header, collapsed by default, below Judge Scores) */}
          {submission.research && (
            <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
              <CardHeader>
                <button
                  type="button"
                  onClick={() => {
                    if (isModal) {
                      navigate(`/submission/${id}/research${isModal ? '?modal=true' : ''}`)
                    } else {
                      setSearchParams(prev => {
                        const next = new URLSearchParams(prev)
                        if (isResearchTab) {
                          next.delete('tab')
                        } else {
                          next.set('tab', 'research')
                        }
                        return next
                      })
                    }
                  }}
                  className="w-full flex items-center justify-between px-2 py-1 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">Research</span>
                  <span className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                    {isResearchTab ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  </span>
                </button>
              </CardHeader>
              {isResearchTab && (
              <CardContent className="px-4 py-3">
                {(() => {
                  const assessment = getTechnicalAssessment()

                  if (!assessment && !submission.research.github_analysis) {
                    return (
                      <p className="text-sm text-gray-500 dark:text-gray-400 italic">No research data available</p>
                    )
                  }

                  const combineAnalysisData = () => {
                      let combinedMarkdown = ''

                      if (submission.research?.github_analysis) {
                                try {
                                  const githubData = typeof submission.research.github_analysis === 'string' 
                                    ? JSON.parse(submission.research.github_analysis)
                                    : submission.research.github_analysis

                          combinedMarkdown += '# Repository Analysis\n\n'

                          if (githubData.description) {
                            combinedMarkdown += `**Description:** ${githubData.description}\n\n`
                          }

                          if (githubData.file_structure) {
                            combinedMarkdown += `**Total Files:** ${githubData.file_structure.total_files || 0}\n\n`

                            if (githubData.file_structure.file_extensions && Object.keys(githubData.file_structure.file_extensions).length > 0) {
                              combinedMarkdown += '**Technologies:**\n'
                              Object.entries(githubData.file_structure.file_extensions)
                                .sort(([,a], [,b]) => (b as number) - (a as number))
                                .slice(0, 5)
                                .forEach(([ext, count]) => {
                                  combinedMarkdown += `- .${ext}: ${count} files\n`
                                })
                              combinedMarkdown += '\n'
                            }

                            const characteristics = [] as string[]
                            if (githubData.file_structure.has_tests) characteristics.push('✅ Has test suite')
                            if (githubData.file_structure.has_docs) characteristics.push('📖 Has documentation')
                            if (githubData.file_structure.is_large_repo) characteristics.push('📦 Large codebase (500+ files)')

                            if (characteristics.length > 0) {
                              combinedMarkdown += '**Project Quality:**\n'
                              characteristics.forEach((char: string) => {
                                combinedMarkdown += `- ${char}\n`
                              })
                              combinedMarkdown += '\n'
                            }
                          }

                          if (githubData.commit_activity) {
                            if (githubData.commit_activity.total_commits) {
                              combinedMarkdown += `**Total Commits:** ${githubData.commit_activity.total_commits}\n\n`
                            }
                            if (githubData.commit_activity.commit_authors && githubData.commit_activity.commit_authors.length > 0) {
                              combinedMarkdown += `**Contributors:** ${githubData.commit_activity.commit_authors.length} developers\n\n`
                            }
                          }

                        } catch (e) {
                          combinedMarkdown += '# Repository Analysis\n\nRepository structure analyzed but details unavailable.\n\n'
                        }
                      }

                      if (assessment) {
                        combinedMarkdown += '# AI Research Analysis\n\n'
                        combinedMarkdown += convertToMarkdown(assessment)
                      }

                      return combinedMarkdown
                    }

                    const fullReport = combineAnalysisData()

                    return (
                      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
                        <div className="flex items-center justify-between mb-6">
                          <h4 className="text-base font-bold text-gray-900 dark:text-gray-100 flex items-center">
                            <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
                            Analysis Report
                          </h4>
                          <button
                            onClick={() => copyToClipboard(fullReport)}
                            className="flex items-center gap-2 px-3 py-2 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 bg-white dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-gray-700 rounded-lg transition-all duration-200 font-medium"
                            title="Copy full analysis report"
                          >
                            <Copy className="h-4 w-4" />
                            {copied ? 'Copied!' : 'Copy'}
                          </button>
                                      </div>
                        <div className="prose prose-sm max-w-none dark:prose-invert break-words overflow-hidden prose-headings:text-gray-900 dark:prose-headings:text-gray-100 prose-headings:font-bold prose-h1:text-xl prose-h1:mb-4 prose-h1:mt-0 prose-h2:text-lg prose-h2:mb-4 prose-h2:mt-6 prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:leading-relaxed prose-strong:text-gray-900 dark:prose-strong:text-gray-100 prose-ul:my-3 prose-li:my-1 prose-code:text-sm prose-pre:bg-gray-100 dark:prose-pre:bg-gray-800 prose-pre:border prose-pre:border-gray-200 dark:prose-pre:border-gray-700 prose-pre:rounded-lg prose-pre:p-4 prose-a:break-all prose-p:break-words prose-li:break-words">
                          <Markdown content={fullReport} />
                                    </div>
                                  </div>
                  )
                })()}
              </CardContent>
              )}
            </Card>
          )}

          {/* Community Feedback */}
          <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
            <CardHeader>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                <Heart className="h-5 w-5 mr-2 text-red-500" />
                Community Feedback
              </h3>
            </CardHeader>
            <CardContent className="p-0">
              <LikeDislike submissionId={submission.submission_id.toString()} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
