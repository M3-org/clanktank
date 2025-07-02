import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { SubmissionDetail as SubmissionDetailType } from '../types'
import { formatDate } from '../lib/utils'
import { Card, CardHeader, CardContent } from '../components/Card'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { 
  ArrowLeft, 
  ExternalLink, 
  Github, 
  Video, 
  Globe,
  RefreshCw,
  Star,
  Code,
  TrendingUp,
  Users,
  Calendar,
  Hash,
  RefreshCcw,
  Trophy,
  Heart
} from 'lucide-react'
import { StatusBadge } from '../components/StatusBadge'
import { CategoryBadge } from '../components/CategoryBadge'

export default function SubmissionDetail() {
  const { id } = useParams<{ id: string }>()
  const [submission, setSubmission] = useState<SubmissionDetailType | null>(null)
  const [feedback, setFeedback] = useState<any>(null)
  const [loading, setLoading] = useState(true)

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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card className="max-w-lg mx-auto mt-16">
          <CardContent className="text-center py-12">
            <div className="rounded-full bg-gray-100 h-16 w-16 flex items-center justify-center mx-auto mb-4">
              <Code className="h-8 w-8 text-gray-400" />
            </div>
            <p className="text-gray-500 mb-6">Submission not found</p>
            <Link to="/">
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

  const scoreIcons = {
    innovation: Star,
    technical_execution: Code,
    market_potential: TrendingUp,
    user_experience: Users
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Back Button */}
      <Link to="/">
        <Button variant="ghost" size="sm" className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>
      </Link>

      {/* Header */}
      <Card className="mb-6">
        <CardContent className="py-8">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">{submission.project_name}</h1>
              <p className="mt-2 text-xl text-gray-600">by <span className="font-medium">{submission.team_name}</span></p>
              
              <div className="mt-6 flex flex-wrap gap-3">
                <CategoryBadge category={submission.category} />
                <StatusBadge status={submission.status} />
                {submission.avg_score && (
                  <Badge variant="default">
                    <Trophy className="h-3 w-3 mr-1" />
                    Score: {submission.avg_score.toFixed(2)}/40
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* Links */}
          <div className="mt-8 pt-6 border-t border-gray-100 flex flex-wrap gap-3">
            {submission.github_url && (
              <a
                href={submission.github_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="secondary" size="sm">
                  <Github className="h-4 w-4 mr-2" />
                  GitHub
                  <ExternalLink className="h-3 w-3 ml-2" />
                </Button>
              </a>
            )}
            {submission.demo_video_url && (
              <a
                href={submission.demo_video_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="secondary" size="sm">
                  <Video className="h-4 w-4 mr-2" />
                  Demo Video
                  <ExternalLink className="h-3 w-3 ml-2" />
                </Button>
              </a>
            )}
            {submission.live_demo_url && (
              <a
                href={submission.live_demo_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="secondary" size="sm">
                  <Globe className="h-4 w-4 mr-2" />
                  Live Demo
                  <ExternalLink className="h-3 w-3 ml-2" />
                </Button>
              </a>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold text-gray-900">Description</h2>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 leading-relaxed">{submission.description}</p>
            </CardContent>
          </Card>

          {/* Details */}
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold text-gray-900">Project Details</h2>
            </CardHeader>
            <CardContent className="space-y-6">
              {submission.how_it_works && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    How It Works
                  </h3>
                  <p className="text-gray-700 leading-relaxed ml-5">{submission.how_it_works}</p>
                </div>
              )}
              
              {submission.problem_solved && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    Problem Solved
                  </h3>
                  <p className="text-gray-700 leading-relaxed ml-5">{submission.problem_solved}</p>
                </div>
              )}
              
              {submission.coolest_tech && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    Technical Highlights
                  </h3>
                  <p className="text-gray-700 leading-relaxed ml-5">{submission.coolest_tech}</p>
                </div>
              )}
              
              {submission.next_steps && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    What's Next
                  </h3>
                  <p className="text-gray-700 leading-relaxed ml-5">{submission.next_steps}</p>
                </div>
              )}
              
              {submission.tech_stack && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2 flex items-center">
                    <div className="h-2 w-2 bg-indigo-600 rounded-full mr-3"></div>
                    Tech Stack
                  </h3>
                  <p className="text-gray-700 leading-relaxed ml-5">{submission.tech_stack}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Judge Scores */}
          {submission.scores && submission.scores.length > 0 && (
            <Card>
              <CardHeader>
                <h2 className="text-xl font-semibold text-gray-900">Judge Scores</h2>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {submission.scores.map((score) => (
                    <div key={score.judge_name} className="border border-gray-200 rounded-lg p-5 hover:border-indigo-300 transition-colors">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-gray-900 capitalize">
                            {score.judge_name.replace('ai', 'AI ')}
                          </h4>
                          <p className="text-xs text-gray-500">AI Judge</p>
                        </div>
                        <div className="text-right">
                          <span className="text-2xl font-bold text-indigo-600">
                            {score.weighted_total.toFixed(2)}
                          </span>
                          <p className="text-xs text-gray-500">Total Score</p>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-gray-100">
                        {Object.entries({
                          innovation: score.innovation,
                          technical_execution: score.technical_execution,
                          market_potential: score.market_potential,
                          user_experience: score.user_experience
                        }).map(([key, value]) => {
                          const Icon = scoreIcons[key as keyof typeof scoreIcons]
                          return (
                            <div key={key} className="flex items-center justify-between bg-gray-50 rounded-md px-3 py-2">
                              <div className="flex items-center gap-2">
                                <Icon className="h-4 w-4 text-indigo-600" />
                                <span className="text-sm text-gray-700">
                                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </span>
                              </div>
                              <span className="text-sm font-semibold">{value}/10</span>
                            </div>
                          )
                        })}
                      </div>
                      
                      {score.notes?.overall_comment && (
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          <p className="text-sm text-gray-600 italic bg-gray-50 rounded-md p-3">
                            "{score.notes.overall_comment}"
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Metadata */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-gray-900">Information</h3>
            </CardHeader>
            <CardContent>
              <dl className="space-y-4">
                <div className="flex items-center justify-between">
                  <dt className="flex items-center text-sm text-gray-500">
                    <Hash className="h-4 w-4 mr-2" />
                    Submission ID
                  </dt>
                  <dd className="text-sm font-medium text-gray-900">{submission.submission_id}</dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="flex items-center text-sm text-gray-500">
                    <Calendar className="h-4 w-4 mr-2" />
                    Created
                  </dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {formatDate(submission.created_at)}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="flex items-center text-sm text-gray-500">
                    <RefreshCcw className="h-4 w-4 mr-2" />
                    Last Updated
                  </dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {formatDate(submission.updated_at)}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {/* Research Summary */}
          {submission.research && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900">Research Summary</h3>
              </CardHeader>
              <CardContent>
                {submission.research.github_analysis && (
                  <div className="mb-4 p-4 bg-indigo-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-900 flex items-center">
                        <Github className="h-4 w-4 mr-2" />
                        GitHub Analysis
                      </h4>
                      <Badge variant="info">
                        Score: {submission.research.github_analysis.quality_score || 'N/A'}/100
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-600">
                      Repository analyzed for code quality and activity
                    </p>
                  </div>
                )}
                <p className="text-xs text-gray-500 italic">
                  Detailed research data available in database
                </p>
              </CardContent>
            </Card>
          )}

          {/* Community Feedback */}
          {feedback && feedback.total_votes > 0 && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Heart className="h-5 w-5 mr-2 text-red-500" />
                  Community Feedback
                </h3>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <p className="text-sm text-gray-600 mb-3">
                    <span className="font-medium">{feedback.total_votes}</span> total votes from the community
                  </p>
                  
                  <div className="space-y-3">
                    {feedback.feedback.map((item: any) => (
                      <div key={item.reaction_type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{item.emoji}</span>
                          <div>
                            <span className="text-sm font-medium text-gray-900">{item.name}</span>
                            <p className="text-xs text-gray-500">{item.vote_count} votes</p>
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
                    <div className="mt-4 pt-3 border-t border-gray-200">
                      <details className="group">
                        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                          View voters ({feedback.feedback.reduce((acc: number, item: any) => acc + item.voters.length, 0)} total)
                        </summary>
                        <div className="mt-2 space-y-2">
                          {feedback.feedback.map((item: any) => (
                            item.voters.length > 0 && (
                              <div key={item.reaction_type} className="text-xs">
                                <span className="font-medium">{item.emoji} {item.name}:</span>
                                <span className="text-gray-600 ml-1">
                                  {item.voters.join(', ')}
                                </span>
                              </div>
                            )
                          ))}
                        </div>
                      </details>
                    </div>
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