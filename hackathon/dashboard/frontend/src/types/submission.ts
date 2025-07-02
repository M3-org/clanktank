/**
 * HACKATHON SCHEMA ARCHITECTURE
 * =============================
 * 
 * Single Source of Truth: /hackathon/submission_schema.json
 * 
 * Flow:
 * 1. JSON schema defines all fields, validation rules, and UI config
 * 2. Backend (schema.py) loads JSON schema for Python validation  
 * 3. Frontend (schemaLoader.ts) fetches schema via API
 * 4. Frontend dynamically generates Yup validation from schema
 * 5. This file (submission.ts) contains all TypeScript types
 * 
 * Benefits:
 * - Single source of truth
 * - No more hardcoded schemas  
 * - Automatic sync between frontend/backend
 * - Dynamic validation generation
 */

// Field definition type used by the dynamic schema loader
export type SubmissionField = {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'url' | 'file';
  required: boolean;
  placeholder?: string;
  maxLength?: number;
  options?: string[]; // for select fields
  pattern?: RegExp | string;
  helperText?: string;
  accept?: string; // for file fields
  maxSize?: number; // for file fields (in bytes)
};

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
  project_image?: File | string | null
  tech_stack?: string
  how_it_works?: string
  problem_solved?: string
  favorite_part?: string
  solana_address?: string
  [key: string]: string | File | null | undefined
}

export const categoryOptions = [
  "DeFi",
  "AI/Agents", 
  "Gaming",
  "Infrastructure",
  "Social",
  "Other"
] 