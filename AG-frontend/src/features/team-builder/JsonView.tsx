/**
 * JsonView - JSON viewer with syntax highlighting and copy-to-clipboard
 * Read-only display of team configuration JSON
 */

import { memo, useMemo, useState, useCallback, useRef, useEffect } from 'react'
import { Copy, Check } from 'lucide-react'
import { Button } from '@/shared/ui'

interface JsonViewProps {
  data: unknown
}

/** Escape HTML entities to prevent XSS in dangerouslySetInnerHTML */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

/** Simple regex-based JSON syntax highlighter (runs on escaped HTML) */
function highlightJson(json: string): string {
  return escapeHtml(json)
    // Strings (keys and values)
    .replace(
      /("(?:\\.|[^"\\])*")\s*:/g,
      '<span class="text-(--color-text-secondary) font-medium">$1</span>:',
    )
    .replace(
      /:\s*("(?:\\.|[^"\\])*")/g,
      ': <span class="text-(--color-accent-primary)">$1</span>',
    )
    // Standalone strings (in arrays)
    .replace(
      /(?<=[\[,]\s*)("(?:\\.|[^"\\])*")(?=\s*[,\]])/g,
      '<span class="text-(--color-accent-primary)">$1</span>',
    )
    // Numbers
    .replace(
      /:\s*(\d+\.?\d*)/g,
      ': <span class="text-amber-500">$1</span>',
    )
    // Booleans
    .replace(
      /:\s*(true|false)/g,
      ': <span class="text-amber-500">$1</span>',
    )
    // Null
    .replace(
      /:\s*(null)/g,
      ': <span class="text-(--color-text-tertiary)">$1</span>',
    )
}

export const JsonView = memo(function JsonView({ data }: JsonViewProps) {
  const [copied, setCopied] = useState(false)
  const copyTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  useEffect(() => {
    return () => clearTimeout(copyTimerRef.current)
  }, [])

  const jsonString = useMemo(
    () => JSON.stringify(data, null, 2),
    [data],
  )

  const highlighted = useMemo(
    () => highlightJson(jsonString),
    [jsonString],
  )

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(jsonString)
      setCopied(true)
      clearTimeout(copyTimerRef.current)
      copyTimerRef.current = setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard API unavailable in some environments
    }
  }, [jsonString])

  return (
    <div className="relative" aria-label="Team configuration JSON">
      <div className="absolute top-2 right-2 z-10">
        <Button
          size="sm"
          variant="ghost"
          onClick={handleCopy}
          aria-label="Copy JSON to clipboard"
        >
          {copied ? (
            <><Check className="w-3.5 h-3.5 mr-1" /><span>Copied!</span></>
          ) : (
            <><Copy className="w-3.5 h-3.5 mr-1" /><span>Copy</span></>
          )}
        </Button>
      </div>
      <pre
        className="p-4 pt-10 rounded-lg bg-(--color-background-secondary) text-xs font-mono max-h-[500px] overflow-y-auto overflow-x-auto border border-(--color-border-default)"
        dangerouslySetInnerHTML={{ __html: highlighted }}
      />
    </div>
  )
})
