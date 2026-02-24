import { Link } from 'react-router-dom'
import Markdown from 'markdown-to-jsx'

// Import the markdown content directly
const markdownContent = `# About Clank Tank

An AI-powered game show where entrepreneurs pitch to simulated judges, competing for virtual funding and real attention.

## What It Is

Clank Tank transforms real business pitches into entertaining episodes featuring AI-generated characters, dialogue, and interactions. Inspired by "Shark Tank," our system creates complete show episodes that provide exposure for projects while offering AI-driven feedback.

## How It Works

1. **Submit Your Pitch** — Builders submit project details through our submission form
2. **AI Research** — Automated research and analysis of your project and market
3. **Episode Generation** — AI creates dialogue between judges and your virtual representative  
4. **3D Rendering** — Episodes are rendered as engaging video content
5. **Community Voting** — The community weighs in alongside AI judge scores

**The Result:** A crisp, distributable video that showcases your project and provides useful feedback.`

const markdownOptions = {
  overrides: {
    h1: {
      props: {
        className: 'text-5xl md:text-6xl font-bold tracking-tight text-gray-900 dark:text-gray-100 text-center mb-4'
      }
    },
    h2: {
      component: ({ children }: any) => (
        <div className="mt-16 mb-8 first:mt-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4 relative">
            <span className="absolute -left-4 top-0 w-1 h-full bg-gradient-to-b from-emerald-500 to-teal-500 rounded-full"></span>
            {children}
          </h2>
        </div>
      )
    },
    p: {
      component: ({ children }: any) => {
        // Check if this is the subtitle (first paragraph)
        const isSubtitle = typeof children === 'string' && children.includes('AI-powered game show')
        if (isSubtitle) {
          return (
            <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 text-center mb-8 max-w-3xl mx-auto leading-relaxed">
              {children}
            </p>
          )
        }
        return (
          <p className="text-lg leading-relaxed text-gray-700 dark:text-gray-300 mb-6">
            {children}
          </p>
        )
      }
    },
    ul: {
      props: {
        className: 'space-y-3 mb-8'
      }
    },
    ol: {
      props: {
        className: 'space-y-4 mb-8'
      }
    },
    li: {
      component: ({ children, ...props }: any) => {
        const isNumberedList = props.parentName === 'ol'
        if (isNumberedList) {
          return (
            <li className="flex gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-emerald-500">
              <div className="text-lg leading-relaxed text-gray-700 dark:text-gray-300">
                {children}
              </div>
            </li>
          )
        }
        return (
          <li className="flex items-start gap-3 text-gray-700 dark:text-gray-300">
            <span className="w-2 h-2 bg-emerald-500 rounded-full mt-2.5 flex-shrink-0"></span>
            <span className="text-lg leading-relaxed">{children}</span>
          </li>
        )
      }
    },
    strong: {
      props: {
        className: 'font-semibold text-gray-900 dark:text-gray-100'
      }
    },
    em: {
      props: {
        className: 'italic text-gray-700 dark:text-gray-300'
      }
    },
    a: {
      props: {
        className: 'text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline decoration-2 underline-offset-2 transition-colors duration-150',
        target: '_blank',
        rel: 'noopener noreferrer'
      }
    },
    hr: {
      props: {
        className: 'border-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-600 to-transparent my-16'
      }
    }
  }
}

export default function About() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-emerald-50 dark:from-gray-900 dark:via-gray-900 dark:to-emerald-950">
      <div className="max-w-4xl mx-auto px-6 py-16">
        
        {/* Content */}
        <div className="mb-16">
          <Markdown options={markdownOptions}>
            {markdownContent}
          </Markdown>
        </div>

        {/* Video Section */}
        <section className="mb-8">
          <div className="relative">
            {/* Decorative background */}
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-2xl blur-3xl transform -rotate-1"></div>
            
            {/* Video container */}
            <div className="relative aspect-video w-full rounded-2xl overflow-hidden bg-gray-900 shadow-2xl ring-1 ring-gray-200 dark:ring-gray-700">
              <iframe
                width="100%"
                height="100%"
                src="https://www.youtube.com/embed/n_g7VaO-zVE"
                title="Clank Tank Demo"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="w-full h-full"
              />
            </div>
            
            {/* Video caption */}
            <p className="text-center text-gray-600 dark:text-gray-400 mt-4 text-lg">
              The first trailer for Clank Tank
            </p>
          </div>
        </section>

        {/* API link */}
        <p className="text-center text-sm text-gray-500 dark:text-gray-400">
          Interested in our data? Check out the{' '}
          <Link to="/api" className="text-indigo-600 dark:text-indigo-400 hover:underline">
            API Documentation
          </Link>.
        </p>

      </div>
    </div>
  )
}
