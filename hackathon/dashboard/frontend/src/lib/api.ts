import axios from 'axios'
import { SubmissionSummary, SubmissionDetail, LeaderboardEntry, Stats, CommunityScore, PrizePoolData } from '../types'
import { SubmissionInputs } from '../types/submission'

// For static deployment, we'll check if we should use JSON files
const USE_STATIC = import.meta.env.VITE_USE_STATIC === 'true'

const API_BASE = USE_STATIC ? '/data' : (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api')

const api = axios.create({
  baseURL: API_BASE,
  // Enable caching for GET requests
  headers: {
    'Cache-Control': 'max-age=86400', // 1 day cache
  }
})

// Add Discord token to requests if available
api.interceptors.request.use((config) => {
  const discordToken = localStorage.getItem('discord_token')
  if (discordToken) {
    config.headers.Authorization = `Bearer ${discordToken}`
  }
  return config
})

// Simple in-memory response cache for GET requests
const responseCache = new Map<string, { data: any; timestamp: number }>()
const CACHE_DURATION = 24 * 60 * 60 * 1000 // 1 day cache for stable hackathon data

// Request deduplication - prevent multiple identical requests
const pendingRequests = new Map<string, Promise<any>>()

// Extended config interface for deduplication
interface ExtendedAxiosConfig {
  _resolveDedup?: (data: any) => void
  _rejectDedup?: (error: any) => void  
  _cacheKey?: string
}

api.interceptors.request.use((config) => {
  // Only cache GET requests
  if (config.method?.toLowerCase() === 'get') {
    const cacheKey = `${config.baseURL}${config.url}${JSON.stringify(config.params || {})}`
    
    // Check cache first
    const cached = responseCache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      // Return cached response immediately
      return Promise.reject({
        isAxiosError: false,
        isCached: true,
        data: cached.data
      })
    }
    
    // Check if identical request is already in flight (deduplication)
    if (pendingRequests.has(cacheKey)) {
      // Wait for the existing request instead of making a new one
      return Promise.reject({
        isAxiosError: false,
        isPending: true,
        cacheKey: cacheKey
      })
    }
    
    // Mark this request as pending
    const extendedConfig = config as ExtendedAxiosConfig
    const requestPromise = new Promise((resolve, reject) => {
      // This promise will be resolved by the response interceptor
      extendedConfig._resolveDedup = resolve
      extendedConfig._rejectDedup = reject
      extendedConfig._cacheKey = cacheKey
    })
    pendingRequests.set(cacheKey, requestPromise)
  }
  return config
})

api.interceptors.response.use(
  (response) => {
    // Cache successful GET responses and resolve pending requests
    if (response.config.method?.toLowerCase() === 'get') {
      const cacheKey = `${response.config.baseURL}${response.config.url}${JSON.stringify(response.config.params || {})}`
      
      // Cache the response
      responseCache.set(cacheKey, {
        data: response.data,
        timestamp: Date.now()
      })
      
      // Resolve any pending duplicate requests
      const pendingRequest = pendingRequests.get(cacheKey)
      const extendedConfig = response.config as ExtendedAxiosConfig
      if (pendingRequest && extendedConfig._resolveDedup) {
        extendedConfig._resolveDedup(response.data)
      }
      pendingRequests.delete(cacheKey)
    }
    return response
  },
  (error) => {
    // Handle cached responses
    if (error.isCached) {
      return Promise.resolve({ data: error.data })
    }
    
    // Handle pending duplicate requests
    if (error.isPending) {
      const pendingRequest = pendingRequests.get(error.cacheKey)
      if (pendingRequest) {
        return pendingRequest.then((data: any) => ({ data }))
      }
    }
    
    // Clean up failed requests
    const extendedConfig = error.config as ExtendedAxiosConfig
    if (extendedConfig?._cacheKey) {
      const cacheKey = extendedConfig._cacheKey
      if (extendedConfig._rejectDedup) {
        extendedConfig._rejectDedup(error)
      }
      pendingRequests.delete(cacheKey)
    }
    
    return Promise.reject(error)
  }
)

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
    const response = await api.get('/submission-schema');
    return response.data;
  },

  // Validate invite code
  validateInviteCode: async (code: string) => {
    const response = await api.post('/invite-codes/validate', { code });
    return response.data;
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

  // Get submission feedback (goes through axios cache)
  getSubmissionFeedback: async (submissionId: string) => {
    const response = await api.get(`/submission/${submissionId}/feedback`);
    return response.data;
  },

  // Get config (cached properly through axios)
  getConfig: async () => {
    if (USE_STATIC) {
      const response = await api.get('/config.json');
      return response.data;
    }
    const response = await api.get('/config');
    return response.data;
  },
}
