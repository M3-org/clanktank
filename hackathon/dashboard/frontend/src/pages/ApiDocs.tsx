import { useState } from 'react'
import Markdown from 'markdown-to-jsx'
import { toast } from 'react-hot-toast'

const markdownContent = `# API

Public read-only endpoints for the Clank Tank hackathon platform.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| \`GET\` | \`/api/submissions\` | List all submissions |
| \`GET\` | \`/api/submissions/{id}\` | Get submission detail by ID |
| \`GET\` | \`/api/leaderboard\` | Ranked leaderboard with scores |
| \`GET\` | \`/api/stats\` | Hackathon statistics |

## Notes

All endpoints return JSON. No authentication is required for read access.
`

const markdownOptions = {
  overrides: {
    h1: {
      props: {
        className: 'text-5xl md:text-6xl font-bold tracking-tight text-white text-center mb-4'
      }
    },
    h2: {
      component: ({ children }: any) => (
        <div className="mt-12 mb-6 first:mt-8">
          <h2 className="text-3xl font-bold text-white mb-4 relative">
            <span className="absolute -left-4 top-0 w-1 h-full bg-gradient-to-b from-indigo-400 to-blue-400 rounded-full"></span>
            {children}
          </h2>
        </div>
      )
    },
    p: {
      component: ({ children }: any) => {
        const isSubtitle = typeof children === 'string' && children.includes('Public read-only')
        if (isSubtitle) {
          return (
            <p className="text-xl md:text-2xl text-gray-300 text-center mb-8 max-w-3xl mx-auto leading-relaxed">
              {children}
            </p>
          )
        }
        return (
          <p className="text-lg leading-relaxed text-gray-300 mb-6">
            {children}
          </p>
        )
      }
    },
    table: {
      props: {
        className: 'w-full mb-8 border-collapse rounded-lg overflow-hidden'
      }
    },
    thead: {
      props: {
        className: 'bg-gray-700'
      }
    },
    th: {
      props: {
        className: 'text-left px-4 py-3 text-sm font-semibold text-gray-200 border-b border-gray-600'
      }
    },
    td: {
      props: {
        className: 'px-4 py-3 text-sm text-gray-200 border-b border-gray-700 bg-gray-800'
      }
    },
    code: {
      props: {
        className: 'bg-gray-700 text-indigo-300 px-1.5 py-0.5 rounded text-sm font-mono'
      }
    },
    strong: {
      props: {
        className: 'font-semibold text-white'
      }
    }
  }
}

export default function ApiDocs() {
  const [copied, setCopied] = useState(false)

  const handleCopyMarkdown = async () => {
    await navigator.clipboard.writeText(markdownContent.trim())
    setCopied(true)
    toast.success('Markdown copied to clipboard!')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-4xl mx-auto px-6 py-16">
        {/* Copy button */}
        <div className="flex justify-end mb-4">
          <button
            onClick={handleCopyMarkdown}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white transition-colors shadow-sm"
          >
            {copied ? 'Copied!' : 'Copy as Markdown'}
          </button>
        </div>

        {/* Content */}
        <div className="mb-16">
          <Markdown options={markdownOptions}>
            {markdownContent}
          </Markdown>
        </div>
      </div>
    </div>
  )
}
