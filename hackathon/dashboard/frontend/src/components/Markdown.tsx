import MarkdownToJSX from 'markdown-to-jsx'
import DOMPurify from 'dompurify'

function sanitizeInput(input: string): string {
  // Strip ALL raw HTML. We only want Markdown to be interpreted.
  // This removes event handlers, inline scripts, and dangerous HTML constructs.
  return DOMPurify.sanitize(input, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] })
}

function isSafeUrl(url?: string | null): boolean {
  if (!url) return false
  try {
    const parsed = new URL(url, window.location.origin)
    const protocol = parsed.protocol.toLowerCase()
    return protocol === 'http:' || protocol === 'https:'
  } catch {
    return false
  }
}

export function Markdown({ content, className }: { content?: string | null; className?: string }) {
  if (!content) return null
  const safe = sanitizeInput(content)
  return (
    <div className={className}>
      <MarkdownToJSX
        options={{
          forceBlock: true,
          // markdown-to-jsx escapes raw HTML by default; we additionally strip ALL HTML with DOMPurify
          overrides: {
            a: {
              component: (props: any) => {
                const href = typeof props.href === 'string' && isSafeUrl(props.href) ? props.href : undefined
                return (
                  <a {...props} href={href} target="_blank" rel="noopener noreferrer">
                    {props.children}
                  </a>
                )
              }
            },
            img: {
              component: (props: any) => {
                const src = typeof props.src === 'string' && isSafeUrl(props.src) ? props.src : undefined
                if (!src) return null
                return <img {...props} src={src} loading="lazy" referrerPolicy="no-referrer" />
              }
            }
          }
        }}
      >
        {safe}
      </MarkdownToJSX>
    </div>
  )
}


