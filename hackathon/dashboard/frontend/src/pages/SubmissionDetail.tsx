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
  Quote,
  Edit3,
  ChevronDown,
  ChevronRight,
  Award,
  Target,
  Lightbulb,
  AlertTriangle,
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
  const [searchParams] = useSearchParams()
  const { authState } = useAuth()
  
  // Check if displayed in modal
  const isModal = searchParams.get('modal') === 'true'
  const [submission, setSubmission] = useState<SubmissionDetailType | null>(null)
  const [, setFeedback] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [discordData, setDiscordData] = useState<{discord_id?: string, discord_avatar?: string} | null>(null)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({})

  // Check if user is authenticated
  const isAuthenticated = authState.authMethod === 'discord' || authState.authMethod === 'invite'

  // Toggle expanded sections
  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }))
  }

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

  // Score badge component
  const ScoreBadge = ({ score, maxScore = 10 }: { score: number, maxScore?: number }) => {
    const percentage = (score / maxScore) * 100
    const bgColor = percentage >= 80 ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200' :
                   percentage >= 60 ? 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200' :
                   percentage >= 40 ? 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200' :
                   'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${bgColor}`}>
        {score}/{maxScore}
      </span>
    )
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

          {/* Judge Scores */}
          {submission.scores && submission.scores.length > 0 && (
            <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
              <CardHeader>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Judge Scores</h2>
              </CardHeader>
              <CardContent>
                {/* Judge sections with separators */}
                <div className="space-y-8">
                  {Array.from(new Set((submission.scores || []).map(s => normalizeJudgeKey(s.judge_name))))
                    .map((judgeKey, index) => {
                    const round1 = (submission.scores || []).find(s => s.judge_name && s.round === 1 && s.judge_name.trim().toLowerCase() === judgeKey)
                    const round2 = (submission.scores || []).find(s => s.judge_name && s.round === 2 && s.judge_name.trim().toLowerCase() === judgeKey)
                    
                    // Use weighted totals from backend (respects judge-specific multipliers)
                    const round1Total = round1 ? round1.weighted_total : 0
                    const round2Total = round2 ? round2.weighted_total : 0
                    
                    // Use the original judge name from round1 or round2 for display
                    const judgeName = round1?.judge_name || round2?.judge_name || judgeKey
                    const avatarSrc = getJudgeAvatar(judgeName)
                                    return (
                      <div key={judgeName}>
                        {index > 0 && <div className="border-t border-gray-200 dark:border-gray-700 mb-8"></div>}
                        <div className="pb-2">
                        {/* Judge header */}
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
                          <div className="flex flex-col items-end gap-2">
                            {round1 && (
                              <div className="flex items-center gap-2">
                                <span className={`text-xs font-semibold ${
                                  round1Total >= 32 ? 'text-emerald-600 dark:text-emerald-400' :
                                  round1Total >= 24 ? 'text-amber-600 dark:text-amber-400' :
                                  round1Total >= 16 ? 'text-orange-600 dark:text-orange-400' :
                                  'text-red-600 dark:text-red-400'
                                }`}>R1</span>
                                <div className={`px-3 py-1 rounded-full text-sm font-bold ${
                                  round1Total >= 32 ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200' :
                                  round1Total >= 24 ? 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200' :
                                  round1Total >= 16 ? 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200' :
                                  'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                                }`}>
                                  {(round1Total / 4).toFixed(1)}/10
                                </div>
                              </div>
                            )}
                            {round2 && (
                              <div className="flex items-center gap-2">
                                <span className={`text-xs font-semibold ${
                                  round2Total >= 32 ? 'text-emerald-600 dark:text-emerald-400' :
                                  round2Total >= 24 ? 'text-amber-600 dark:text-amber-400' :
                                  round2Total >= 16 ? 'text-orange-600 dark:text-orange-400' :
                                  'text-red-600 dark:text-red-400'
                                }`}>R2</span>
                                <div className={`px-3 py-1 rounded-full text-sm font-bold ${
                                  round2Total >= 32 ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200' :
                                  round2Total >= 24 ? 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200' :
                                  round2Total >= 16 ? 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200' :
                                  'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                                }`}>
                                  {(round2Total / 4).toFixed(1)}/10
                                </div>
                              </div>
                            )}
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
                                {/* Compact toggle to reveal Round 1 details */}
                                <div className="mt-1 mb-2">
                                  <button
                                    onClick={(e) => {
                                      e.preventDefault();
                                      e.stopPropagation();
                                      const detailsKey = `${judgeName}-r1-details`
                                      setExpandedSections(prev => {
                                        const isOpen = !!prev[detailsKey]
                                        const next: Record<string, boolean> = { ...prev, [detailsKey]: !isOpen }
                                        const catKeys = ['innovation','technical_execution','market_potential','user_experience']
                                          .map(k => `${judgeName}-${k}-reasoning`)
                                        catKeys.forEach(k => { next[k] = !isOpen })
                                        return next
                                      })
                                    }}
                                    className="flex items-center gap-1 text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300"
                                    type="button"
                                  >
                                    {expandedSections[`${judgeName}-r1-details`] ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                                    {expandedSections[`${judgeName}-r1-details`] ? 'Hide detailed analysis' : 'Show detailed analysis'}
                                  </button>
                                </div>

                                {/* Overall Comment (always visible if present) */}
                                {round1.notes?.overall_comment && (
                                  <div className="mb-4 relative">
                                    <div className="absolute left-0 top-0 w-1 h-full bg-gradient-to-b from-indigo-500 to-indigo-400 rounded-full"></div>
                                    <div className="pl-4 py-2 bg-gradient-to-r from-indigo-50/40 to-transparent dark:from-indigo-900/20 dark:to-transparent rounded-r-lg border-l-4 border-indigo-200 dark:border-indigo-700">
                                      <p className="text-sm text-indigo-900 dark:text-indigo-100 leading-relaxed font-medium">
                                        "{round1.notes.overall_comment}"
                                      </p>
                                    </div>
                                  </div>
                                )}

                                {expandedSections[`${judgeName}-r1-details`] && (
                                  <>
                                {/* Combined Category Scores & Detailed Reasoning */}
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
                                    const sectionKey = `${judgeName}-${key}-reasoning`
                                    
                                    const getReasoningKey = (key: string) => {
                                      switch (key) {
                                        case 'technical_execution': return 'technical'
                                        case 'market_potential': return 'market'
                                        case 'user_experience': return 'experience'
                                        default: return key
                                      }
                                    }
                                    
                                    const reasoningKey = `${getReasoningKey(key as string)}_reasoning`
                                    const reasoningText = (round1.notes as any)?.[reasoningKey] as string || 
                                                         (round1.notes?.reasons as any)?.[getReasoningKey(key as string)] as string
                                    const hasReasoning = Boolean(reasoningText)
                                    
                                    return (
                                      <div key={key as string}>
                                        <button
                                          onClick={(e) => {
                                            e.preventDefault()
                                            e.stopPropagation()
                                            if (hasReasoning) {
                                              toggleSection(sectionKey)
                                            }
                                          }}
                                          type="button"
                                          className={`w-full grid grid-cols-[1fr_auto_auto_auto] items-center gap-3 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors ${
                                            hasReasoning ? 'cursor-pointer' : 'cursor-default'
                                          }`}
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
                                          <div className="w-20 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
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
                                          <span className={`text-sm font-semibold text-right w-12 ${
                                            numValue >= 8 ? 'text-emerald-600 dark:text-emerald-400' :
                                            numValue >= 6 ? 'text-amber-600 dark:text-amber-400' :
                                            numValue >= 4 ? 'text-orange-600 dark:text-orange-400' :
                                            'text-red-600 dark:text-red-400'
                                          }`}>
                                            {numValue}/10
                                          </span>
                                          <div className="w-4">
                                            {hasReasoning && (
                                              expandedSections[sectionKey] ? 
                                                <ChevronDown className="h-4 w-4 text-gray-400" /> : 
                                                <ChevronRight className="h-4 w-4 text-gray-400" />
                                            )}
                                          </div>
                                        </button>
                                        
                                        {hasReasoning && expandedSections[sectionKey] && (
                                          <div className="ml-6 mt-2 mb-3 p-3 bg-gray-50/50 dark:bg-gray-800/30 rounded border-l-4 border-gray-200 dark:border-gray-600">
                                            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed italic">
                                              "{reasoningText}"
                                            </p>
                                          </div>
                                        )}
                                      </div>
                                    )
                                  })}
                                </div>
                                
                                  {/* Global reasoning toggle removed in favor of single details toggle */}
                                  </>
                                )}
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
                              <>
                                {round2.notes?.round2_final_verdict ? (
                                  <div className={`mt-2`}> 
                                    <div className={`relative flex items-start w-full rounded-lg p-3 leading-6 italic bg-green-50 dark:bg-green-900 border-l-4 border-green-400 dark:border-green-500`}> 
                                      <Quote className="h-4 w-4 text-gray-400 dark:text-gray-500 opacity-60 absolute left-2 top-2" />
                                      <span className="pl-6 text-gray-900 dark:text-gray-100">"{round2.notes.round2_final_verdict}"</span>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="mt-2 text-xs text-gray-400 dark:text-gray-500 italic">– no final verdict –</div>
                                )}

                                {/* Round 2 details toggle */}
                                {(round2.notes?.round2_reasoning || round2.notes?.score_revision || round2.notes?.community_influence || round2.notes?.confidence) && (
                                  <div className="mt-3">
                                    <button
                                      onClick={() => toggleSection(`${judgeName}-round2-details`)}
                                      className="flex items-center gap-1 text-sm font-medium text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200 transition-colors"
                                      type="button"
                                    >
                                      {expandedSections[`${judgeName}-round2-details`] ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                                      {expandedSections[`${judgeName}-round2-details`] ? 'Hide detailed analysis' : 'Show detailed analysis'}
                                    </button>
                                  </div>
                                )}

                                {expandedSections[`${judgeName}-round2-details`] && (
                                  <div className="mt-2 space-y-2 pl-4 border-l-2 border-green-200 dark:border-green-700">
                                    {round2?.notes?.round2_reasoning && (
                                      <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs">
                                        <div className="font-medium text-green-800 dark:text-green-200 mb-1">
                                          Judge Reasoning
                                        </div>
                                        <div className="text-green-700 dark:text-green-300">
                                              {round2?.notes?.round2_reasoning}
                                        </div>
                                      </div>
                                    )}
                                    
                                    {round2?.notes?.score_revision && typeof round2?.notes?.score_revision === 'object' && (
                                      <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs">
                                        <div className="font-medium text-green-800 dark:text-green-200 mb-1">
                                              Score Revision: {round2?.notes?.score_revision?.type || 'none'}
                                        </div>
                                        <div className="text-green-700 dark:text-green-300">
                                              {round2?.notes?.score_revision?.reason && (
                                                <div className="mb-1">{round2?.notes?.score_revision?.reason}</div>
                                          )}
                                              {round2?.notes?.score_revision?.adjustment && (
                                                <div>Adjustment: {round2?.notes?.score_revision?.adjustment > 0 ? '+' : ''}{round2?.notes?.score_revision?.adjustment}</div>
                                          )}
                                              {round2?.notes?.score_revision?.new_score && (
                                                <div>New Score: {round2?.notes?.score_revision?.new_score}/40</div>
                                          )}
                                        </div>
                                      </div>
                                    )}

                                    {round2?.notes?.community_influence && (
                                      <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs">
                                        <div className="font-medium text-green-800 dark:text-green-200 mb-1">
                                          Community Influence
                                        </div>
                                        <div className="text-green-700 dark:text-green-300 capitalize">
                                              {round2?.notes?.community_influence}
                                        </div>
                                      </div>
                                    )}

                                    {round2?.notes?.confidence && (
                                      <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs">
                                        <div className="font-medium text-green-800 dark:text-green-200 mb-1">
                                          Judge Confidence
                                        </div>
                                        <div className="text-green-700 dark:text-green-300 capitalize">
                                              {round2?.notes?.confidence}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </>
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
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Metadata */}
          <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
            <CardHeader>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Information</h3>
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
                {submission.twitter_handle && (
                  <div className="flex items-center justify-between">
                    <dt className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                      {/* Twitter SVG logo */}
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" className="mr-2"><path d="M22.46 5.924c-.793.352-1.645.59-2.54.698a4.48 4.48 0 0 0 1.965-2.475 8.94 8.94 0 0 1-2.828 1.082A4.48 4.48 0 0 0 16.11 4c-2.485 0-4.5 2.014-4.5 4.5 0 .353.04.697.116 1.027C7.728 9.37 4.1 7.6 1.67 4.905c-.388.666-.61 1.44-.61 2.263 0 1.563.796 2.942 2.006 3.75a4.48 4.48 0 0 1-2.037-.563v.057c0 2.185 1.555 4.007 3.623 4.425-.378.104-.777.16-1.188.16-.29 0-.57-.028-.844-.08.57 1.78 2.223 3.075 4.183 3.11A8.98 8.98 0 0 1 2 19.54a12.68 12.68 0 0 0 6.88 2.017c8.26 0 12.78-6.84 12.78-12.77 0-.195-.004-.39-.013-.583A9.22 9.22 0 0 0 24 4.59a8.93 8.93 0 0 1-2.54.698z"/></svg>
                      X (Twitter)
                    </dt>
                    <dd className="text-sm font-medium text-indigo-700 dark:text-indigo-400 truncate max-w-[160px]">
                      <a href={`https://x.com/${submission.twitter_handle.replace(/^@/, '')}`} target="_blank" rel="noopener noreferrer" className="underline hover:text-indigo-900 dark:hover:text-indigo-200">
                        {submission.twitter_handle}
                      </a>
                    </dd>
                  </div>
                )}
                {submission.solana_address && (
                  <div className="flex items-center justify-between">
                    <dt className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                      {solanaLogo}
                      Solana Address
                    </dt>
                    <dd className="text-xs font-mono text-indigo-700 dark:text-indigo-400 truncate max-w-[160px] flex items-center">
                      <a href={`https://solscan.io/account/${submission.solana_address}`} target="_blank" rel="noopener noreferrer" className="underline hover:text-indigo-900 dark:hover:text-indigo-200 flex items-center">
                        {truncateSolanaAddress(submission.solana_address)}
                      </a>
                    </dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>

          {/* Enhanced Research Analysis */}
          {submission.research && (
            <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Research Analysis</h3>
              </CardHeader>
              <CardContent className="px-4 py-3 space-y-6">
                {(() => {
                  const assessment = getTechnicalAssessment()
                  if (!assessment && !submission.research.github_analysis) {
                    return (
                      <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                        No research data available
                      </p>
                    )
                  }

                  let sectionIndex = 0

                  return (
                    <>
                      {/* GitHub Analysis Section */}
                      {submission.research.github_analysis && (
                        <div>
                          {sectionIndex++ > 0 && <div className="border-t border-gray-200 dark:border-gray-700 mb-3"></div>}
                          <button
                            onClick={() => toggleSection('github-analysis')}
                            className="flex items-center justify-between w-full text-left hover:text-indigo-600 dark:hover:text-indigo-400 transition-all duration-200 py-2 px-2 -mx-2 rounded-lg hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10 mb-3 group"
                          >
                            <div className="flex items-center gap-4">
                              <Github className="h-5 w-5 text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform" />
                              <span className="text-base font-semibold text-gray-900 dark:text-gray-100">GitHub Analysis</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="flex items-center bg-green-50 dark:bg-green-900/20 px-3 py-1.5 rounded-full border border-green-200 dark:border-green-700">
                                <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                                <span className="text-xs font-medium text-green-700 dark:text-green-300">Completed</span>
                              </div>
                              {expandedSections['github-analysis'] ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
                            </div>
                          </button>
                          {expandedSections['github-analysis'] && (
                            <div className="pt-1 pb-4 mb-3 bg-white/50 dark:bg-gray-800/30 rounded border-l-4 border-indigo-200 dark:border-indigo-600 px-3">
                              {(() => {
                                try {
                                  const githubData = typeof submission.research.github_analysis === 'string' 
                                    ? JSON.parse(submission.research.github_analysis)
                                    : submission.research.github_analysis

                                  return (
                                    <div className="space-y-3">
                                      {/* Repository Overview */}
                                      <div className="grid grid-cols-3 gap-3">
                                        <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                                          <div className="text-lg font-semibold text-blue-700 dark:text-blue-300">
                                            {githubData.file_structure?.total_files || 0}
                                          </div>
                                          <div className="text-xs text-blue-600 dark:text-blue-400">Files</div>
                                        </div>
                                        <div className="text-center p-2 bg-green-50 dark:bg-green-900/20 rounded">
                                          <div className="text-lg font-semibold text-green-700 dark:text-green-300">
                                            {githubData.commit_activity?.total_commits !== undefined ? 
                                             githubData.commit_activity.total_commits :
                                             '—'}
                                          </div>
                                          <div className="text-xs text-green-600 dark:text-green-400">Commits</div>
                                        </div>
                                        <div className="text-center p-2 bg-purple-50 dark:bg-purple-900/20 rounded">
                                          <div className="text-lg font-semibold text-purple-700 dark:text-purple-300">
                                            {githubData.commit_activity?.commit_authors?.length !== undefined ? 
                                             githubData.commit_activity.commit_authors.length :
                                             '—'}
                                          </div>
                                          <div className="text-xs text-purple-600 dark:text-purple-400">Contributors</div>
                                        </div>
                                      </div>

                                      {/* Tech Stack */}
                                      {githubData.file_structure?.file_extensions && (
                                        <div>
                                          <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center">
                                            <Code className="h-3 w-3 mr-1" />
                                            Tech Stack
                                          </h5>
                                          <div className="flex flex-wrap gap-1">
                                            {Object.entries(githubData.file_structure.file_extensions)
                                              .sort(([,a], [,b]) => (b as number) - (a as number))
                                              .slice(0, 6)
                                              .map(([ext, count]) => (
                                                <span key={ext} className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                                                  {ext.toUpperCase()} ({count as number})
                                                </span>
                                              ))
                                            }
                                          </div>
                                        </div>
                                      )}

                                      {/* Architecture & Timeline */}
                                      <div className="grid grid-cols-2 gap-3 text-xs">
                                        <div>
                                          <div className="text-gray-700 dark:text-gray-300 mb-1">
                                            <strong>Architecture:</strong>
                                          </div>
                                          <div className="text-gray-600 dark:text-gray-400 space-y-1">
                                            {githubData.file_structure?.is_mono_repo && (
                                              <div className="flex items-center gap-1">
                                                <div className="h-1 w-1 bg-indigo-500 rounded-full"></div>
                                                Monorepo
                                              </div>
                                            )}
                                            {githubData.file_structure?.has_tests && (
                                              <div className="flex items-center gap-1">
                                                <div className="h-1 w-1 bg-green-500 rounded-full"></div>
                                                Has Tests
                                              </div>
                                            )}
                                            {githubData.file_structure?.has_docs && (
                                              <div className="flex items-center gap-1">
                                                <div className="h-1 w-1 bg-blue-500 rounded-full"></div>
                                                Has Docs
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                        <div>
                                          <div className="text-gray-700 dark:text-gray-300 mb-1">
                                            <strong>Timeline:</strong>
                                          </div>
                                          <div className="text-gray-600 dark:text-gray-400 space-y-1">
                                            {githubData.commit_activity?.days_with_commits && (
                                              <div>{githubData.commit_activity.days_with_commits} active days</div>
                                            )}
                                            {githubData.commit_activity?.days_before_deadline !== undefined && (
                                              <div className={githubData.commit_activity.days_before_deadline > 0 ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400'}>
                                                Finished {Math.abs(githubData.commit_activity.days_before_deadline)}d {githubData.commit_activity.days_before_deadline > 0 ? 'early' : 'after deadline'}
                                              </div>
                                            )}
                                            {githubData.commit_activity?.web_upload_commits && githubData.commit_activity.web_upload_commits > 0 && (
                                              <div className="text-amber-600 dark:text-amber-400">
                                                {githubData.commit_activity.web_upload_commits} web uploads
                                              </div>
                                            )}
                                            {!githubData.commit_activity?.total_commits && githubData.commit_activity?.commits_in_last_72h !== undefined && (
                                              <div className="text-gray-500 dark:text-gray-400 text-xs italic">
                                                Limited commit data
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                      </div>

                                      {/* Contributors */}
                                      {githubData.commit_activity?.commit_authors && githubData.commit_activity.commit_authors.length > 0 && (
                                        <div>
                                          <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1 flex items-center">
                                            <Users className="h-3 w-3 mr-1" />
                                            Contributors
                                          </h5>
                                          <div className="flex flex-wrap gap-1">
                                            {githubData.commit_activity.commit_authors.map((author: string) => (
                                              <span key={author} className="text-xs text-gray-600 dark:text-gray-400">
                                                {author}
                                              </span>
                                            )).reduce((prev: any, curr: any, i: number) => 
                                              prev === null ? [curr] : [...prev, <span key={`sep-${i}`} className="text-gray-400">, </span>, curr], null
                                            )}
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  )
                                } catch (e) {
                                  return (
                                    <div className="text-xs text-gray-600 dark:text-gray-300">
                                      Repository structure and commit history analyzed
                                    </div>
                                  )
                                }
                              })()}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Technical Implementation */}
                      {assessment?.technical_implementation && (
                        <div>
                          {sectionIndex++ > 0 && <div className="border-t border-gray-200 dark:border-gray-700 mb-3"></div>}
                          <button
                            onClick={() => toggleSection('technical-impl')}
                            className="flex items-center justify-between w-full text-left hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-200 py-2 px-2 -mx-2 rounded-lg hover:bg-blue-50/50 dark:hover:bg-blue-900/10 mb-3 group"
                          >
                            <div className="flex items-center gap-4">
                              <Code className="h-5 w-5 text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform" />
                              <span className="text-base font-semibold text-gray-900 dark:text-gray-100">Technical Implementation</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="shadow-sm">
                                <ScoreBadge score={assessment.technical_implementation.score} />
                              </div>
                              {expandedSections['technical-impl'] ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
                            </div>
                          </button>
                          {expandedSections['technical-impl'] && (
                            <div className="pt-1 pb-4 mb-3 bg-white/50 dark:bg-gray-800/30 rounded border-l-4 border-blue-200 dark:border-blue-600 px-3 space-y-3">
                              {/* Safe render for analysis: supports string, array, or object with positive/negative */}
                              {(() => {
                                const ti: any = (assessment as any).technical_implementation || {}
                                const analysis: any = ti.analysis ?? ti.assessment
                                if (!analysis) return null
                                if (typeof analysis === 'string') {
                                  return (
                                    <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{analysis}</p>
                                  )
                                }
                                if (Array.isArray(analysis)) {
                                  return (
                                    <div className="space-y-2">
                                      {analysis.map((line: any, idx: number) => (
                                        <p key={idx} className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{String(line)}</p>
                                      ))}
                                    </div>
                                  )
                                }
                                if (typeof analysis === 'object') {
                                  const pos = analysis.positive
                                  const neg = analysis.negative
                                  return (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                      {pos && (
                                        <div>
                                          <h5 className="text-xs font-medium text-green-800 dark:text-green-200 mb-1">Positive</h5>
                                          <ul className="text-xs text-green-700 dark:text-green-300 space-y-1 ml-4">
                                            {(Array.isArray(pos) ? pos : [pos]).map((item: any, idx: number) => (
                                              <li key={`pos-${idx}`} className="list-disc">{String(item)}</li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}
                                      {neg && (
                                        <div>
                                          <h5 className="text-xs font-medium text-orange-800 dark:text-orange-200 mb-1">Negative</h5>
                                          <ul className="text-xs text-orange-700 dark:text-orange-300 space-y-1 ml-4">
                                            {(Array.isArray(neg) ? neg : [neg]).map((item: any, idx: number) => (
                                              <li key={`neg-${idx}`} className="list-disc">{String(item)}</li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}
                                    </div>
                                  )
                                }
                                return (
                                  <pre className="text-xs text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-900/20 p-2 rounded">{JSON.stringify(analysis, null, 2)}</pre>
                                )
                              })()}
                              
                              {assessment.technical_implementation.strengths && assessment.technical_implementation.strengths.length > 0 && (
                                <div>
                                  <h5 className="text-xs font-medium text-green-800 dark:text-green-200 mb-1 flex items-center">
                                    <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                                    Strengths
                                  </h5>
                                  <ul className="text-xs text-green-700 dark:text-green-300 space-y-1 ml-4">
                                    {assessment.technical_implementation.strengths.map((strength: string, idx: number) => (
                                      <li key={idx} className="flex items-start">
                                        <span className="mr-1">•</span>
                                        <span>{strength}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {assessment.technical_implementation.weaknesses && assessment.technical_implementation.weaknesses.length > 0 && (
                                <div>
                                  <h5 className="text-xs font-medium text-orange-800 dark:text-orange-200 mb-1 flex items-center">
                                    <div className="h-2 w-2 bg-orange-500 rounded-full mr-2"></div>
                                    Areas for Improvement
                                  </h5>
                                  <ul className="text-xs text-orange-700 dark:text-orange-300 space-y-1 ml-4">
                                    {assessment.technical_implementation.weaknesses.map((weakness: string, idx: number) => (
                                      <li key={idx} className="flex items-start">
                                        <span className="mr-1">•</span>
                                        <span>{weakness}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Market Analysis */}
                      {assessment?.market_analysis && (
                        <div>
                          {sectionIndex++ > 0 && <div className="border-t border-gray-200 dark:border-gray-700 mb-3"></div>}
                          <button
                            onClick={() => toggleSection('market-analysis')}
                            className="flex items-center justify-between w-full text-left hover:text-purple-600 dark:hover:text-purple-400 transition-all duration-200 py-2 px-2 -mx-2 rounded-lg hover:bg-purple-50/50 dark:hover:bg-purple-900/10 mb-3 group"
                          >
                            <div className="flex items-center gap-4">
                              <Target className="h-5 w-5 text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform" />
                              <span className="text-base font-semibold text-gray-900 dark:text-gray-100">Market Analysis</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="shadow-sm">
                                <ScoreBadge score={assessment.market_analysis.score} />
                              </div>
                              {expandedSections['market-analysis'] ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
                            </div>
                          </button>
                          {expandedSections['market-analysis'] && (
                            <div className="pt-1 pb-4 mb-3 bg-white/50 dark:bg-gray-800/30 rounded border-l-4 border-purple-200 dark:border-purple-600 px-3 space-y-3">
                              <div className="text-sm text-gray-700 dark:text-gray-200 space-y-1">
                                {(
                                  (assessment.market_analysis as any).market_size ||
                                  (assessment.market_analysis as any).addressable_market
                                ) && (
                                  <p>
                                    <strong>Market Size:</strong> {(assessment.market_analysis as any).market_size || (assessment.market_analysis as any).addressable_market}
                                  </p>
                                )}
                                {(
                                  (assessment.market_analysis as any).unique_value ||
                                  (assessment.market_analysis as any).differentiation
                                ) && (
                                  <p>
                                    <strong>Unique Value:</strong> {(assessment.market_analysis as any).unique_value || (assessment.market_analysis as any).differentiation}
                                  </p>
                                )}
                                {(assessment.market_analysis as any).market_potential && (
                                  <p>
                                    <strong>Market Potential:</strong> {(assessment.market_analysis as any).market_potential}
                                  </p>
                                )}
                              </div>
                              
                              {assessment.market_analysis.competitors && assessment.market_analysis.competitors.length > 0 && (
                                <div>
                                  <h5 className="text-xs font-medium text-purple-800 dark:text-purple-200 mb-1 flex items-center">
                                    <div className="h-2 w-2 bg-purple-500 rounded-full mr-2"></div>
                                    Key Competitors
                                  </h5>
                                  <div className="space-y-2 ml-4">
                                    {assessment.market_analysis.competitors.slice(0, 3).map((competitor: any, idx: number) => {
                                      if (typeof competitor === 'string') {
                                        return (
                                          <div key={idx} className="text-xs text-gray-700 dark:text-gray-300">
                                            {competitor}
                                          </div>
                                        )
                                      }
                                      return (
                                        <div key={idx} className="text-xs">
                                          <p className="font-medium text-gray-900 dark:text-gray-100">{competitor.name}</p>
                                          {competitor.differentiation && (
                                            <p className="text-gray-600 dark:text-gray-400">{competitor.differentiation}</p>
                                          )}
                                        </div>
                                      )
                                    })}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Innovation Rating */}
                      {assessment?.innovation_rating && (
                        <div>
                          {sectionIndex++ > 0 && <div className="border-t border-gray-200 dark:border-gray-700 mb-3"></div>}
                          <button
                            onClick={() => toggleSection('innovation')}
                            className="flex items-center justify-between w-full text-left hover:text-yellow-600 dark:hover:text-yellow-400 transition-all duration-200 py-2 px-2 -mx-2 rounded-lg hover:bg-yellow-50/50 dark:hover:bg-yellow-900/10 mb-3 group"
                          >
                            <div className="flex items-center gap-4">
                              <Lightbulb className="h-5 w-5 text-yellow-600 dark:text-yellow-400 group-hover:scale-110 transition-transform" />
                              <span className="text-base font-semibold text-gray-900 dark:text-gray-100">Innovation Rating</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="shadow-sm">
                                <ScoreBadge score={assessment.innovation_rating.score} />
                              </div>
                              {expandedSections['innovation'] ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
                            </div>
                          </button>
                          {expandedSections['innovation'] && (
                            <div className="pt-1 pb-4 mb-3 bg-white/50 dark:bg-gray-800/30 rounded border-l-4 border-yellow-200 dark:border-yellow-600 px-3">
                              <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">{(assessment.innovation_rating as any).analysis ?? (assessment.innovation_rating as any).assessment}</p>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Viability Assessment */}
                      {assessment?.viability_assessment && (
                        <div>
                          {sectionIndex++ > 0 && <div className="border-t border-gray-200 dark:border-gray-700 mb-3"></div>}
                          <button
                            onClick={() => toggleSection('viability')}
                            className="flex items-center justify-between w-full text-left hover:text-emerald-600 dark:hover:text-emerald-400 transition-all duration-200 py-2 px-2 -mx-2 rounded-lg hover:bg-emerald-50/50 dark:hover:bg-emerald-900/10 mb-3 group"
                            type="button"
                          >
                            <div className="flex items-center gap-4">
                              <Target className="h-5 w-5 text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform" />
                              <span className="text-base font-semibold text-gray-900 dark:text-gray-100">Viability Assessment</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="shadow-sm">
                                <ScoreBadge score={assessment.viability_assessment.score} />
                              </div>
                              {expandedSections['viability'] ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
                            </div>
                          </button>
                          {expandedSections['viability'] && (
                            <div className="pt-1 pb-4 mb-3 bg-white/50 dark:bg-gray-800/30 rounded border-l-4 border-emerald-200 dark:border-emerald-600 px-3 space-y-2">
                              {(assessment.viability_assessment as any).challenges && Array.isArray((assessment.viability_assessment as any).challenges) && (
                                <div>
                                  <h5 className="text-xs font-medium text-emerald-800 dark:text-emerald-200 mb-1 flex items-center">
                                    <div className="h-2 w-2 bg-emerald-500 rounded-full mr-2"></div>
                                    Challenges
                                  </h5>
                                  <ul className="text-xs text-emerald-700 dark:text-emerald-300 space-y-1 ml-4">
                                    {(assessment.viability_assessment as any).challenges.map((c: string, idx: number) => (
                                      <li key={idx} className="list-disc">{c}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {(assessment.viability_assessment as any).production_readiness && (
                                <p className="text-sm text-gray-700 dark:text-gray-200"><strong>Production Readiness:</strong> {(assessment.viability_assessment as any).production_readiness}</p>
                              )}
                              {(assessment.viability_assessment as any).maintenance_concerns && (
                                <p className="text-sm text-gray-700 dark:text-gray-200"><strong>Maintenance:</strong> {(assessment.viability_assessment as any).maintenance_concerns}</p>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Overall Assessment */}
                      {(assessment as any).overall_assessment && (
                        <div>
                          {sectionIndex++ > 0 && <div className="border-t border-gray-200 dark:border-gray-700 mb-3"></div>}
                          <button
                            onClick={() => toggleSection('overall')}
                            className="flex items-center justify-between w-full text-left hover:text-indigo-600 dark:hover:text-indigo-400 transition-all duration-200 py-2 px-2 -mx-2 rounded-lg hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10 mb-3 group"
                            type="button"
                          >
                            <div className="flex items-center gap-4">
                              <Award className="h-5 w-5 text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform" />
                              <span className="text-base font-semibold text-gray-900 dark:text-gray-100">Overall Assessment</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="shadow-sm">
                                <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 border border-indigo-200 dark:border-indigo-700">
                                  {(assessment as any).overall_assessment?.final_score ?? '—'}/10
                                </span>
                              </div>
                              {expandedSections['overall'] ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
                            </div>
                          </button>
                          {expandedSections['overall'] && (
                            <div className="pt-1 pb-4 mb-3 bg-white/50 dark:bg-gray-800/30 rounded border-l-4 border-indigo-200 dark:border-indigo-600 px-3 space-y-2">
                              {(assessment as any).overall_assessment?.summary && (
                                <p className="text-sm text-gray-700 dark:text-gray-200">{(assessment as any).overall_assessment.summary}</p>
                              )}
                              {(assessment as any).overall_assessment?.recommendation && (
                                <p className="text-sm text-gray-700 dark:text-gray-200"><strong>Recommendation:</strong> {(assessment as any).overall_assessment.recommendation}</p>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Red Flags */}
                      {assessment?.red_flags && assessment.red_flags.length > 0 && (
                        <div>
                          {sectionIndex++ > 0 && <div className="border-t border-gray-200 dark:border-gray-700 mb-3"></div>}
                          <button
                            onClick={() => toggleSection('red-flags')}
                            className="flex items-center justify-between w-full text-left hover:text-red-600 dark:hover:text-red-400 transition-all duration-200 py-2 px-2 -mx-2 rounded-lg hover:bg-red-50/50 dark:hover:bg-red-900/10 mb-3 group"
                          >
                            <div className="flex items-center gap-4">
                              <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 group-hover:scale-110 transition-transform" />
                              <span className="text-base font-semibold text-red-800 dark:text-red-200">Red Flags</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="shadow-sm">
                                <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-700">
                                  {assessment.red_flags.length} flags
                                </span>
                              </div>
                              {expandedSections['red-flags'] ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
                            </div>
                          </button>
                          {expandedSections['red-flags'] && (
                            <div className="pt-1 pb-4 mb-3 bg-white/50 dark:bg-gray-800/30 rounded border-l-4 border-red-200 dark:border-red-600 px-3">
                              <ul className="text-sm text-red-700 dark:text-red-300 space-y-1">
                                {assessment.red_flags.map((flag: string, idx: number) => (
                                  <li key={idx} className="flex items-start">
                                    <span className="mr-1">•</span>
                                    <span>{flag}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Judge Insights */}
                      {assessment?.judge_insights && (
                        <div>
                          {sectionIndex++ > 0 && <div className="border-t border-gray-200 dark:border-gray-700 mb-3"></div>}
                          <button
                            onClick={() => toggleSection('judge-insights')}
                            className="flex items-center justify-between w-full text-left hover:text-indigo-600 dark:hover:text-indigo-400 transition-all duration-200 py-2 px-2 -mx-2 rounded-lg hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10 mb-3 group"
                          >
                            <div className="flex items-center gap-4">
                              <Award className="h-5 w-5 text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform" />
                              <span className="text-base font-semibold text-gray-900 dark:text-gray-100">Judge Insights</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="shadow-sm">
                                <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 border border-indigo-200 dark:border-indigo-700">
                                  {Object.keys(assessment.judge_insights).length} perspectives
                                </span>
                              </div>
                              {expandedSections['judge-insights'] ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
                            </div>
                          </button>
                          {expandedSections['judge-insights'] && (
                            <div className="pt-1 pb-4 mb-3 bg-gradient-to-r from-indigo-50/30 to-transparent dark:from-indigo-900/10 dark:to-transparent rounded-lg space-y-2">
                              {Object.entries(assessment.judge_insights).map(([judge, insight]: [string, any]) => {
                                // Map research judge names to avatar keys
                                const judgeKey = normalizeJudgeKey(judge)
                                const displayName = judgeKey
                                
                                return (
                                  <div key={judge} className="py-2 px-3 bg-white/50 dark:bg-gray-800/30 rounded border-l-4 border-indigo-200 dark:border-indigo-600">
                                    <div className="flex items-center gap-2 mb-2">
                                      <img
                                        src={getJudgeAvatar(judge)}
                                        alt={judge + ' avatar'}
                                        className="h-6 w-6 rounded-full border-2 border-white dark:border-gray-600 shadow-sm"
                                      />
                                      <div>
                                        <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 capitalize">
                                          {displayName.replace('ai', 'AI ')}
                                        </span>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">
                                          {judgeSpecialtyMap[judgeKey] || 'AI Judge'}
                                        </p>
                                      </div>
                                    </div>
                                    <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed">
                                      "{insight}"
                                    </p>
                                  </div>
                                )
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )
                })()}
              </CardContent>
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