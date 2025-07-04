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
}

export interface SubmissionDetail extends SubmissionSummary {
  description: string
  updated_at: string
  github_url?: string
  demo_video_url?: string
  live_demo_url?: string
  tech_stack?: string
  how_it_works?: string
  problem_solved?: string
  coolest_tech?: string
  next_steps?: string
  scores?: Score[]
  research?: Research
  solana_address?: string
  // Edit permission info
  can_edit?: boolean
  is_creator?: boolean
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
  }
}

export interface Research {
  github_analysis?: any
  market_research?: any
  technical_assessment?: any
}

export interface LeaderboardEntry {
  rank: number
  project_name: string
  team_name: string
  category: string
  final_score: number
  youtube_url?: string
  status: string
}

export interface Stats {
  total_submissions: number
  by_status: Record<string, number>
  by_category: Record<string, number>
  updated_at: string
}