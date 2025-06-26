import { object, string } from 'yup'

export const SubmissionSchema = object({
  project_name: string().required('Project name is required').max(100, 'Project name must be 100 characters or less'),
  team_name: string().required('Team name is required').max(100, 'Team name must be 100 characters or less'),
  category: string().required('Category is required'),
  description: string().required('Description is required').max(2000, 'Description must be 2000 characters or less'),
  discord_handle: string()
    .required('Discord handle is required')
    .matches(/^.+#\d{4}$|^.+$/, 'Discord handle should be in format username#1234 or just username'),
  twitter_handle: string().notRequired(),
  github_url: string().url('Must be a valid URL').required('GitHub URL is required'),
  demo_video_url: string().url('Must be a valid URL').required('Demo video URL is required'),
  live_demo_url: string().url('Must be a valid URL').notRequired(),
  logo_url: string().url('Must be a valid URL').notRequired(),
  tech_stack: string().notRequired(),
  how_it_works: string().notRequired(),
  problem_solved: string().notRequired(),
  coolest_tech: string().notRequired(),
  next_steps: string().notRequired(),
})

export type SubmissionInputs = {
  project_name: string
  team_name: string
  category: string
  description: string
  discord_handle: string
  twitter_handle?: string
  github_url: string
  demo_video_url: string
  live_demo_url?: string
  logo_url?: string
  tech_stack?: string
  how_it_works?: string
  problem_solved?: string
  coolest_tech?: string
  next_steps?: string
}

export const categoryOptions = [
  "DeFi",
  "AI/Agents", 
  "Gaming",
  "Infrastructure",
  "Social",
  "Other"
] 