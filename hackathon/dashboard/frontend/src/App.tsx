import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Header from './components/Header'
import { lazy, Suspense } from 'react'

// Performance: Move static objects outside component
const TOAST_OPTIONS = {
  duration: 2000,
  style: {
    background: '#363636',
    color: '#fff',
  },
}

// Lazy load toast library to save 135ms execution time
const Toaster = lazy(() => import('react-hot-toast').then(module => ({ default: module.Toaster })))

// Critical routes - load immediately
import Dashboard from './pages/Dashboard'
import Frontpage from './pages/Frontpage'

// Non-critical routes - lazy load
const Leaderboard = lazy(() => import('./pages/Leaderboard'))
const SubmissionDetail = lazy(() => import('./pages/SubmissionDetail'))
const SubmissionPage = lazy(() => import('./pages/SubmissionPage'))
const SubmissionEdit = lazy(() => import('./pages/SubmissionEdit'))
const AuthPage = lazy(() => import('./pages/AuthPage'))
const ProtectedRoute = lazy(() => import('./components/ProtectedRoute'))
const DiscordCallback = lazy(() => import('./pages/DiscordCallback'))

function AppContent() {
  const location = useLocation()
  const searchParams = new URLSearchParams(location.search)
  const isModal = searchParams.get('modal') === 'true'

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {!isModal && <Header />}
      <main className={isModal ? "" : "pt-6"}>
        <Suspense fallback={
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        }>
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
        </Suspense>
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
        <Suspense fallback={null}>
          <Toaster
            position="bottom-right"
            toastOptions={TOAST_OPTIONS}
          />
        </Suspense>
      </Router>
    </AuthProvider>
  )
}

export default App