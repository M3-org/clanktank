import MarkdownToJSX from 'markdown-to-jsx'

function sanitizeInput(input: string): string {
  // Remove script tags and their content (defense-in-depth)
  const withoutScripts = input.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
  return withoutScripts
}

export function Markdown({ content, className }: { content?: string | null; className?: string }) {
  if (!content) return null
  const safe = sanitizeInput(content)
  return (
    <div className={className}>
      <MarkdownToJSX
        options={{
          forceBlock: true,
          // markdown-to-jsx escapes raw HTML by default; we also stripped <script> for safety
          overrides: {
            a: {
              props: {
                target: '_blank',
                rel: 'noopener noreferrer'
              }
            },
            img: {
              props: {
                loading: 'lazy',
                referrerPolicy: 'no-referrer'
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


