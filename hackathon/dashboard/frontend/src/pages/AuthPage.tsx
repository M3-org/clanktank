import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/Button'
import { Card, CardHeader, CardContent } from '../components/Card'
import { useAuth } from '../contexts/AuthContext'
import { hackathonApi } from '../lib/api'
import { toast } from 'react-hot-toast'

export default function AuthPage() {
  const navigate = useNavigate()
  const { authState } = useAuth()

  // Redirect if already authenticated
  useEffect(() => {
    if (authState.isAuthenticated) {
      navigate('/dashboard', { replace: true })
    }
  }, [authState.isAuthenticated, navigate])

  const handleDiscordLogin = async () => {
    try {
      const authUrl = await hackathonApi.getDiscordAuthUrl()
      window.location.href = authUrl
    } catch (error) {
      console.error('Discord login error:', error)
      toast.error('Failed to initiate Discord login. Please try again.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Welcome to Clank Tank Hackathon
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            Sign in with Discord to participate
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center">
            <Button
              onClick={handleDiscordLogin}
              className="w-full bg-[#5865F2] hover:bg-[#4752C4] text-white border-none"
              size="lg"
            >
              <svg 
                className="w-5 h-5 mr-2" 
                viewBox="0 0 24 24" 
                fill="currentColor"
              >
                <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419-.0189 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1568 2.4189Z"/>
              </svg>
              Continue with Discord
            </Button>
          </div>

          <div className="text-center text-sm text-gray-600 dark:text-gray-400">
            <p className="mb-4">
              By continuing, you agree to participate in the Clank Tank Hackathon and allow us to use your Discord username for submissions.
            </p>
            
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                Why Discord?
              </h3>
              <ul className="text-blue-800 dark:text-blue-200 text-sm space-y-1">
                <li>• Simple one-click authentication</li>
                <li>• Your username is automatically populated</li>
                <li>• Easy to track your submissions</li>
                <li>• Connected to our Discord community</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 