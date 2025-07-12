import { DiscordAvatar } from './DiscordAvatar'
import { Flame, ThumbsUp } from 'lucide-react'
import { cn } from '../lib/utils'
import type { LeaderboardEntry } from '../types'

const RANK_COLORS = {
  1: { ring: 'ring-[#f5c000] ring-offset-2 ring-offset-white dark:ring-offset-gray-950', text: 'text-[#f5c000]' },   // gold
  2: { ring: 'ring-[#c0c0c0] ring-offset-2 ring-offset-white dark:ring-offset-gray-950', text: 'text-[#c0c0c0]' },   // silver
  3: { ring: 'ring-[#cd7f32] ring-offset-2 ring-offset-white dark:ring-offset-gray-950', text: 'text-[#cd7f32]' },   // bronze
} as const

export function LeaderboardCard({ entry }: { entry: LeaderboardEntry }) {
  const medal = RANK_COLORS[entry.rank as keyof typeof RANK_COLORS] ?? {}
  const Icon = entry.community_score && entry.community_score >= 8
    ? Flame : entry.community_score && entry.community_score >= 6
    ? ThumbsUp : null

  return (
    <div
      className={cn(
        "group relative rounded-xl p-6 backdrop-blur border border-gray-200/60 dark:border-gray-700/60 transition-all duration-200",
        "before:pointer-events-none before:absolute before:inset-0 before:rounded-[inherit]",
        "before:bg-gradient-to-br before:from-white/5 before:via-white/0 before:to-white/5",
        "hover:before:opacity-60 before:opacity-40 hover:-translate-y-0.5 hover:shadow-lg"
      )}
    >
      {/* rank badge */}
      <div className={cn(
        "absolute -left-4 -top-4 h-9 w-9 rounded-full flex items-center justify-center text-sm font-bold bg-white dark:bg-gray-950 ring-4",
        medal.ring, medal.text
      )}>{entry.rank}</div>

      <div className="flex items-center gap-4">
        <DiscordAvatar 
          discord_id={entry.discord_id}
          discord_avatar={entry.discord_avatar}
          discord_handle={entry.discord_handle}
          size="lg" 
          className="ring-2 ring-white dark:ring-gray-950" 
        />
        <div className="flex-1 min-w-0">
          <a
            href={`/submission/${entry.submission_id || entry.project_name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9\-]/g, '')}`}
            className="text-lg font-semibold hover:underline text-gray-900 dark:text-white group-hover:text-gray-700 dark:group-hover:text-gray-200 transition-colors"
          >
            {entry.project_name}
          </a>
          <p className="text-xs text-gray-500 dark:text-gray-400">{entry.category}</p>
        </div>

        {/* Scores */}
        <div className="text-right">
          <div className="text-xl font-bold text-gray-900 dark:text-white">{entry.final_score.toFixed(1)}</div>
          <p className="text-[10px] uppercase tracking-wide text-gray-500 dark:text-gray-400">AI Score</p>
        </div>
        <div className="text-right w-12">
          {Icon && <Icon className="mx-auto h-5 w-5 text-blue-600 dark:text-blue-400 mb-1" />}
          <p className="text-xs font-medium text-blue-600 dark:text-blue-400">
            {entry.community_score ? entry.community_score.toFixed(1) : "—"}
          </p>
        </div>
      </div>
    </div>
  )
}