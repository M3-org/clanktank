export interface SubmissionSchemaV2 {
  project_name: string;
  discord_handle: string;
  category: string;
  description: string;
  twitter_handle?: string;
  github_url: string;
  demo_video_url: string;
  project_image?: string;
  problem_solved?: string;
  favorite_part?: string;
  solana_address?: string;
  ethereum_address?: string;
}
