import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, ExternalLink } from 'lucide-react'
import { useSubmissionCache } from '../hooks/useSubmissionCache'

interface SubmissionModalProps {
  submissionId: number
  onClose: () => void
  onNavigate?: (direction: 'prev' | 'next') => void
  allSubmissionIds?: number[]
}

export function SubmissionModal({ submissionId, onClose, onNavigate, allSubmissionIds }: SubmissionModalProps) {
  const navigate = useNavigate()
  const { prefetchSubmissions } = useSubmissionCache()

  // Prefetch adjacent submissions for faster navigation
  useEffect(() => {
    if (allSubmissionIds && allSubmissionIds.length > 1) {
      const currentIndex = allSubmissionIds.indexOf(submissionId)
      if (currentIndex !== -1) {
        // Get next/prev submission IDs
        const nextIndex = currentIndex < allSubmissionIds.length - 1 ? currentIndex + 1 : 0
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : allSubmissionIds.length - 1
        const adjacentIds = [allSubmissionIds[nextIndex].toString(), allSubmissionIds[prevIndex].toString()]
        
        // Prefetch adjacent submissions
        prefetchSubmissions(adjacentIds)
      }
    }
  }, [submissionId, allSubmissionIds, prefetchSubmissions])

  // Keyboard navigation
  useEffect(() => {
    const handleKeydown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      } else if (e.key === 'ArrowLeft' && onNavigate) {
        onNavigate('prev')
      } else if (e.key === 'ArrowRight' && onNavigate) {
        onNavigate('next')
      }
    }

    document.addEventListener('keydown', handleKeydown)
    return () => document.removeEventListener('keydown', handleKeydown)
  }, [onClose, onNavigate])

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  const handleViewFullPage = () => {
    navigate(`/submission/${submissionId}`, { state: { from: 'dashboard' } })
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4" 
      onClick={handleBackdropClick}
    >
      <div 
        className="bg-white dark:bg-gray-900 rounded-lg shadow-2xl w-full h-full max-w-[85vw] max-h-[85vh] overflow-hidden flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Submission Details
            </h2>
            {onNavigate && (
              <div className="text-xs text-gray-500 dark:text-gray-400">
                <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs">←</kbd>
                <span className="mx-1">Previous</span>
                <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs">→</kbd>
                <span className="mx-1">Next</span>
                <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs">Esc</kbd>
                <span className="mx-1">Close</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleViewFullPage}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
            >
              <ExternalLink className="h-4 w-4" />
              View Full Page
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              aria-label="Close modal"
            >
              <X className="h-5 w-5 text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        </div>
        
        {/* Iframe Content */}
        <iframe 
          src={`/submission/${submissionId}?modal=true`} 
          className="flex-1 w-full border-0 bg-white dark:bg-gray-900"
          title="Submission Details"
        />
      </div>
    </div>
  )
}