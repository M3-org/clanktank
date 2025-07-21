import { Card } from './Card'
import { DiscordAvatar } from './DiscordAvatar'
import { cn } from '../lib/utils'
import type { LeaderboardEntry } from '../types'

const RANK_COLORS = {
  1: { ring: 'ring-[#f5c000] ring-offset-2 ring-offset-white dark:ring-offset-gray-950', text: 'text-[#f5c000]' },   // gold
  2: { ring: 'ring-[#c0c0c0] ring-offset-2 ring-offset-white dark:ring-offset-gray-950', text: 'text-[#c0c0c0]' },   // silver
  3: { ring: 'ring-[#cd7f32] ring-offset-2 ring-offset-white dark:ring-offset-gray-950', text: 'text-[#cd7f32]' },   // bronze
} as const

export function LeaderboardCard({ entry, onVoteClick }: { entry: LeaderboardEntry; onVoteClick?: () => void }) {
  const medal = RANK_COLORS[entry.rank as keyof typeof RANK_COLORS] ?? {}
  // const Icon = entry.community_score && entry.community_score >= 8
  //   ? Flame : entry.community_score && entry.community_score >= 6
  //   ? ThumbsUp : null  // Unused for now

  return (
    <Card 
      interactive
      className={cn(
        "group relative p-6 backdrop-blur",
        "before:pointer-events-none before:absolute before:inset-0 before:rounded-[inherit]",
        "before:bg-gradient-to-br before:from-white/5 before:via-white/0 before:to-white/5",
        "hover:before:opacity-60 before:opacity-40"
      )}
    >
      {/* rank badge */}
      <div className={cn(
        "absolute -left-4 -top-4 h-9 w-9 rounded-full flex items-center justify-center text-sm font-bold bg-white dark:bg-gray-950 ring-4 ring-offset-2 ring-offset-white dark:ring-offset-gray-950",
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
          <h2 className="text-lg font-semibold">
            <a
              href={`/submission/${entry.submission_id || entry.project_name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')}`}
              className="hover:underline text-gray-900 dark:text-white group-hover:text-gray-700 dark:group-hover:text-gray-200 transition-colors"
            >
              {entry.project_name}
            </a>
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400">{entry.category}</p>
        </div>

        {/* Scores */}
        <div className="text-right">
          <div className="flex items-center justify-end gap-2">
            <div className="text-xl font-bold text-gray-900 dark:text-white">{entry.final_score.toFixed(1)}</div>
            {entry.community_score !== undefined && entry.community_score > 0 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-300">
                {entry.community_score.toFixed(1)}
              </span>
            )}
          </div>
          <p className="text-[10px] uppercase tracking-wide text-gray-500 dark:text-gray-400">AI Score</p>
        </div>
        <div className="text-right w-12">
          <button
            onClick={onVoteClick}
            className="w-full px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-indigo-500 to-sky-500 hover:from-indigo-600 hover:to-sky-600 rounded-md transition-all duration-200 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40"
            aria-label={`Vote for ${entry.project_name}`}
          >
            Vote
          </button>
        </div>
      </div>
    </Card>
  )
}