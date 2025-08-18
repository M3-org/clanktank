import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect, useState, useCallback } from 'react'
import { Card, CardContent, CardHeader } from '../components/Card'
import { Markdown } from '../components/Markdown'
import { hackathonApi } from '../lib/api'
import { FileText, Copy, ArrowLeft } from 'lucide-react'
import { useCopyToClipboard } from '../hooks/useCopyToClipboard'

export default function ResearchPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const isModal = searchParams.get('modal') === 'true'
  const [report, setReport] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const { copied, copyToClipboard } = useCopyToClipboard()

  const load = useCallback(async () => {
    if (!id) return
    try {
      const submission = await hackathonApi.getSubmission(id)
      const assessmentRaw = submission?.research?.technical_assessment
      const assessment = typeof assessmentRaw === 'string' ? (() => { try { return JSON.parse(assessmentRaw) } catch { return null } })() : assessmentRaw
      const githubRaw = submission?.research?.github_analysis
      const github = typeof githubRaw === 'string' ? (() => { try { return JSON.parse(githubRaw) } catch { return null } })() : githubRaw

      let md = ''
      if (github) {
        md += '# Repository Analysis\n\n'
        if (github.description) md += `**Description:** ${github.description}\n\n`
        if (github.file_structure) {
          md += `**Total Files:** ${github.file_structure.total_files || 0}\n\n`
          if (github.file_structure.file_extensions && Object.keys(github.file_structure.file_extensions).length > 0) {
            md += '**Technologies:**\n'
            Object.entries(github.file_structure.file_extensions)
              .sort(([,a], [,b]) => (b as number) - (a as number))
              .slice(0, 5)
              .forEach(([ext, count]) => { md += `- .${ext}: ${count} files\n` })
            md += '\n'
          }
        }
      }
      if (assessment) {
        const convert = (data: any, depth = 0): string => {
          if (!data) return ''
          if (typeof data === 'string') return data
          if (typeof data === 'number' || typeof data === 'boolean') return String(data)
          if (Array.isArray(data)) return data.map(v => `- ${convert(v, depth)}`).join('\n')
          let out = ''
          for (const [k, v] of Object.entries(data)) {
            if (v === null || v === undefined || v === '') continue
            const key = k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
            if (typeof v === 'object' && !Array.isArray(v)) {
              out += depth === 0 ? `## ${key}\n\n` : `**${key}:**\n\n`
              out += `${convert(v, depth + 1)}\n\n`
            } else if (Array.isArray(v)) {
              out += `**${key}:**\n${convert(v, depth + 1)}\n\n`
            } else {
              out += `**${key}:** ${convert(v, depth)}\n\n`
            }
          }
          return out.trim()
        }
        md += '# AI Research Analysis\n\n' + convert(assessment)
      }
      setReport(md || 'No research data available')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  if (loading) {
    return <div className="p-6 text-sm text-gray-500">Loading…</div>
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <Card className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  if (isModal) {
                    navigate(`/submission/${id}?modal=true`)
                  } else {
                    navigate(-1)
                  }
                }}
                className="inline-flex items-center gap-2 px-2 py-1 text-xs text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                title="Back"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              <h2 className="text-lg font-semibold flex items-center">
                <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
                Research
              </h2>
            </div>
            <button
              onClick={() => copyToClipboard(report)}
              className="flex items-center gap-2 px-3 py-1.5 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 bg-white dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-gray-700 rounded border border-gray-200 dark:border-gray-700"
            >
              <Copy className="h-4 w-4" />
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none dark:prose-invert break-words overflow-hidden">
            <Markdown content={report} />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}



