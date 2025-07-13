export interface SubmissionSummary {
  submission_id: string
  project_name: string
  team_name: string
  category: string
  status: string
  created_at: string
  avg_score?: number
  judge_count?: number
  project_image?: string
  description?: string
  // Discord user info
  discord_id?: string
  discord_username?: string
  discord_discriminator?: string
  discord_avatar?: string
  discord_handle?: string
  twitter_handle?: string
}

export interface SubmissionDetail extends SubmissionSummary {
  description: string
  updated_at: string
  github_url?: string
  demo_video_url?: string
  project_image?: string
  problem_solved?: string
  favorite_part?: string
  scores?: Score[]
  research?: Research
  solana_address?: string
  discord_handle?: string
  // Edit permission info
  can_edit?: boolean
  is_creator?: boolean
  twitter_handle?: string
}

export interface Score {
  judge_name: string
  innovation: number | null
  technical_execution: number | null
  market_potential: number | null
  user_experience: number | null
  weighted_total: number
  round: number
  notes?: {
    reasons?: Record<string, string>
    overall_comment?: string
    final_verdict?: string
    // Round 2 flattened structure
    round2_final_verdict?: string
    round2_reasoning?: string
    score_revision?: {
      type: 'none' | 'adjustment' | 'explicit'
      new_score?: number
      adjustment?: number
      reason?: string
    }
    community_influence?: 'none' | 'minimal' | 'moderate' | 'significant'
    confidence?: 'low' | 'medium' | 'high'
    round1_score?: number
    comparative_reasoning?: string
    community_context?: CommunityContext
    judge_persona?: string
    submission_id?: string
    synthesis_timestamp?: string
  }
}

export interface CommunityContext {
  total_reactions: number
  unique_voters: number
  reaction_breakdown: Record<string, number>
  engagement_level: 'low' | 'medium' | 'high'
  thresholds: {
    high: number
    medium: number
    median: number
    mean: number
  }
}

export interface Research {
  github_analysis?: {
    file_count?: number
    token_budget?: number
    gitingest_config?: any
    red_flags?: string[]
    dependency_analysis?: any
    repository_stats?: any
  }
  market_research?: any
  technical_assessment?: any
}

export interface LeaderboardEntry {
  rank: number
  submission_id: string
  project_name: string
  category: string
  final_score: number
  community_score?: number  // Community voting score
  youtube_url?: string
  status: string
  discord_handle?: string
  // Discord user info
  discord_id?: string
  discord_username?: string
  discord_discriminator?: string
  discord_avatar?: string
  round?: number  // Added to indicate which round the score is from
}

export interface Stats {
  total_submissions: number
  by_status: Record<string, number>
  by_category: Record<string, number>
  updated_at: string
}

export interface CommunityScore {
  submission_id: string
  community_score: number
  unique_voters: number
  last_vote_time: number
}

export interface TokenBreakdown {
  mint: string
  symbol: string
  name?: string
  amount: number
  decimals: number
  logo?: string
}

export interface PrizePoolContribution {
  wallet: string
  token: string
  amount: number
  timestamp: number
  description?: string
}

export interface PrizePoolData {
  total_sol: number
  target_sol: number
  progress_percentage: number
  token_breakdown: Record<string, TokenBreakdown>
  recent_contributions: PrizePoolContribution[]
}

export interface LikeDislikeResponse {
  likes: number
  dislikes: number
  user_action?: 'like' | 'dislike' | null
}