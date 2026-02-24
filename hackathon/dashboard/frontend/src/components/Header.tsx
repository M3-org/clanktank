
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Button } from './Button'
import { DiscordAvatar } from './DiscordAvatar'
import { LogOut, ChevronDown, Plus, Menu, X, Camera } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { CountdownTimer } from './CountdownTimer'

export default function Header() {
  const { authState, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [userDropdownOpen, setUserDropdownOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setUserDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false)
  }, [location.pathname])

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  // const isAuthPage = location.pathname === '/auth'  // Unused for now

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center h-16">
          
          {/* Logo/Brand */}
          <div className="flex items-center">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-xl font-bold text-gray-900 dark:text-gray-100 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors h-12 md:h-14"
              style={{ alignItems: 'center' }}
            >
              <span className="relative inline-block h-10 md:h-12 w-6 md:w-8 flex-shrink-0" style={{ verticalAlign: 'middle' }}>
                <svg
                  className="absolute left-10 -translate-x-1/3 -translate-y-1 h-8 w-8 opacity-60 animate-spin-slow z-0 top-[-1px]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.5}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 8 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 8a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 8 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09c0 .66.38 1.26 1 1.51a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 8c.66 0 1.26.38 1.51 1H21a2 2 0 0 1 0 4h-.09c-.25 0-.49.09-.68.26z" />
                </svg>
              </span>
              <span className="relative inline-block h-10 md:h-12 w-24 md:w-28 flex-shrink-0" style={{ verticalAlign: 'middle' }}>
                <img 
                  src="/clanktank_white.png" 
                  alt="Clank Tank Logo" 
                  className="relative z-10 h-full w-auto max-w-[6rem] drop-shadow-lg mx-auto"
                  {...({ fetchpriority: "high" } as any)}
                  width="96"
                  height="48"
                />
              </span>
              <span className="relative inline-block h-10 md:h-12 w-6 md:w-8 flex-shrink-0" style={{ verticalAlign: 'middle' }}>
                <svg
                  className="absolute right-8 -translate-x-full -translate-y-4 h-8 w-8 opacity-60 animate-spin-slow z-0 top-[12px]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.5}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 8 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 8a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 8 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09c0 .66.38 1.26 1 1.51a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 8c.66 0 1.26.38 1.51 1H21a2 2 0 0 1 0 4h-.09c-.25 0-.49.09-.68.26z" />
                </svg>
              </span>
            </button>
          </div>

          {/* Spacer to push navigation right */}
          <div className="flex-grow"></div>

          {/* Navigation and Auth - aligned right */}
          <div className="flex items-center space-x-8">
            {/* Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              <button
                onClick={() => authState.isAuthenticated ? navigate('/submit') : navigate('/auth')}
                className={`flex items-center gap-3 text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
                  location.pathname === '/submit' || location.pathname === '/auth' ? 'text-indigo-600 dark:text-indigo-400 font-medium' : ''
                }`}
              >
                Submit
                <CountdownTimer variant="compact" showLabel={false} />
              </button>

              <button
                onClick={() => navigate('/dashboard')}
                className={`text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
                  location.pathname === '/dashboard' ? 'text-indigo-600 dark:text-indigo-400 font-medium' : ''
                }`}
              >
                Dashboard
              </button>

              <button
                onClick={() => navigate('/gallery')}
                className={`text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
                  location.pathname === '/gallery' ? 'text-indigo-600 dark:text-indigo-400 font-medium' : ''
                }`}
              >
                Gallery
              </button>

              <button
                onClick={() => navigate('/about')}
                className={`text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
                  location.pathname === '/about' ? 'text-indigo-600 dark:text-indigo-400 font-medium' : ''
                }`}
              >
                About
              </button>

            </nav>

            {/* Auth Section */}
            <div className="hidden md:block">
              {authState.isAuthenticated ? (
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                    className="flex items-center space-x-2 text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                  >
                    <DiscordAvatar
                      discord_id={authState.discordUser?.discord_id}
                      discord_avatar={authState.discordUser?.avatar}
                      discord_handle={authState.discordUser?.username}
                      size="md"
                      variant="light"
                      className="border border-gray-300 dark:border-gray-700"
                    />
                    <ChevronDown className="h-4 w-4 text-gray-500" />
                  </button>

                  {userDropdownOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-50 border border-gray-200 dark:border-gray-700">
                      <button
                        onClick={() => {
                          navigate('/profile')
                          setUserDropdownOpen(false)
                        }}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border-b border-gray-200 dark:border-gray-700"
                      >
                        {authState.discordUser?.username}
                      </button>
                      <button
                        onClick={() => {
                          handleLogout()
                          setUserDropdownOpen(false)
                        }}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        <LogOut className="h-4 w-4 mr-2" />
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <Button
                  onClick={() => navigate('/auth')}
                  size="sm"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white border-none"
                >
                  Connect
                </Button>
              )}
            </div>

            {/* Mobile menu button - positioned on far right */}
            <div className="flex items-center md:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
                aria-expanded="false"
              >
                {mobileMenuOpen ? (
                  <X className="h-6 w-6" aria-hidden="true" />
                ) : (
                  <Menu className="h-6 w-6" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation - Only show when menu is open */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="px-4 py-3 space-y-1">
            <button
              onClick={() => authState.isAuthenticated ? navigate('/submit') : navigate('/auth')}
              className={`flex items-center gap-2 w-full text-left px-3 py-2 text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
                location.pathname === '/submit' || location.pathname === '/auth' ? 'text-indigo-600 dark:text-indigo-400 font-medium bg-indigo-50 dark:bg-indigo-900/20 rounded-md' : ''
              }`}
            >
              <Plus className="h-4 w-4" />
              Submit
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className={`block w-full text-left px-3 py-2 text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
                location.pathname === '/dashboard' ? 'text-indigo-600 dark:text-indigo-400 font-medium bg-indigo-50 dark:bg-indigo-900/20 rounded-md' : ''
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => navigate('/gallery')}
              className={`flex items-center gap-2 w-full text-left px-3 py-2 text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
                location.pathname === '/gallery' ? 'text-indigo-600 dark:text-indigo-400 font-medium bg-indigo-50 dark:bg-indigo-900/20 rounded-md' : ''
              }`}
            >
              <Camera className="h-4 w-4" />
              Gallery
            </button>
            <button
              onClick={() => navigate('/about')}
              className={`block w-full text-left px-3 py-2 text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ${
                location.pathname === '/about' ? 'text-indigo-600 dark:text-indigo-400 font-medium bg-indigo-50 dark:bg-indigo-900/20 rounded-md' : ''
              }`}
            >
              About
            </button>
            {/* Mobile Auth Section */}
            {authState.isAuthenticated ? (
                <div className="border-t border-gray-200 dark:border-gray-700 pt-2 mt-2">
                <button
                  onClick={() => {
                    navigate('/profile')
                    setMobileMenuOpen(false)
                  }}
                  className="flex items-center w-full px-3 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
                >
                  <DiscordAvatar
                    discord_id={authState.discordUser?.discord_id}
                    discord_avatar={authState.discordUser?.avatar}
                    discord_handle={authState.discordUser?.username}
                    size="sm"
                    variant="light"
                    className="border border-gray-300 dark:border-gray-700 mr-2"
                  />
                  <span className="text-sm">{authState.discordUser?.username}</span>
                </button>
                <button
                  onClick={() => {
                    handleLogout()
                    setMobileMenuOpen(false)
                  }}
                  className="flex items-center w-full text-left px-3 py-2 text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Logout
                </button>
              </div>
            ) : (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-2 mt-2">
                <button
                  onClick={() => navigate('/auth')}
                  className="w-full text-left px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md font-medium transition-colors"
                >
                  Connect
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  )
} 