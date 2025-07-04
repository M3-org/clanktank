import { useEffect, useState, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { hackathonApi } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'

export default function DiscordCallback() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [error, setError] = useState<string>('')
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login } = useAuth()
  const hasProcessed = useRef(false)

  // Extract params once to avoid re-runs
  const code = searchParams.get('code')
  const oauthError = searchParams.get('error')

  useEffect(() => {
    // Prevent multiple executions of the callback
    if (hasProcessed.current) return

    const handleCallback = async () => {
      hasProcessed.current = true

      if (oauthError) {
        setStatus('error')
        setError(`Discord OAuth error: ${oauthError}`)
        return
      }

      if (!code) {
        setStatus('error')
        setError('No authorization code received from Discord')
        return
      }

      try {
        // Exchange code for user data and access token
        const result = await hackathonApi.handleDiscordCallback(code)
        
        // Use the login method from AuthContext
        login(result.user, result.access_token)
        
        setStatus('success')
        
        // Redirect to auth page to show options after a short delay
        setTimeout(() => {
          navigate('/auth')
        }, 2000)
        
      } catch (error: any) {
        console.error('Discord OAuth callback error:', error)
        setStatus('error')
        
        // Check if this is likely a "code already used" error
        if (error.response?.status === 400) {
          setError('Authentication code expired or already used. Please try logging in again.')
        } else {
          setError(error.response?.data?.detail || 'Failed to authenticate with Discord')
        }
      }
    }

    handleCallback()
  }, [code, oauthError, navigate, login])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          {status === 'loading' && (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Authenticating with Discord...
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Please wait while we complete your login.
              </p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="rounded-full h-12 w-12 bg-green-100 mx-auto mb-4 flex items-center justify-center">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-green-600">
                Successfully authenticated!
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Redirecting you to the dashboard...
              </p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="rounded-full h-12 w-12 bg-red-100 mx-auto mb-4 flex items-center justify-center">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-red-600">
                Authentication failed
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                {error}
              </p>
              <button
                onClick={() => navigate('/auth')}
                className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors"
              >
                Try Again
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
} 