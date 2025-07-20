import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './contexts/AuthContext'
import Header from './components/Header'

// Performance: Move static objects outside component
const TOAST_OPTIONS = {
  duration: 2000,
  style: {
    background: '#363636',
    color: '#fff',
  },
}

import Dashboard from './pages/Dashboard'
import Leaderboard from './pages/Leaderboard'
import SubmissionDetail from './pages/SubmissionDetail'
import SubmissionPage from './pages/SubmissionPage'
import SubmissionEdit from './pages/SubmissionEdit'
import Frontpage from './pages/Frontpage'
import AuthPage from './pages/AuthPage'
import ProtectedRoute from './components/ProtectedRoute'
import DiscordCallback from './pages/DiscordCallback'

function AppContent() {
  const location = useLocation()
  const searchParams = new URLSearchParams(location.search)
  const isModal = searchParams.get('modal') === 'true'

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {!isModal && <Header />}
      <main className={isModal ? "" : "pt-6"}>
        <Routes>
          <Route path="/" element={<Frontpage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/auth/discord/callback" element={<DiscordCallback />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/submission/:id" element={<SubmissionDetail />} />
          
          {/* Dev-only route - wallet functionality only in development */}
          {import.meta.env.DEV && (
            <Route path="/voting-prototypes" element={
              <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-lg text-gray-900 dark:text-gray-100 mb-2">Dev Only: Voting Prototypes</div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Wallet functionality available in development</div>
                </div>
              </div>
            } />
          )}
          
          {/* Protected Routes */}
          <Route path="/submit" element={
            <ProtectedRoute>
              <SubmissionPage />
            </ProtectedRoute>
          } />
          <Route path="/submission/:id/edit" element={
            <ProtectedRoute>
              <SubmissionEdit />
            </ProtectedRoute>
          } />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
        <Toaster
          position="bottom-right"
          toastOptions={TOAST_OPTIONS}
        />
      </Router>
    </AuthProvider>
  )
}

export default App