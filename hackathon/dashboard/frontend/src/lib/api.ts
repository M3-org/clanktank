import axios from 'axios'
import { SubmissionSummary, SubmissionDetail, LeaderboardEntry, Stats, CommunityScore, PrizePoolData } from '../types'
import { SubmissionInputs } from '../types/submission'

const API_BASE = import.meta.env.PROD ? '/api' : 'http://localhost:8000/api'

// For static deployment, we'll check if we should use JSON files
const USE_STATIC = import.meta.env.VITE_USE_STATIC === 'true'

const api = axios.create({
  baseURL: API_BASE,
})

// Add Discord token to requests if available
api.interceptors.request.use((config) => {
  const discordToken = localStorage.getItem('discord_token')
  if (discordToken) {
    config.headers.Authorization = `Bearer ${discordToken}`
  }
  return config
})

// Post a new submission (latest)
export const postSubmission = async (data: SubmissionInputs) => {
  const response = await api.post('/submissions', data)
  return response.data  // {status:"success", submission_id:"..."}
}

export const hackathonApi = {
  // Get all submissions (latest)
  getSubmissions: async (filters?: { status?: string; category?: string }) => {
    if (USE_STATIC) {
      const response = await api.get<SubmissionSummary[]>('/submissions.json')
      let data = response.data
      
      // Apply client-side filtering for static data
      if (filters?.status) {
        data = data.filter(s => s.status === filters.status)
      }
      if (filters?.category) {
        data = data.filter(s => s.category === filters.category)
      }
      
      return data
    }
    
    const response = await api.get<SubmissionSummary[]>('/submissions', { params: filters })
    return response.data
  },

  // Get submission details (latest)
  getSubmission: async (id: string) => {
    if (USE_STATIC) {
      const response = await api.get<SubmissionDetail>(`/submission/${id}.json`)
      return response.data
    }
    
    const response = await api.get<SubmissionDetail>(`/submissions/${id}`)
    return response.data
  },

  // Get leaderboard (latest)
  getLeaderboard: async () => {
    if (USE_STATIC) {
      const response = await api.get<LeaderboardEntry[]>('/leaderboard.json')
      return response.data
    }
    
    const response = await api.get<LeaderboardEntry[]>('/leaderboard')
    return response.data
  },

  // Get stats (latest)
  getStats: async () => {
    if (USE_STATIC) {
      const response = await api.get<Stats>('/stats.json')
      return response.data
    }
    
    const response = await api.get<Stats>('/stats')
    return response.data
  },

  // Fetch the latest submission schema from the backend
  fetchSubmissionSchema: async () => {
    try {
      const response = await api.get('/submission-schema');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Validate invite code
  validateInviteCode: async (code: string) => {
    try {
      const response = await api.post('/invite-codes/validate', { code });
      return response.data;
    } catch (error) {
      throw error;
    }
  },



  // Discord OAuth methods
  getDiscordAuthUrl: async () => {
    const response = await api.get('/auth/discord/login');
    return response.data.auth_url;
  },

  handleDiscordCallback: async (code: string) => {
    const response = await api.post('/auth/discord/callback', { code });
    return response.data;
  },

  getCurrentUser: async (token: string) => {
    const response = await api.get('/auth/me', {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  discordLogout: async () => {
    const response = await api.post('/auth/discord/logout');
    return response.data;
  },

  // File upload
  uploadImage: async (file: File, submissionId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('submission_id', submissionId);
    const response = await api.post('/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Create submission
  createSubmission: async (data: any) => {
    const response = await api.post('/submissions', data);
    return response.data;
  },

  // Edit submission
  editSubmission: async (id: string, data: any) => {
    const response = await api.put(`/submissions/${id}`, data);
    return response.data;
  },

  // Token voting methods
  getCommunityScores: async () => {
    const response = await api.get<CommunityScore[]>('/community-scores');
    return response.data;
  },

  getPrizePool: async () => {
    const response = await api.get<PrizePoolData>('/prize-pool');
    return response.data;
  },

  // Like/Dislike functionality
  toggleLikeDislike: async (submissionId: string, action: 'like' | 'dislike' | 'remove') => {
    const response = await api.post(`/submissions/${submissionId}/like-dislike`, {
      submission_id: submissionId,
      action
    });
    return response.data;
  },

  getLikeDislikeCounts: async (submissionId: string) => {
    const response = await api.get(`/submissions/${submissionId}/like-dislike`);
    return response.data;
  },
}
