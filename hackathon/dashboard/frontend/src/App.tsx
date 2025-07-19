import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './contexts/AuthContext'
import { SolanaProvider } from './components/SolanaProvider'
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
import VotingPrototypes from './pages/VotingPrototypes'

function App() {
  return (
    <SolanaProvider>
      <AuthProvider>
        <Router>
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Header />
            <main className="pt-6">
            <Routes>
              <Route path="/" element={<Frontpage />} />
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/auth/discord/callback" element={<DiscordCallback />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route path="/submission/:id" element={<SubmissionDetail />} />
              <Route path="/voting-prototypes" element={<VotingPrototypes />} />
              
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
          <Toaster
            position="bottom-right"
            toastOptions={TOAST_OPTIONS}
          />
        </div>
      </Router>
    </AuthProvider>
  </SolanaProvider>
  )
}

export default App