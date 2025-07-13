import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { SubmissionDetail as SubmissionDetailType } from '../types'
import { formatDate } from '../lib/utils'
import { Card, CardHeader, CardContent } from '../components/Card'
import { Button } from '../components/Button'
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
  const { authState } = useAuth()
  const [submission, setSubmission] = useState<SubmissionDetailType | null>(null)
  const [, setFeedback] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [discordData, setDiscordData] = useState<{discord_id?: string, discord_avatar?: string} | null>(null)

  // Check if user is authenticated
  const isAuthenticated = authState.authMethod === 'discord' || authState.authMethod === 'invite'

  useEffect(() => {
    if (id) {
      loadSubmission()
      loadFeedback()
      loadDiscordData()
    }
  }, [id])

  const loadSubmission = async () => {
    if (!id) return
    
    try {
      const data = await hackathonApi.getSubmission(id)
      setSubmission(data)
    } catch (error) {
      console.error('Failed to load submission:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadFeedback = async () => {
    if (!id) return
    
    try {
      const response = await fetch(`/api/submission/${id}/feedback`)
      if (response.ok) {
        const data = await response.json()
        setFeedback(data)
      }
    } catch (error) {
      console.error('Failed to load feedback:', error)
    }
  }

  const loadDiscordData = async () => {
    if (!id) return
    
    try {
      // Get Discord data from submissions list API
      const submissions = await hackathonApi.getSubmissions()
      const submissionWithDiscord = submissions.find(s => s.submission_id === id)
      if (submissionWithDiscord) {
        setDiscordData({
          discord_id: submissionWithDiscord.discord_id,
          discord_avatar: submissionWithDiscord.discord_avatar
        })
      }
    } catch (error) {
      console.error('Failed to load Discord data:', error)
    }
  }

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
            <Link to="/dashboard">
              <Button variant="secondary" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
            </Link>
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

  // Add mapping for judge specialties (matching Frontpage.tsx)
  const judgeSpecialtyMap: Record<string, string> = {
    'aimarc': 'ROI skeptic',
    'aishaw': 'Code purist', 
    'peepo': 'UX meme lord',
    'spartan': 'DeFi maximalist',
    'eliza': 'AI Judge', // fallback for eliza or unknown judges
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
            <span className="text-lg font-semibold text-white">{submission.discord_handle}</span>
            <DiscordAvatar 
              discord_id={discordData?.discord_id || submission.discord_id}
              discord_avatar={discordData?.discord_avatar || submission.discord_avatar}
              discord_handle={submission.discord_handle}
              size="md"
              variant="dark"
            />
          </div>
        </div>
      </div>

      {/* The rest of the page content follows here, in normal flow */}
      {/* Action Buttons */}
      <div className="flex justify-between items-center mb-6 px-4 sm:px-6 lg:px-8">
        <Link to="/dashboard">
          <Button variant="ghost" size="sm" className="dark:text-gray-200 dark:hover:text-white">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
        </Link>
        
        {submission?.can_edit && isAuthenticated && (
          <Link to={`/submission/${id}/edit`}>
            <Button variant="secondary" size="sm">
              <Edit3 className="h-4 w-4 mr-2" />
              Edit Submission
            </Button>
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 px-4 sm:px-6 lg:px-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
            <CardHeader>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Description</h2>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 dark:text-gray-200 leading-relaxed">{submission.description}</p>
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
                  <p className="text-gray-700 dark:text-gray-200 leading-relaxed ml-5">{submission.problem_solved}</p>
                </div>
              )}
              
              {submission.favorite_part && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    Favorite Part
                  </h3>
                  <p className="text-gray-700 dark:text-gray-200 leading-relaxed ml-5">{submission.favorite_part}</p>
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
                {/* Judge-centric cards */}
                <div className="space-y-6">
                  {Array.from(new Set((submission.scores || []).map(s => s.judge_name.trim().toLowerCase()))).map((judgeKey) => {
                    const round1 = (submission.scores || []).find(s => s.judge_name && s.round === 1 && s.judge_name.trim().toLowerCase() === judgeKey)
                    const round2 = (submission.scores || []).find(s => s.judge_name && s.round === 2 && s.judge_name.trim().toLowerCase() === judgeKey)
                    
                    // Use weighted totals from backend (respects judge-specific multipliers)
                    const round1Total = round1 ? round1.weighted_total : 0
                    const round2Total = round2 ? round2.weighted_total : 0
                    
                    // Use the original judge name from round1 or round2 for display
                    const judgeName = round1?.judge_name || round2?.judge_name || judgeKey
                    const avatarSrc = judgeAvatarMap[judgeKey] || '/avatars/default.png';
                                    return (
                      <div key={judgeName} className="border border-gray-200 dark:border-gray-700 rounded-lg p-5 hover:border-indigo-300 dark:hover:border-indigo-500 transition-colors bg-white dark:bg-gray-900">
                        {/* Judge header */}
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <img
                              src={avatarSrc}
                              alt={judgeName + ' avatar'}
                              className="h-8 w-8 rounded-full border border-gray-200 dark:border-gray-700 object-cover bg-white dark:bg-gray-800"
                              style={{ minWidth: 32, minHeight: 32 }}
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
                                  round1Total >= 8 ? 'text-emerald-600 dark:text-emerald-400' :
                                  round1Total >= 6 ? 'text-amber-600 dark:text-amber-400' :
                                  round1Total >= 4 ? 'text-orange-600 dark:text-orange-400' :
                                  'text-red-600 dark:text-red-400'
                                }`}>R1</span>
                                <div className={`px-3 py-1 rounded-full text-sm font-bold ${
                                  round1Total >= 8 ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200' :
                                  round1Total >= 6 ? 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200' :
                                  round1Total >= 4 ? 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200' :
                                  'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                                }`}>
                                  {round1Total.toFixed(1)}
                                </div>
                              </div>
                            )}
                            {round2 && (
                              <div className="flex items-center gap-2">
                                <span className={`text-xs font-semibold ${
                                  round2Total >= 8 ? 'text-emerald-600 dark:text-emerald-400' :
                                  round2Total >= 6 ? 'text-amber-600 dark:text-amber-400' :
                                  round2Total >= 4 ? 'text-orange-600 dark:text-orange-400' :
                                  'text-red-600 dark:text-red-400'
                                }`}>R2</span>
                                <div className={`px-3 py-1 rounded-full text-sm font-bold ${
                                  round2Total >= 8 ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200' :
                                  round2Total >= 6 ? 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200' :
                                  round2Total >= 4 ? 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200' :
                                  'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                                }`}>
                                  {round2Total.toFixed(1)}
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
                                <div className="grid grid-cols-2 gap-3 mb-3">
                                  {[
                                    ['innovation', round1.innovation],
                                    ['technical_execution', round1.technical_execution],
                                    ['market_potential', round1.market_potential],
                                    ['user_experience', round1.user_experience],
                                  ].map(([key, value]) => {
                                    const Icon = scoreIcons[key as keyof typeof scoreIcons]
                                    const label = (key as string).replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                                    const numValue = value as number
                                    return (
                                      <div key={key as string} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                        <div className="flex items-center gap-2">
                                          <Icon className={`h-4 w-4 ${
                                            numValue >= 8 ? 'text-emerald-600 dark:text-emerald-400' :
                                            numValue >= 6 ? 'text-amber-600 dark:text-amber-400' :
                                            'text-gray-400 dark:text-gray-500'
                                          }`} />
                                          <span className="text-xs text-gray-700 dark:text-gray-200 font-medium">{label}</span>
                                        </div>
                                        <div className={`px-2 py-1 rounded-md text-xs font-bold ${
                                          numValue >= 8 ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200' :
                                          numValue >= 6 ? 'bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200' :
                                          numValue >= 4 ? 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200' :
                                          'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                                        }`}>
                                          {value !== null && value !== undefined ? value : '-'}
                                        </div>
                                      </div>
                                    )
                                  })}
                                </div>
                                {round1.notes?.overall_comment ? (
                                  <div className={`mt-2`}> 
                                    <div className={`relative flex items-start w-full rounded-lg p-3 leading-6 italic ${round1Total >= 8 ? 'bg-indigo-50 dark:bg-indigo-900' : 'bg-gray-50 dark:bg-gray-800'} border-l-4 ${round1Total >= 8 ? 'border-indigo-500 dark:border-indigo-400' : 'border-gray-200 dark:border-gray-700'}`}> 
                                      <Quote className="h-4 w-4 text-gray-400 dark:text-gray-500 opacity-60 absolute left-2 top-2" />
                                      <span className="pl-6 text-gray-900 dark:text-gray-100">"{round1.notes.overall_comment}"</span>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="mt-2 text-xs text-gray-400 dark:text-gray-500 italic">– no comment –</div>
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
                              </>
                            ) : (
                              <div className="text-xs text-gray-400 dark:text-gray-500 italic">No round 2 data</div>
                            )}
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

          {/* Research Summary */}
          {submission.research && (
            <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Research Summary</h3>
              </CardHeader>
              <CardContent>
                {submission.research.github_analysis && (
                  <div className="mb-3 p-3 bg-indigo-50 dark:bg-indigo-900 rounded-lg">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center">
                        <Github className="h-4 w-4 mr-2" />
                        GitHub Analysis
                      </h4>
                      <div className="flex items-center">
                        <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                        <span className="text-xs text-gray-600 dark:text-gray-300">Completed</span>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* AI Research Summary */}
                {submission.research.technical_assessment && (
                  <div className="mb-3 p-3 bg-green-50 dark:bg-green-900 rounded-lg">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center">
                        <TrendingUp className="h-4 w-4 mr-2" />
                        AI Research
                      </h4>
                      <div className="flex items-center">
                        <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                        <span className="text-xs text-gray-600 dark:text-gray-300">Completed</span>
                      </div>
                    </div>
                    
                    {(() => {
                      try {
                        const research = typeof submission.research.technical_assessment === 'string' 
                          ? JSON.parse(submission.research.technical_assessment) 
                          : submission.research.technical_assessment;
                        
                        // Only show red flags if any exist
                        if (research['Red Flags'] && Array.isArray(research['Red Flags']) && research['Red Flags'].length > 0) {
                          return (
                            <div className="mt-2 p-2 bg-red-50 dark:bg-red-900 rounded border-l-4 border-red-400">
                              <h5 className="text-xs font-medium text-red-800 dark:text-red-200 mb-1">Red Flags Found</h5>
                              <ul className="text-xs text-red-700 dark:text-red-300 space-y-1">
                                {research['Red Flags'].slice(0, 2).map((flag: string, idx: number) => (
                                  <li key={idx} className="flex items-start">
                                    <span className="mr-1">•</span>
                                    <span>{flag}</span>
                                  </li>
                                ))}
                                {research['Red Flags'].length > 2 && (
                                  <li className="text-xs italic">... and {research['Red Flags'].length - 2} more</li>
                                )}
                              </ul>
                            </div>
                          );
                        }
                        return null;
                      } catch (e) {
                        return null;
                      }
                    })()}
                  </div>
                )}
                
                {!submission.research.github_analysis && !submission.research.technical_assessment && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                    No research data available
                  </p>
                )}
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
            <CardContent>
              <LikeDislike submissionId={submission.submission_id} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}