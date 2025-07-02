import axios from 'axios'
import { SubmissionSummary, SubmissionDetail, LeaderboardEntry, Stats } from '../types'
import { SubmissionInputs } from '../types/submission'

const API_BASE = import.meta.env.PROD ? '/data' : '/api'

// For static deployment, we'll check if we should use JSON files
const USE_STATIC = import.meta.env.VITE_USE_STATIC === 'true'

const api = axios.create({
  baseURL: API_BASE,
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
}