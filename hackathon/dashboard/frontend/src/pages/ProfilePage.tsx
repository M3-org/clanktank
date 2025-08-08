import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { DiscordAvatar } from '../components/DiscordAvatar'
import { Card, CardContent, CardHeader } from '../components/Card'
import { Badge } from '../components/Badge'
import { useAuth } from '../contexts/AuthContext'
import { hackathonApi } from '../lib/api'

interface ProfileData {
  discord_id?: string
  discord_username?: string
  discord_avatar?: string
  roles?: string[]
}

export default function ProfilePage() {
  const { username: paramUsername } = useParams<{ username: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const { authState } = useAuth()
  const isModal = new URLSearchParams(location.search).get('modal') === 'true'

  // Resolve which username to show
  const query = new URLSearchParams(location.search)
  const queryUser = query.get('user') || undefined

  const selfUsername = authState.discordUser?.username
  const targetUsername = useMemo(() => {
    return paramUsername || queryUser || selfUsername || ''
  }, [paramUsername, queryUser, selfUsername])

  // If visiting /profile and we have self user, canonicalize to /p/:username for DRY
  useEffect(() => {
    if (!paramUsername && !queryUser && selfUsername) {
      navigate(`/p/${encodeURIComponent(selfUsername)}`, { replace: true })
    }
  }, [paramUsername, queryUser, selfUsername, navigate])

  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [projects, setProjects] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const run = async () => {
      if (!targetUsername) return
      setLoading(true)
      try {
        // Fetch submissions and filter by username
        const all = await hackathonApi.getSubmissions()
        const mine = all.filter(s => (s as any).discord_username === targetUsername)
        setProjects(mine)

        // Derive profile info from any submission (detail has discord info)
        let derived: ProfileData | null = null
        if (mine.length > 0) {
          try {
            const detail = await hackathonApi.getSubmission(String(mine[0].submission_id))
            derived = {
              discord_id: (detail as any).discord_id,
              discord_username: (detail as any).discord_username || targetUsername,
              discord_avatar: (detail as any).discord_avatar,
            }
          } catch {}
        }

        // Fallback to auth if viewing self
        if (!derived && authState.discordUser && authState.discordUser.username === targetUsername) {
          derived = {
            discord_id: authState.discordUser.discord_id,
            discord_username: authState.discordUser.username,
            discord_avatar: authState.discordUser.avatar,
          }
        }
        setProfile(derived || { discord_username: targetUsername })
      } finally {
        setLoading(false)
      }
    }
    run()
  }, [targetUsername, authState.discordUser])

  if (!targetUsername) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 text-gray-600 dark:text-gray-300">
        Sign in to view your profile.
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <DiscordAvatar
          discord_id={profile?.discord_id}
          discord_avatar={profile?.discord_avatar}
          discord_handle={profile?.discord_username}
          size="lg"
          className="border border-gray-300 dark:border-gray-700"
        />
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{profile?.discord_username}</h1>
          <div className="flex items-center gap-2 mt-1">
            {(profile?.roles || []).map(r => (
              <Badge key={r} variant="secondary">{r}</Badge>
            ))}
          </div>
        </div>
      </div>

      {/* Projects */}
      <Card className="bg-white dark:bg-gray-900">
        <CardHeader>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Projects</h2>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-sm text-gray-500 dark:text-gray-400">Loading...</div>
          ) : projects.length === 0 ? (
            <div className="text-sm text-gray-500 dark:text-gray-400">No projects yet.</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {projects.map(p => (
                <a key={p.submission_id} href={`/submission/${p.submission_id}${isModal ? '?modal=true' : ''}`} className="block p-3 rounded border border-gray-200 dark:border-gray-800 hover:border-indigo-400 dark:hover:border-indigo-400 transition-colors">
                  <div className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 line-clamp-2">{p.project_name}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">ID #{p.submission_id} · {p.category}</div>
                  {p.avg_score != null && (
                    <div className="text-xs text-gray-600 dark:text-gray-300 mt-1">Avg Score: {p.avg_score.toFixed(2)}</div>
                  )}
                </a>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
