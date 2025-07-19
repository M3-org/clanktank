import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { SubmissionSummary, Stats } from '../types'
import { Card, CardContent } from '../components/Card'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { DiscordAvatar } from '../components/DiscordAvatar'
import { VoteModal } from '../components/VoteModal'
import { PrizePool } from '../components/PrizePool'
import { 
  RefreshCw, 
  Trophy, 
  Code, 
  Users, 
  Filter,
  ChevronDown,
  LayoutGrid,
  LayoutList,
  ArrowUp,
  ArrowDown
} from 'lucide-react'
import { StatusBadge } from '../components/Badge'


export default function Dashboard() {
  const [submissions, setSubmissions] = useState<SubmissionSummary[]>([])
  const [, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list')
  const [sortField, setSortField] = useState<'project_name' | 'category' | 'status' | 'avg_score' | 'created_at' | 'discord_username'>('avg_score')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
  const [selectedSubmission, setSelectedSubmission] = useState<SubmissionSummary | null>(null)

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
    
    // Handle special cases for submitter field
    if (sortField === 'discord_username') {
      aVal = a.discord_username || a.discord_handle || ''
      bVal = b.discord_username || b.discord_handle || ''
    }
    
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}


      {/* Prize Pool */}
      <PrizePool goal={10} variant="banner" />

      {/* Filters */}
      <Card className="mb-6 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <CardContent className="p-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Filters:</span>
            </div>
            
            <div className="relative">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="appearance-none block w-full rounded-md border-0 py-1.5 pl-3 pr-10 text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 ring-1 ring-inset ring-gray-300 dark:ring-gray-700 focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6"
              >
                {/* Note: Most browsers do not support custom styles for <option> dropdowns. This only works in some browsers (e.g., Firefox). */}
                <option value="" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">All Statuses</option>
                <option value="submitted" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">Submitted</option>
                <option value="researched" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">Researched</option>
                <option value="scored" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">Scored</option>
                <option value="published" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">Published</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-2 h-4 w-4 text-gray-400" />
            </div>

            <div className="relative">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="appearance-none block w-full rounded-md border-0 py-1.5 pl-3 pr-10 text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 ring-1 ring-inset ring-gray-300 dark:ring-gray-700 focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6"
              >
                {/* Note: Most browsers do not support custom styles for <option> dropdowns. This only works in some browsers (e.g., Firefox). */}
                <option value="" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">All Categories</option>
                <option value="DeFi" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">DeFi</option>
                <option value="Gaming" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">Gaming</option>
                <option value="AI/Agents" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">AI/Agents</option>
                <option value="Infrastructure" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">Infrastructure</option>
                <option value="Social" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">Social</option>
                <option value="Other" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">Other</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-2 h-4 w-4 text-gray-400" />
            </div>

            <div className="flex items-center gap-2 ml-auto">
              <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                <Users className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {submissions.length} Total
                </span>
              </div>
              
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
        <Card className="overflow-hidden bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" onClick={() => handleSort('discord_username')}>
                    <div className="flex items-center gap-1">
                      Submitter
                      {sortField === 'discord_username' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      )}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" onClick={() => handleSort('project_name')}>
                    <div className="flex items-center gap-1">
                      Project
                      {sortField === 'project_name' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      )}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" onClick={() => handleSort('category')}>
                    <div className="flex items-center gap-1">
                      Category
                      {sortField === 'category' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      )}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" onClick={() => handleSort('status')}>
                    <div className="flex items-center gap-1">
                      Status
                      {sortField === 'status' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      )}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" onClick={() => handleSort('avg_score')}>
                    <div className="flex items-center gap-1">
                      Score
                      {sortField === 'avg_score' && (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />
                      )}
                    </div>
                  </th>
                  <th className="relative px-6 py-3">
                    <span className="sr-only">Vote</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
                {sortedSubmissions.map((submission) => (
                  <tr key={submission.submission_id} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <DiscordAvatar
                          discord_id={submission.discord_id}
                          discord_avatar={submission.discord_avatar}
                          discord_handle={submission.discord_handle}
                          size="md"
                          className="border border-gray-300 dark:border-gray-700"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-200">
                          {submission.discord_username || submission.discord_handle || '—'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <Link
                          to={`/submission/${submission.submission_id}`}
                          className="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-200"
                        >
                          {submission.project_name}
                        </Link>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {submission.team_name}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center justify-between mb-2 text-xs font-medium min-h-[1.25em]">
                        <span
                          role="button"
                          tabIndex={0}
                          title={`Filter by ${submission.category}`}
                          className={
                            `cursor-pointer select-none focus:outline-none focus:ring-2 focus:ring-indigo-500 hover:opacity-80 ` +
                            (submission.category?.toLowerCase() === 'defi' ? 'text-blue-700 dark:text-blue-100' :
                             submission.category?.toLowerCase() === 'gaming' ? 'text-green-800 dark:text-green-100' :
                             submission.category?.toLowerCase().includes('ai') ? 'text-yellow-800 dark:text-yellow-100' :
                             'text-gray-700 dark:text-gray-100')
                          }
                          onClick={() => setCategoryFilter(submission.category)}
                          onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') setCategoryFilter(submission.category); }}
                        >
                          {submission.category}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={submission.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {submission.avg_score ? (
                        <div className="font-semibold text-gray-900 dark:text-white">{submission.avg_score.toFixed(2)}</div>
                      ) : (
                        <span className="text-gray-400 dark:text-gray-500">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Button
                        onClick={() => setSelectedSubmission(submission)}
                        size="sm"
                        className="bg-gradient-to-r from-indigo-500 to-sky-500 hover:from-indigo-600 hover:to-sky-600 text-white"
                      >
                        Vote
                      </Button>
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
            <Card
              key={submission.submission_id}
              className="overflow-hidden hover:shadow-lg transition-shadow flex flex-col cursor-pointer group focus-within:ring-2 focus-within:ring-indigo-500"
              tabIndex={0}
              onClick={() => window.location.href = `/submission/${submission.submission_id}`}
              onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') window.location.href = `/submission/${submission.submission_id}`; }}
            >
              {/* Preview Image */}
              <div className="aspect-[9/5] bg-gradient-to-br from-indigo-100 to-purple-100 relative overflow-hidden">
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
                {/* Category top left */}
                <span
                  role="button"
                  tabIndex={0}
                  title={`Filter by ${submission.category}`}
                  className={
                    `absolute top-2 left-2 z-10 text-xs font-semibold cursor-pointer select-none focus:outline-none focus:ring-2 focus:ring-indigo-500 hover:opacity-80 ` +
                    (submission.category?.toLowerCase() === 'defi' ? 'text-blue-700 dark:text-blue-100' :
                     submission.category?.toLowerCase() === 'gaming' ? 'text-green-800 dark:text-green-100' :
                     submission.category?.toLowerCase().includes('ai') ? 'text-yellow-800 dark:text-yellow-100' :
                     'text-gray-800 dark:text-gray-100')
                  }
                  onClick={() => setCategoryFilter(submission.category)}
                  onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') setCategoryFilter(submission.category); }}
                >
                  {submission.category}
                </span>
                {/* Status icon bottom right */}
                <span
                  className={
                    `absolute bottom-2 right-2 z-10 text-lg font-bold select-none ` +
                    (submission.status === 'completed' || submission.status === 'published'
                      ? 'text-green-500'
                      : 'text-amber-500')
                  }
                  title={submission.status.charAt(0).toUpperCase() + submission.status.slice(1)}
                >
                  {(submission.status === 'completed' || submission.status === 'published')
                    ? '✓'
                    : <span className="inline-block align-middle" style={{fontSize: '1em'}}>&#8987;</span>}
                </span>
              </div>
              <CardContent className="p-4 flex flex-col flex-1">
                <div className="flex items-center gap-2 mb-1 min-h-[2.5em]">
                  <DiscordAvatar
                    discord_id={submission.discord_id}
                    discord_avatar={submission.discord_avatar}
                    discord_handle={submission.discord_handle}
                    size="md"
                    className="border border-gray-300 dark:border-gray-700"
                  />
                  <Link
                    to={`/submission/${submission.submission_id}`}
                    className="font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-200 line-clamp-2 truncate"
                  >
                    {submission.project_name}
                  </Link>
                  <span className="text-xs text-gray-500 dark:text-gray-400 truncate">· {submission.discord_username || submission.discord_handle || '—'}</span>
                </div>
                {submission.description && (
                  <div className="text-sm text-gray-700 dark:text-gray-300 mb-2 line-clamp-2" title={submission.description}>
                    {submission.description}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Vote Modal */}
      {selectedSubmission && (
        <VoteModal
          submission={selectedSubmission}
          onClose={() => setSelectedSubmission(null)}
        />
      )}
    </div>
  )
}