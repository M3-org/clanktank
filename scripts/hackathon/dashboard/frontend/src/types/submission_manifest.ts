// Submission manifest/config for v2 fields
// This will be the single source of truth for the submission form fields, validation, and UI rendering

export type SubmissionField = {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'url';
  required: boolean;
  placeholder?: string;
  maxLength?: number;
  options?: string[]; // for select fields
  pattern?: RegExp;
  helperText?: string;
};

export const SUBMISSION_FIELDS_V2: SubmissionField[] = [
  {
    name: 'project_name',
    label: 'Project Name',
    type: 'text',
    required: true,
    placeholder: 'My Awesome Project',
    maxLength: 100,
  },
  {
    name: 'team_name',
    label: 'Team Name',
    type: 'text',
    required: true,
    placeholder: 'The A-Team',
    maxLength: 100,
  },
  {
    name: 'category',
    label: 'Category',
    type: 'select',
    required: true,
    options: [
      'DeFi',
      'AI/Agents',
      'Gaming',
      'Infrastructure',
      'Social',
      'Other',
    ],
    placeholder: 'Select a category',
  },
  {
    name: 'description',
    label: 'Project Description',
    type: 'textarea',
    required: true,
    placeholder: 'A short, clear description of what your project does.',
    maxLength: 2000,
  },
  {
    name: 'github_url',
    label: 'GitHub URL',
    type: 'url',
    required: true,
    placeholder: 'https://github.com/...',
  },
  {
    name: 'demo_video_url',
    label: 'Demo Video URL',
    type: 'url',
    required: true,
    placeholder: 'https://youtube.com/...',
  },
  {
    name: 'live_demo_url',
    label: 'Live Demo URL',
    type: 'url',
    required: false,
    placeholder: 'https://my-project.com',
  },
  {
    name: 'logo_url',
    label: 'Project Logo URL',
    type: 'url',
    required: false,
    placeholder: 'https://my-project.com/logo.png',
  },
  {
    name: 'tech_stack',
    label: 'Tech Stack',
    type: 'textarea',
    required: false,
    placeholder: 'e.g., React, Python, Solidity,...',
  },
  {
    name: 'how_it_works',
    label: 'How It Works',
    type: 'textarea',
    required: false,
    placeholder: 'Explain the technical architecture and how the components work together.',
  },
  {
    name: 'problem_solved',
    label: 'Problem Solved',
    type: 'textarea',
    required: false,
    placeholder: 'What problem does your project solve?',
  },
  {
    name: 'coolest_tech',
    label: "What's the most impressive part of your project?",
    type: 'textarea',
    required: false,
    placeholder: 'Describe the most impressive technical aspect or feature.',
  },
  {
    name: 'next_steps',
    label: 'Next Steps',
    type: 'textarea',
    required: false,
    placeholder: 'What are your future plans for this project?',
  },
  {
    name: 'discord_handle',
    label: 'Discord Handle',
    type: 'text',
    required: true,
    placeholder: 'username#1234',
    pattern: /^.+#\d{4}$|^.+$/, // username#1234 or just username
    helperText: 'Format: username#1234 or just username',
  },
  {
    name: 'twitter_handle',
    label: 'X (Twitter) Handle',
    type: 'text',
    required: false,
    placeholder: '@username',
  },
]; 