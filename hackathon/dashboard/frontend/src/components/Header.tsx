
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
              Clank Tank
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
                    onClick={() => navigate('/submit')}
                    size="sm"
                    className="bg-indigo-600 hover:bg-indigo-700 text-white border-none"
                  >
                    Submit Project
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