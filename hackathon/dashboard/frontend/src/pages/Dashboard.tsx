import { useEffect, useState, useMemo, lazy, Suspense } from 'react'
import { useSearchParams } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { SubmissionSummary, Stats } from '../types'
import { Card, CardContent } from '../components/Card'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'
import { DiscordAvatar } from '../components/DiscordAvatar'
// Lazy load modal components to reduce initial bundle
const SubmissionModal = lazy(() => import('../components/SubmissionModal').then(module => ({ default: module.SubmissionModal })))
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
  ArrowDown,
  Search
} from 'lucide-react'
import { StatusBadge } from '../components/Badge'


export default function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [submissions, setSubmissions] = useState<SubmissionSummary[]>([])
  const [, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  
  // Initialize state from URL parameters
  const [searchTerm, setSearchTerm] = useState<string>(searchParams.get('search') || '')
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('status') || '')
  const [categoryFilter, setCategoryFilter] = useState<string>(searchParams.get('category') || '')
  const [viewMode, setViewMode] = useState<'list' | 'grid'>((searchParams.get('view') as 'list' | 'grid') || 'list')
  const [sortField, setSortField] = useState<'project_name' | 'category' | 'status' | 'avg_score' | 'created_at' | 'discord_username' | 'submission_id'>((searchParams.get('sort') as any) || 'avg_score')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>((searchParams.get('dir') as 'asc' | 'desc') || 'desc')
  const [viewingSubmissionId, setViewingSubmissionId] = useState<number | null>(
    searchParams.get('submission') ? parseInt(searchParams.get('submission')!) : null
  )

  // Update URL parameters when filters change
  const updateSearchParams = (updates: Record<string, string | null>) => {
    const newParams = new URLSearchParams(searchParams)
    Object.entries(updates).forEach(([key, value]) => {
      if (value) {
        newParams.set(key, value)
      } else {
        newParams.delete(key)
      }
    })
    setSearchParams(newParams)
  }

  // Load data on mount and filter changes
  useEffect(() => {
    loadData()
  }, [statusFilter, categoryFilter])

  // Auto-refresh interval - only start after initial load for better mobile performance
  useEffect(() => {
    if (loading) return // Don't start interval until initial load is complete
    
    const refreshInterval = viewingSubmissionId ? 60000 : 45000 // Longer interval for mobile battery
    const interval = setInterval(loadData, refreshInterval)
    return () => clearInterval(interval)
  }, [loading, viewingSubmissionId])

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
    const newDirection = field === sortField ? (sortDirection === 'asc' ? 'desc' : 'asc') : 'asc'
    setSortField(field)
    setSortDirection(newDirection)
    updateSearchParams({ sort: field, dir: newDirection })
  }

  const handleStatusFilterChange = (status: string) => {
    setStatusFilter(status)
    updateSearchParams({ status: status || null })
  }

  const handleCategoryFilterChange = (category: string) => {
    setCategoryFilter(category)
    updateSearchParams({ category: category || null })
  }

  const handleViewModeChange = (mode: 'list' | 'grid') => {
    setViewMode(mode)
    updateSearchParams({ view: mode })
  }

  const handleViewSubmission = (submissionId: number) => {
    setViewingSubmissionId(submissionId)
    updateSearchParams({ submission: submissionId.toString() })
  }

  const handleCloseModal = () => {
    setViewingSubmissionId(null)
    updateSearchParams({ submission: null })
  }

  const handleNavigateSubmission = (direction: 'prev' | 'next') => {
    if (!viewingSubmissionId) return
    
    const currentIndex = sortedSubmissions.findIndex(s => s.submission_id === viewingSubmissionId)
    if (currentIndex === -1) return
    
    let newIndex
    if (direction === 'prev') {
      newIndex = currentIndex > 0 ? currentIndex - 1 : sortedSubmissions.length - 1
    } else {
      newIndex = currentIndex < sortedSubmissions.length - 1 ? currentIndex + 1 : 0
    }
    
    const newSubmissionId = sortedSubmissions[newIndex].submission_id
    setViewingSubmissionId(newSubmissionId)
    updateSearchParams({ submission: newSubmissionId.toString() })
  }

  // Get unique categories for filter dropdown
  const uniqueCategories = useMemo(() => {
    const categories = [...new Set(submissions.map(s => s.category).filter(Boolean))]
    return categories.sort()
  }, [submissions])

  // Memoize filtered and sorted submissions
  const sortedSubmissions = useMemo(() => {
    if (submissions.length === 0) return []
    
    // Apply search and filters first
    let filtered = submissions
    
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase()
      filtered = filtered.filter(submission => 
        submission.project_name?.toLowerCase().includes(searchLower) ||
        submission.team_name?.toLowerCase().includes(searchLower) ||
        submission.description?.toLowerCase().includes(searchLower) ||
        submission.discord_username?.toLowerCase().includes(searchLower) ||
        submission.discord_handle?.toLowerCase().includes(searchLower)
      )
    }
    
    return filtered.slice().sort((a, b) => {
      let aVal: any, bVal: any
      
      // Pre-compute values instead of doing it in comparison
      switch (sortField) {
        case 'discord_username':
          aVal = a.discord_username || a.discord_handle || ''
          bVal = b.discord_username || b.discord_handle || ''
          break
        case 'avg_score':
          aVal = a.avg_score || 0
          bVal = b.avg_score || 0
          break
        case 'created_at':
          aVal = new Date(a.created_at).getTime()
          bVal = new Date(b.created_at).getTime()
          break
        case 'submission_id':
          aVal = a.submission_id || 0
          bVal = b.submission_id || 0
          break
        default:
          aVal = a[sortField] || ''
          bVal = b[sortField] || ''
      }
      
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
      return 0
    })
  }, [submissions, searchTerm, sortField, sortDirection])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-4 sm:py-8">
      {/* Header */}



      {/* Filters */}
      <Card className="mb-4 sm:mb-6 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <CardContent className="p-3 sm:p-6">
          <div className="flex flex-wrap gap-2 sm:gap-4 items-center">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Search projects, teams, descriptions..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value)
                    updateSearchParams({ search: e.target.value || null })
                  }}
                  className="w-full pl-10 pr-4 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Filters:</span>
            </div>
            
            <div className="relative">
              <select
                value={statusFilter}
                onChange={(e) => handleStatusFilterChange(e.target.value)}
                className="appearance-none block w-full rounded-md border-0 py-1.5 pl-3 pr-8 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 ring-1 ring-inset ring-gray-300 dark:ring-gray-700 focus:ring-2 focus:ring-indigo-600"
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
                onChange={(e) => handleCategoryFilterChange(e.target.value)}
                className="appearance-none block w-full rounded-md border-0 py-1.5 pl-3 pr-8 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900 ring-1 ring-inset ring-gray-300 dark:ring-gray-700 focus:ring-2 focus:ring-indigo-600"
              >
                <option value="" className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">All Categories</option>
                {uniqueCategories.map(category => (
                  <option key={category} value={category} className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
                    {category}
                  </option>
                ))}
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
                  onClick={() => handleViewModeChange('list')}
                  variant={viewMode === 'list' ? 'primary' : 'secondary'}
                  size="sm"
                  className="rounded-r-none"
                >
                  <LayoutList className="h-4 w-4" />
                </Button>
                <Button
                  onClick={() => handleViewModeChange('grid')}
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
          <div className="overflow-x-auto -webkit-overflow-scrolling-touch" style={{scrollBehavior: 'smooth'}}>
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0 z-10">
                <tr>
                  <th 
                    className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all duration-200 select-none" 
                    onClick={() => handleSort('submission_id' as any)}
                    title="Click to sort by submission ID"
                  >
                    <div className="flex items-center gap-1">
                      <span className="hidden sm:inline">ID</span>
                      <span className="sm:hidden">#</span>
                      {sortField === 'submission_id' ? (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3 text-indigo-600 dark:text-indigo-400" /> : <ArrowDown className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
                      ) : (
                        <div className="h-3 w-3 opacity-0 group-hover:opacity-50">↕</div>
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all duration-200 select-none" 
                    onClick={() => handleSort('discord_username')}
                    title="Click to sort by submitter"
                  >
                    <div className="flex items-center gap-1">
                      <span className="hidden sm:inline">Submitter</span>
                      <span className="sm:hidden">User</span>
                      {sortField === 'discord_username' ? (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3 text-indigo-600 dark:text-indigo-400" /> : <ArrowDown className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
                      ) : (
                        <div className="h-3 w-3 opacity-0 group-hover:opacity-50">↕</div>
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all duration-200 select-none" 
                    onClick={() => handleSort('project_name')}
                    title="Click to sort by project name"
                  >
                    <div className="flex items-center gap-1">
                      Project
                      {sortField === 'project_name' ? (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3 text-indigo-600 dark:text-indigo-400" /> : <ArrowDown className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
                      ) : (
                        <div className="h-3 w-3 opacity-0 group-hover:opacity-50">↕</div>
                      )}
                    </div>
                  </th>
                  <th 
                    className="hidden md:table-cell px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all duration-200 select-none" 
                    onClick={() => handleSort('category')}
                    title="Click to sort by category"
                  >
                    <div className="flex items-center gap-1">
                      Category
                      {sortField === 'category' ? (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3 text-indigo-600 dark:text-indigo-400" /> : <ArrowDown className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
                      ) : (
                        <div className="h-3 w-3 opacity-0 group-hover:opacity-50">↕</div>
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all duration-200 select-none" 
                    onClick={() => handleSort('status')}
                    title="Click to sort by status"
                  >
                    <div className="flex items-center gap-1">
                      Status
                      {sortField === 'status' ? (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3 text-indigo-600 dark:text-indigo-400" /> : <ArrowDown className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
                      ) : (
                        <div className="h-3 w-3 opacity-0 group-hover:opacity-50">↕</div>
                      )}
                    </div>
                  </th>
                  <th 
                    className="hidden sm:table-cell px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all duration-200 select-none" 
                    onClick={() => handleSort('avg_score')}
                    title="Click to sort by score"
                  >
                    <div className="flex items-center gap-1">
                      Score
                      {sortField === 'avg_score' ? (
                        sortDirection === 'asc' ? <ArrowUp className="h-3 w-3 text-indigo-600 dark:text-indigo-400" /> : <ArrowDown className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />
                      ) : (
                        <div className="h-3 w-3 opacity-0 group-hover:opacity-50">↕</div>
                      )}
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
                {sortedSubmissions.map((submission) => (
                  <tr 
                    key={submission.submission_id} 
                    className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
                    onClick={() => handleViewSubmission(submission.submission_id)}
                  >
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        #{submission.submission_id}
                      </div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <DiscordAvatar
                          discord_id={submission.discord_id}
                          discord_avatar={submission.discord_avatar}
                          discord_handle={submission.discord_handle}
                          size="sm"
                          className="border border-gray-300 dark:border-gray-700"
                        />
                        <span className="text-xs sm:text-sm text-gray-700 dark:text-gray-200 truncate max-w-[80px] sm:max-w-none">
                          {submission.discord_username || submission.discord_handle || '—'}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4">
                      <div>
                        <div className="text-xs sm:text-sm font-medium text-indigo-600 dark:text-indigo-400 text-left line-clamp-2">
                          {submission.project_name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 truncate sm:block hidden">
                          {submission.team_name}
                        </div>
                        <div className="md:hidden text-xs text-gray-600 dark:text-gray-300 mt-1">
                          {submission.category}
                        </div>
                      </div>
                    </td>
                    <td className="hidden md:table-cell px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                      <span
                        role="button"
                        tabIndex={0}
                        title={`Filter by ${submission.category}`}
                        className={
                          `cursor-pointer select-none focus:outline-none focus:ring-2 focus:ring-indigo-500 hover:opacity-80 text-xs font-medium ` +
                          (submission.category?.toLowerCase() === 'defi' ? 'text-blue-700 dark:text-blue-100' :
                           submission.category?.toLowerCase() === 'gaming' ? 'text-green-800 dark:text-green-100' :
                           submission.category?.toLowerCase().includes('ai') ? 'text-yellow-800 dark:text-yellow-100' :
                           'text-gray-700 dark:text-gray-100')
                        }
                        onClick={() => handleCategoryFilterChange(submission.category)}
                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleCategoryFilterChange(submission.category); }}
                      >
                        {submission.category}
                      </span>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                      <StatusBadge status={submission.status} />
                    </td>
                    <td className="hidden sm:table-cell px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {submission.avg_score ? (
                        <div className="font-semibold text-gray-900 dark:text-white">{submission.avg_score.toFixed(2)}</div>
                      ) : (
                        <span className="text-gray-400 dark:text-gray-500">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
          {sortedSubmissions.map((submission) => (
            <Card
              key={submission.submission_id}
              className="overflow-hidden hover:shadow-lg transition-shadow flex flex-col cursor-pointer group focus-within:ring-2 focus-within:ring-indigo-500"
              tabIndex={0}
              onClick={() => handleViewSubmission(submission.submission_id)}
              onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleViewSubmission(submission.submission_id); }}
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
                    loading="lazy"
                    decoding="async"
                    onError={(e) => {
                      // Simple fallback - just hide the image
                      (e.target as HTMLImageElement).style.display = 'none'
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
                  onClick={() => handleCategoryFilterChange(submission.category)}
                  onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleCategoryFilterChange(submission.category); }}
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
                  <span className="font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-200 line-clamp-2 truncate">
                    {submission.project_name}
                  </span>
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

      {/* Submission Detail Modal */}
      {viewingSubmissionId && (
        <Suspense fallback={
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          </div>
        }>
          <SubmissionModal
            submissionId={viewingSubmissionId}
            onClose={handleCloseModal}
            onNavigate={handleNavigateSubmission}
            allSubmissionIds={sortedSubmissions.map(s => s.submission_id)}
          />
        </Suspense>
      )}
    </div>
  )
}