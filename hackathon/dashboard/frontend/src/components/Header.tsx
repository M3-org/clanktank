
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Button } from './Button'
import { LogOut, User } from 'lucide-react'

export default function Header() {
  const { authState, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogin = () => {
    navigate('/auth')
  }

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const isAuthPage = location.pathname === '/auth'

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          
          {/* Logo/Brand */}
          <div className="flex items-center">
            <button
              onClick={() => navigate('/')}
              className="text-xl font-bold text-gray-900 dark:text-gray-100 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
            >
              🏗️ Clank Tank Hackathon
            </button>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <button
              onClick={() => navigate('/dashboard')}
              className={`text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
                location.pathname === '/dashboard' ? 'text-indigo-600 dark:text-indigo-400 font-medium' : ''
              }`}
            >
              Dashboard
            </button>

            <button
              onClick={() => navigate('/leaderboard')}
              className={`text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
                location.pathname === '/leaderboard' ? 'text-indigo-600 dark:text-indigo-400 font-medium' : ''
              }`}
            >
              Leaderboard
            </button>
          </nav>

          {/* Auth Section */}
          <div className="flex items-center space-x-4">
            {authState.isAuthenticated ? (
              <div className="flex items-center space-x-3">
                {/* User Info */}
                <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                  {authState.discordUser?.avatar ? (
                    <img
                      src={`https://cdn.discordapp.com/avatars/${authState.discordUser.discord_id}/${authState.discordUser.avatar}.png`}
                      alt="Discord avatar"
                      className="h-8 w-8 rounded-full object-cover border border-gray-300 dark:border-gray-700"
                    />
                  ) : (
                    <User className="h-8 w-8 rounded-full bg-gray-200 dark:bg-gray-700 p-1" />
                  )}
                </div>

                {/* Quick Actions */}
                {!isAuthPage && (
                  <div className="flex items-center space-x-2">
                    <Button
                      onClick={() => navigate('/submit')}
                      variant="primary"
                      size="sm"
                    >
                      Submit Project
                    </Button>
                  </div>
                )}

                {/* Logout */}
                <Button
                  onClick={handleLogout}
                  variant="secondary"
                  size="sm"
                  className="flex items-center gap-1"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="hidden sm:inline">Logout</span>
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                {!isAuthPage && (
                  <Button
                    onClick={handleLogin}
                    size="sm"
                    className="flex items-center gap-2 bg-[#5865F2] hover:bg-[#4752C4] text-white border-none"
                  >
                    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419-.0189 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1568 2.4189Z"/>
                    </svg>
                    <span className="hidden sm:inline">Login with Discord</span>
                    <span className="inline sm:hidden">Discord</span>
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      <div className="md:hidden border-t border-gray-200 dark:border-gray-700">
        <div className="px-4 py-3 space-y-1">
          <button
            onClick={() => navigate('/dashboard')}
            className={`block w-full text-left px-3 py-2 text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
              location.pathname === '/dashboard' ? 'text-indigo-600 dark:text-indigo-400 font-medium bg-indigo-50 dark:bg-indigo-900/20 rounded-md' : ''
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => navigate('/leaderboard')}
            className={`block w-full text-left px-3 py-2 text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
              location.pathname === '/leaderboard' ? 'text-indigo-600 dark:text-indigo-400 font-medium bg-indigo-50 dark:bg-indigo-900/20 rounded-md' : ''
            }`}
          >
            Leaderboard
          </button>
        </div>
      </div>
    </header>
  )
} 