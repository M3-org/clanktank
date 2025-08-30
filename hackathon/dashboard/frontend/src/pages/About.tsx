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
      component: ({ children, ...props }: any) => (
        <div className="mt-16 mb-8 first:mt-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4 relative">
            <span className="absolute -left-4 top-0 w-1 h-full bg-gradient-to-b from-emerald-500 to-teal-500 rounded-full"></span>
            {children}
          </h2>
        </div>
      )
    },
    p: {
      component: ({ children, ...props }: any) => {
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
        <section className="mb-16">
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

        {/* Divider */}
        <div className="border-t border-gray-200 dark:border-gray-700 my-12"></div>

        {/* Links Section */}
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-6">Links & Resources</h2>
          
          <div className="grid gap-4 sm:grid-cols-2">
            <a
              href="https://mirror.xyz/m3org.eth/VU_Pl00hI7vRkCQPQg73Mg8906elnkvbaEvM1E2zZaE"
              target="_blank"
              rel="noopener noreferrer"
              className="group p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 transition-colors duration-200"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100 group-hover:text-blue-700 dark:group-hover:text-blue-300">
                    Full Story on Mirror
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Read the complete origin story and vision
                  </p>
                </div>
                <svg className="w-4 h-4 text-gray-400 group-hover:text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </div>
            </a>

            <a
              href="http://127.0.0.1:8082/clanktank/"
              target="_blank"
              rel="noopener noreferrer"
              className="group p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-emerald-300 dark:hover:border-emerald-600 transition-colors duration-200"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100 group-hover:text-emerald-700 dark:group-hover:text-emerald-300">
                    Technical Documentation
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Architecture, APIs, and development guides
                  </p>
                </div>
                <svg className="w-4 h-4 text-gray-400 group-hover:text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </a>
          </div>
        </div>

      </div>
    </div>
  )
}
