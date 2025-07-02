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
}

export interface Score {
  judge_name: string
  innovation: number
  technical_execution: number
  market_potential: number
  user_experience: number
  weighted_total: number
  notes?: {
    reasons?: Record<string, string>
    overall_comment?: string
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