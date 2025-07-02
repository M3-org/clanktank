import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { SubmissionSummary, Stats } from '../types'
import { formatDate } from '../lib/utils'
import { Card, CardContent } from '../components/Card'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { 
  ArrowUpRight, 
  RefreshCw, 
  Trophy, 
  Code, 
  Users, 
  Clock,
  Filter,
  ChevronDown,
  LayoutGrid,
  LayoutList,
  ArrowUp,
  ArrowDown
} from 'lucide-react'

export default function Dashboard() {
  const [submissions, setSubmissions] = useState<SubmissionSummary[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  // const [sortBy, setSortBy] = useState<'created' | 'score'>('created')
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list')
  const [sortField, setSortField] = useState<'project_name' | 'category' | 'status' | 'avg_score' | 'created_at'>('created_at')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000) // Auto-refresh every 30s
    return () => clearInterval(interval)
  }, [statusFilter, categoryFilter])

  const loadData = async () => {
    try {
      const [submissionsData, statsData] = await Promise.all([
        hackathonApi.getSubmissions({ 
          status: statusFilter || undefined, 
          category: categoryFilter || undefined 
        }),
        hackathonApi.getStats()
      ])
      setSubmissions(submissionsData)
      setStats(statsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (field: typeof sortField) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedSubmissions = [...submissions].sort((a, b) => {
    let aVal: any = a[sortField]
    let bVal: any = b[sortField]
    
    // Handle null/undefined values
    if (aVal === null || aVal === undefined) aVal = ''
    if (bVal === null || bVal === undefined) bVal = ''
    
    // Handle numeric vs string comparison
    if (sortField === 'avg_score') {
      aVal = aVal || 0
      bVal = bVal || 0
    } else if (sortField === 'created_at') {
      aVal = new Date(aVal).getTime()
      bVal = new Date(bVal).getTime()
    }
    
    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Hackathon Dashboard</h1>
        <p className="mt-2 text-gray-600">Monitor and manage hackathon submissions</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Code className="h-6 w-6 text-indigo-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Submissions
                    </dt>
                    <dd className="text-2xl font-bold text-gray-900">
                      {stats.total_submissions || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Trophy className="h-6 w-6 text-yellow-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Published
                    </dt>
                    <dd className="text-2xl font-bold text-gray-900">
                      {stats.by_status?.published || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Scored
                    </dt>
                    <dd className="text-2xl font-bold text-gray-900">
                      {stats.by_status?.scored || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Clock className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      In Progress
                    </dt>
                    <dd className="text-2xl font-bold text-gray-900">
                      {(stats.by_status?.submitted || 0) + (stats.by_status?.researched || 0)}
                    </dd>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">Filters:</span>
            </div>
            
            <div className="relative">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="appearance-none block w-full rounded-md border-0 py-1.5 pl-3 pr-10 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6"
              >
                <option value="">All Statuses</option>
                <option value="submitted">Submitted</option>
                <option value="researched">Researched</option>
                <option value="scored">Scored</option>
                <option value="published">Published</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-2 h-4 w-4 text-gray-400" />
            </div>

            <div className="relative">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="appearance-none block w-full rounded-md border-0 py-1.5 pl-3 pr-10 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6"
              >
                <option value="">All Categories</option>
                <option value="DeFi">DeFi</option>
                <option value="Gaming">Gaming</option>
                <option value="AI/Agents">AI/Agents</option>
                <option value="Infrastructure">Infrastructure</option>
                <option value="Social">Social</option>
                <option value="Other">Other</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-2 h-4 w-4 text-gray-400" />
            </div>

            <div className="flex items-center gap-2 ml-auto">
              <Button
                onClick={loadData}
                variant="secondary"
                size="sm"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              
              <div className="flex rounded-md shadow-sm" role="group">
                <Button
                  onClick={() => setViewMode('list')}
                  variant={viewMode === 'list' ? 'primary' : 'secondary'}
                  size="sm"
                  className="rounded-r-none"
                >
                  <LayoutList className="h-4 w-4" />
                </Button>
                <Button
                  onClick={() => setViewMode('grid')}
                  variant={viewMode === 'grid' ? 'primary' : 'secondary'}
                  size="sm"
                  className="rounded-l-none border-l-0"
                >
                  <LayoutGrid className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Submissions Display */}
      {viewMode === 'list' ? (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => handleSort('project_name')}
                  >
                    <div className="flex items-center gap-1">
                      Project
                      {sortField === 'project_name' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => handleSort('category')}
                  >
                    <div className="flex items-center gap-1">
                      Category
                      {sortField === 'category' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => handleSort('status')}
                  >
                    <div className="flex items-center gap-1">
                      Status
                      {sortField === 'status' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => handleSort('avg_score')}
                  >
                    <div className="flex items-center gap-1">
                      Score
                      {sortField === 'avg_score' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => handleSort('created_at')}
                  >
                    <div className="flex items-center gap-1">
                      Created
                      {sortField === 'created_at' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      )}
                    </div>
                  </th>
                  <th className="relative px-6 py-3">
                    <span className="sr-only">View</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedSubmissions.map((submission) => (
                  <tr key={submission.submission_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {submission.project_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {submission.team_name}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={
                        submission.category === 'DeFi' ? 'info' :
                        submission.category === 'Gaming' ? 'secondary' :
                        submission.category === 'AI/Agents' ? 'warning' :
                        'default'
                      }>
                        {submission.category}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={
                        submission.status === 'published' ? 'success' :
                        submission.status === 'scored' ? 'info' :
                        submission.status === 'researched' ? 'secondary' :
                        'warning'
                      }>
                        {submission.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {submission.avg_score ? (
                        <div>
                          <div className="font-semibold">{submission.avg_score.toFixed(2)}</div>
                          <div className="text-xs text-gray-500">
                            {submission.judge_count} judges
                          </div>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(submission.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link
                        to={`/submission/${submission.submission_id}`}
                        className="text-indigo-600 hover:text-indigo-900 inline-flex items-center gap-1 font-medium"
                      >
                        View
                        <ArrowUpRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {sortedSubmissions.map((submission) => (
            <Card key={submission.submission_id} className="overflow-hidden hover:shadow-lg transition-shadow">
              {/* Preview Image */}
              <div className="aspect-video bg-gradient-to-br from-indigo-100 to-purple-100 relative overflow-hidden">
                {submission.project_image && 
                 typeof submission.project_image === 'string' && 
                 submission.project_image !== '[object File]' && 
                 submission.project_image.trim() !== '' ? (
                  <img 
                    src={submission.project_image} 
                    alt={`${submission.project_name} preview`}
                    className="absolute inset-0 w-full h-full object-cover"
                    onError={(e) => {
                      // Fallback to code icon if image fails to load
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      const parent = target.parentElement;
                      if (parent && !parent.querySelector('.fallback-icon')) {
                        const fallback = document.createElement('div');
                        fallback.className = 'fallback-icon absolute inset-0 flex items-center justify-center';
                        fallback.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-16 w-16 text-indigo-300"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>';
                        parent.appendChild(fallback);
                      }
                    }}
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Code className="h-16 w-16 text-indigo-300" />
                    {submission.project_image === '[object File]' && (
                      <div className="absolute bottom-2 left-2 text-xs text-red-500 bg-white/90 px-2 py-1 rounded">
                        Invalid Image
                      </div>
                    )}
                  </div>
                )}
                {submission.avg_score && (
                  <div className="absolute top-2 right-2">
                    <Badge variant="default" className="bg-white/90 backdrop-blur-sm">
                      <Trophy className="h-3 w-3 mr-1" />
                      {submission.avg_score.toFixed(1)}
                    </Badge>
                  </div>
                )}
              </div>
              
              <CardContent className="p-4">
                <div className="mb-3">
                  <h3 className="font-semibold text-gray-900 truncate">
                    {submission.project_name}
                  </h3>
                  <p className="text-sm text-gray-500 truncate">
                    by {submission.team_name}
                  </p>
                </div>
                
                <div className="flex items-center justify-between mb-4">
                  <Badge variant={
                    submission.category === 'DeFi' ? 'info' :
                    submission.category === 'Gaming' ? 'secondary' :
                    submission.category === 'AI/Agents' ? 'warning' :
                    'default'
                  } className="text-xs">
                    {submission.category}
                  </Badge>
                  <Badge variant={
                    submission.status === 'published' ? 'success' :
                    submission.status === 'scored' ? 'info' :
                    submission.status === 'researched' ? 'secondary' :
                    'warning'
                  } className="text-xs">
                    {submission.status}
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                  <span>{formatDate(submission.created_at)}</span>
                  {submission.judge_count && (
                    <span>{submission.judge_count} judges</span>
                  )}
                </div>
                
                <Link to={`/submission/${submission.submission_id}`}>
                  <Button variant="secondary" size="sm" className="w-full">
                    View Details
                    <ArrowUpRight className="h-3 w-3 ml-2" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}