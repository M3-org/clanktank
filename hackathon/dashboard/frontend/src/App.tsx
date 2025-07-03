import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Leaderboard from './pages/Leaderboard'
import SubmissionDetail from './pages/SubmissionDetail'
import SubmissionPage from './pages/SubmissionPage'
import Frontpage from './pages/Frontpage'
import { Trophy, LayoutDashboard, Upload } from 'lucide-react'
import { cn } from './lib/utils'

function Navigation() {
  const location = useLocation()
  
  return (
    <nav className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Trophy className="h-8 w-8 text-indigo-600 mr-3" />
              <Link to="/">
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 hover:text-indigo-700 dark:hover:text-indigo-400 transition-colors">Clank Tank Hackathon</h1>
              </Link>
            </div>
            <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
              <Link
                to="/dashboard"
                className={cn(
                  "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors",
                  location.pathname === "/dashboard" 
                    ? "border-indigo-500 text-gray-900 dark:text-gray-100" 
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-200"
                )}
              >
                <LayoutDashboard className="h-4 w-4 mr-2" />
                Dashboard
              </Link>
              <Link
                to="/leaderboard"
                className={cn(
                  "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors",
                  location.pathname === "/leaderboard"
                    ? "border-indigo-500 text-gray-900 dark:text-gray-100"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-200"
                )}
              >
                <Trophy className="h-4 w-4 mr-2" />
                Leaderboard
              </Link>
              <Link
                to="/submit"
                className={cn(
                  "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors",
                  location.pathname === "/submit"
                    ? "border-indigo-500 text-gray-900 dark:text-gray-100"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-200"
                )}
              >
                <Upload className="h-4 w-4 mr-2" />
                Submit Project
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <Navigation />
        
        {/* Main Content */}
        <main className="py-8">
          <Routes>
            <Route path="/" element={<Frontpage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/submission/:id" element={<SubmissionDetail />} />
            <Route path="/submit" element={<SubmissionPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App