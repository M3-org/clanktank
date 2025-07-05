import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import Leaderboard from './pages/Leaderboard'
import SubmissionDetail from './pages/SubmissionDetail'
import SubmissionPage from './pages/SubmissionPage'
import SubmissionEdit from './pages/SubmissionEdit'
import Frontpage from './pages/Frontpage'
import AuthPage from './pages/AuthPage'
import ProtectedRoute from './components/ProtectedRoute'
import DiscordCallback from './pages/DiscordCallback'

function App() {
  return (
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
      </Router>
    </AuthProvider>
  )
}

export default App