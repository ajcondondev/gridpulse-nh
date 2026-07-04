import type { ReactNode } from 'react'

interface ChartCardProps {
  /** Claim-style title: says what the chart shows, not what it is. */
  title: string
  subtitle?: string
  source: string
  caveat?: string
  children: ReactNode
}

/**
 * Standard frame for every story chart: claim title, subtitle, the chart,
 * then source + caveat in the footer. Keeps the story page honest and
 * consistent (see .local-plan/04-visualization-plan.md).
 */
export function ChartCard({ title, subtitle, source, caveat, children }: ChartCardProps) {
  return (
    <figure className="bg-white border border-slate-200 rounded-xl shadow-sm p-5 sm:p-7">
      <figcaption>
        <h3 className="text-lg sm:text-xl font-semibold text-slate-900 tracking-tight">
          {title}
        </h3>
        {subtitle && <p className="text-sm text-slate-500 mt-1">{subtitle}</p>}
      </figcaption>
      <div className="mt-4">{children}</div>
      <div className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-400 space-y-0.5">
        <p>Source: {source}</p>
        {caveat && <p>{caveat}</p>}
      </div>
    </figure>
  )
}
