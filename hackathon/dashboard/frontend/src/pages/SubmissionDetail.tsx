import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { SubmissionDetail as SubmissionDetailType } from '../types'
import { formatDate } from '../lib/utils'
import { Card, CardHeader, CardContent } from '../components/Card'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { useAuth } from '../contexts/AuthContext'
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
  Edit3
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
  const [feedback, setFeedback] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Check if user is authenticated
  const isAuthenticated = authState.authMethod === 'discord' || authState.authMethod === 'invite'

  useEffect(() => {
    if (id) {
      loadSubmission()
      loadFeedback()
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

  // Helper for score gradient
  function getScoreGradient(value: number) {
    if (value <= 5) return 'linear-gradient(90deg, #ef4444, #f87171)'; // red
    if (value <= 8) return 'linear-gradient(90deg, #f59e42, #fbbf24)'; // orange
    return 'linear-gradient(90deg, #fbbf24, #ffd700)'; // gold
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
          <p className="text-lg text-white/80 mb-2">by <span className="font-semibold text-white">{submission.team_name}</span></p>
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
              {submission.how_it_works && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    How It Works
                  </h3>
                  <p className="text-gray-700 dark:text-gray-200 leading-relaxed ml-5">{submission.how_it_works}</p>
                </div>
              )}
              
              {submission.problem_solved && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    Problem Solved
                  </h3>
                  <p className="text-gray-700 dark:text-gray-200 leading-relaxed ml-5">{submission.problem_solved}</p>
                </div>
              )}
              
              {submission.coolest_tech && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    Technical Highlights
                  </h3>
                  <p className="text-gray-700 dark:text-gray-200 leading-relaxed ml-5">{submission.coolest_tech}</p>
                </div>
              )}
              
              {submission.next_steps && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    What's Next
                  </h3>
                  <p className="text-gray-700 dark:text-gray-200 leading-relaxed ml-5">{submission.next_steps}</p>
                </div>
              )}
              
              {submission.tech_stack && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    Tech Stack
                  </h3>
                  <p className="text-gray-700 dark:text-gray-200 leading-relaxed ml-5">{submission.tech_stack}</p>
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
                    // Use the original judge name from round1 or round2 for display
                    const judgeName = round1?.judge_name || round2?.judge_name || judgeKey
                    const avatarSrc = judgeAvatarMap[judgeKey] || '/avatars/default.png';
                    console.log('Judge:', judgeName, 'Key:', judgeKey, 'Avatar:', avatarSrc);
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
                              <p className="text-xs text-gray-500 dark:text-gray-400">AI Judge</p>
                            </div>
                          </div>
                          <div className="flex flex-col items-end gap-1">
                            {round1 && (
                              <div className="w-44 flex flex-col items-end">
                                <div className="flex items-center w-full">
                                  <span className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold mr-2">R1</span>
                                  <div className="flex-1 h-3 rounded bg-gray-200 dark:bg-gray-700 relative overflow-hidden">
                                    <div
                                      className="h-full rounded"
                                      style={{
                                        width: `${Math.min((round1.weighted_total / 40) * 100, 100)}%`,
                                        background: 'linear-gradient(90deg, #6366f1, #818cf8)',
                                        transition: 'width 0.3s'
                                      }}
                                    />
                                  </div>
                                  <span className="ml-2 text-xs font-medium tabular-nums min-w-[38px] text-right text-gray-900 dark:text-gray-100">{round1.weighted_total.toFixed(2)}/40</span>
                                </div>
                              </div>
                            )}
                            {round2 && (
                              <div className="w-44 flex flex-col items-end">
                                <div className="flex items-center w-full">
                                  <span className="text-xs text-green-700 dark:text-green-400 font-semibold mr-2">R2</span>
                                  <div className="flex-1 h-3 rounded bg-gray-200 dark:bg-gray-700 relative overflow-hidden">
                                    <div
                                      className="h-full rounded"
                                      style={{
                                        width: `${Math.min((round2.weighted_total / 40) * 100, 100)}%`,
                                        background: 'linear-gradient(90deg, #22c55e, #4ade80)',
                                        transition: 'width 0.3s'
                                      }}
                                    />
                                  </div>
                                  <span className="ml-2 text-xs font-medium tabular-nums min-w-[38px] text-right text-gray-900 dark:text-gray-100">{round2.weighted_total.toFixed(2)}/40</span>
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
                                    return (
                                      <div key={key as string} className="flex items-center gap-2">
                                        <Icon className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                                        <span className="w-24 text-xs text-gray-700 dark:text-gray-200">{label}</span>
                                        <div className="flex-1 h-3 rounded bg-gray-200 dark:bg-gray-700 relative overflow-hidden">
                                          {typeof value === 'number' && value >= 0 ? (
                                            <div
                                              className="h-full rounded"
                                              style={{
                                                width: `${(value as number / 10) * 100}%`,
                                                background: getScoreGradient(value as number),
                                                transition: 'width 0.3s'
                                              }}
                                            />
                                          ) : null}
                                        </div>
                                        <span className="ml-2 text-xs font-medium tabular-nums min-w-[32px] text-right text-gray-900 dark:text-gray-100">{value !== null && value !== undefined ? value + '/10' : '-'}</span>
                                      </div>
                                    )
                                  })}
                                </div>
                                {round1.notes?.overall_comment ? (
                                  <div className={`mt-2`}> 
                                    <div className={`relative flex items-start w-full rounded-lg p-3 leading-6 italic ${round1.weighted_total >= 36 ? 'bg-indigo-50 dark:bg-indigo-900' : 'bg-gray-50 dark:bg-gray-800'} border-l-4 ${round1.weighted_total >= 36 ? 'border-indigo-500 dark:border-indigo-400' : 'border-gray-200 dark:border-gray-700'}`}> 
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
                                {round2.notes?.final_verdict ? (
                                  <div className={`mt-2`}> 
                                    <div className={`relative flex items-start w-full rounded-lg p-3 leading-6 italic bg-green-50 dark:bg-green-900 border-l-4 border-green-400 dark:border-green-500`}> 
                                      <Quote className="h-4 w-4 text-gray-400 dark:text-gray-500 opacity-60 absolute left-2 top-2" />
                                      <span className="pl-6 text-gray-900 dark:text-gray-100">"{round2.notes.final_verdict}"</span>
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
                {submission['solana_address'] && (
                  <div className="flex items-center justify-between">
                    <dt className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                      {solanaLogo}
                      Solana Address
                    </dt>
                    <dd className="text-xs font-mono text-indigo-700 dark:text-indigo-400 truncate max-w-[160px] flex items-center">
                      <a href={`https://solscan.io/account/${submission['solana_address']}`} target="_blank" rel="noopener noreferrer" className="underline hover:text-indigo-900 dark:hover:text-indigo-200 flex items-center">
                        {truncateSolanaAddress(submission['solana_address'])}
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
                  <div className="mb-4 p-4 bg-indigo-50 dark:bg-indigo-900 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center">
                        <Github className="h-4 w-4 mr-2" />
                        GitHub Analysis
                      </h4>
                      <Badge variant="info">
                        Score: {submission.research.github_analysis.quality_score || 'N/A'}/100
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-300">
                      Repository analyzed for code quality and activity
                    </p>
                  </div>
                )}
                <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                  Detailed research data available in database
                </p>
              </CardContent>
            </Card>
          )}

          {/* Community Feedback */}
          {feedback && feedback.total_votes > 0 && (
            <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                  <Heart className="h-5 w-5 mr-2 text-red-500 dark:text-red-400" />
                  Community Feedback
                </h3>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                    <span className="font-medium">{feedback.total_votes}</span> total votes from the community
                  </p>
                  
                  <div className="space-y-3">
                    {feedback.feedback.map((item: any) => (
                      <div key={item.reaction_type} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{item.emoji}</span>
                          <div>
                            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.name}</span>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{item.vote_count} votes</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge variant="secondary">
                            {item.vote_count}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {feedback.feedback.length > 0 && (
                    <></>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}