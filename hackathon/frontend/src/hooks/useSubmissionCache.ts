import { useRef, useCallback } from 'react'
import { hackathonApi } from '../lib/api'
import { SubmissionDetail } from '../types'

const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

export function useSubmissionCache() {
  const cacheRef = useRef(new Map<string, { data: SubmissionDetail; timestamp: number }>())
  
  const getCachedSubmission = useCallback((id: string): SubmissionDetail | null => {
    const cached = cacheRef.current.get(id)
    if (!cached) return null
    
    // Check if cache is still valid
    if (Date.now() - cached.timestamp > CACHE_DURATION) {
      cacheRef.current.delete(id)
      return null
    }
    
    return cached.data
  }, [])
  
  const cacheSubmission = useCallback((id: string, data: SubmissionDetail) => {
    cacheRef.current.set(id, { data, timestamp: Date.now() })
  }, [])
  
  const prefetchSubmission = useCallback(async (id: string) => {
    if (getCachedSubmission(id)) return // Already cached
    
    try {
      const data = await hackathonApi.getSubmission(id)
      cacheSubmission(id, data)
    } catch (error) {
      console.error('Failed to prefetch submission:', error)
    }
  }, [getCachedSubmission, cacheSubmission])
  
  const prefetchSubmissions = useCallback(async (ids: string[]) => {
    // Prefetch up to 3 submissions to avoid too many concurrent requests
    const uncachedIds = ids.slice(0, 3).filter(id => !getCachedSubmission(id))
    await Promise.allSettled(uncachedIds.map(prefetchSubmission))
  }, [getCachedSubmission, prefetchSubmission])
  
  const clearCache = useCallback(() => {
    cacheRef.current.clear()
  }, [])
  
  return {
    getCachedSubmission,
    cacheSubmission,
    prefetchSubmission,
    prefetchSubmissions,
    clearCache
  }
}