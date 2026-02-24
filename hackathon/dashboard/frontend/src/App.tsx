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
import Footer from './components/Footer'

// Non-critical routes - lazy load
const Leaderboard = lazy(() => import('./pages/Leaderboard'))
const SubmissionDetail = lazy(() => import('./pages/SubmissionDetail'))
const ResearchPage = lazy(() => import('./pages/ResearchPage.tsx'))
const SubmissionPage = lazy(() => import('./pages/SubmissionPage'))
const SubmissionEdit = lazy(() => import('./pages/SubmissionEdit'))
const ProfilePage = lazy(() => import('./pages/ProfilePage.tsx'))
const AuthPage = lazy(() => import('./pages/AuthPage'))
const ProtectedRoute = lazy(() => import('./components/ProtectedRoute'))
const DiscordCallback = lazy(() => import('./pages/DiscordCallback'))
const Gallery = lazy(() => import('./pages/Gallery'))
const About = lazy(() => import('./pages/About'))
const ApiDocs = lazy(() => import('./pages/ApiDocs'))

// Experimental routes - development only
const LeaderboardV1 = lazy(() => import('./pages/experimental/LeaderboardV1'))
const LeaderboardV2 = lazy(() => import('./pages/experimental/LeaderboardV2'))
const VotingPrototypes = lazy(() => import('./pages/experimental/VotingPrototypes'))
const Templates = lazy(() => import('./pages/experimental/Templates'))

function AppContent() {
  const location = useLocation()
  const searchParams = new URLSearchParams(location.search)
  const isInIframe = typeof window !== 'undefined' && window.self !== window.top
  const isModal = isInIframe ||
                  searchParams.get('modal') === 'true' ||
                  (location.pathname.startsWith('/profile') && searchParams.has('user'))

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {!isModal && <Header />}
      <main className={`flex-1 ${isModal ? "" : "pt-6"}`}>
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
          <Route path="/gallery" element={<Gallery />} />
          <Route path="/about" element={<About />} />
          <Route path="/api" element={<ApiDocs />} />
           <Route path="/p/:username" element={<ProfilePage />} />
           <Route path="/profile" element={<ProfilePage />} />
          <Route path="/submission/:id" element={<SubmissionDetail />} />
           <Route path="/submission/:id/research" element={<ResearchPage />} />
          
          {/* Experimental routes - development only */}
          {import.meta.env.DEV && (
            <>
              <Route path="/experimental/voting-prototypes" element={<VotingPrototypes />} />
              <Route path="/experimental/leaderboard-v1" element={<LeaderboardV1 />} />
              <Route path="/experimental/leaderboard-v2" element={<LeaderboardV2 />} />
              <Route path="/experimental/templates" element={<Templates />} />
            </>
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
      {!isModal && <Footer />}
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