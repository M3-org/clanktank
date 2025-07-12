import { Copy, Wallet, Check } from 'lucide-react'
import { Button } from './Button'
import { cn } from '../lib/utils'
import { useState } from 'react'

export default function PrizePoolBanner({
  total = 16.42,                // ETH
  goal  = 25,
  address = "0xDEAD...BEEF",
}: {
  total?: number
  goal?: number
  address?: string
}) {
  const pct = Math.min((total/goal)*100, 100)
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    await navigator.clipboard.writeText(address)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="mb-8 rounded-xl bg-gray-100/40 dark:bg-gray-800/40 px-6 py-4 backdrop-blur border border-gray-200/60 dark:border-gray-700/60">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Wallet className="h-5 w-5 opacity-70 text-gray-600 dark:text-gray-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Prize Pool&nbsp;
            <span className="font-semibold text-gray-900 dark:text-gray-100">{total.toFixed(2)} ETH</span>
          </span>
        </div>

        {/* Progress bar */}
        <div className="h-2 w-full sm:w-64 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>

        <Button size="sm" variant="secondary" onClick={copy} className="text-xs">
          {copied ? (
            <Check className="mr-2 h-3 w-3 text-green-600" />
          ) : (
            <Copy className="mr-2 h-3 w-3" />
          )}
          <span className="mr-1">Prize Pool:</span>
          <span className="font-mono">{address.slice(0, 5)}...{address.slice(-5)}</span>
        </Button>
      </div>
    </div>
  )
}