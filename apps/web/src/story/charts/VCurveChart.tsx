import * as Plot from '@observablehq/plot'
import { useEffect, useRef, useState } from 'react'
import { tempDemandDaily, type Season } from '../../lib/processedData'

/**
 * Season palette validated with the dataviz six-checks script against a white
 * surface (CVD worst-adjacent ΔE 13.3, all ≥3:1 contrast). Identity is also
 * positionally redundant here — temperature (x) largely encodes season.
 */
export const SEASON_COLORS: Record<Season, string> = {
  winter: '#2a78d6',
  spring: '#008300',
  summer: '#e34948',
  fall: '#c98500',
}

/** Mean daily peak per 2°F temperature bin — traces the V silhouette. */
function binnedMeans(binWidth = 2): { temp: number; peak: number }[] {
  const bins = new Map<number, { sum: number; n: number }>()
  for (const d of tempDemandDaily) {
    const bin = Math.round(d.temp_avg_f / binWidth) * binWidth
    const entry = bins.get(bin) ?? { sum: 0, n: 0 }
    entry.sum += d.peak_mw
    entry.n += 1
    bins.set(bin, entry)
  }
  return [...bins.entries()]
    .filter(([, { n }]) => n >= 3)
    .map(([temp, { sum, n }]) => ({ temp, peak: sum / n }))
    .sort((a, b) => a.temp - b.temp)
}

export function VCurveChart() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(720)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width
      if (w) setWidth(Math.round(w))
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const trend = binnedMeans()
    const chart = Plot.plot({
      width,
      height: Math.max(360, Math.min(460, width * 0.55)),
      marginLeft: 52,
      marginBottom: 44,
      insetTop: 10,
      insetRight: 12,
      style: { fontSize: '12px', background: 'transparent', color: '#898781' },
      x: {
        label: 'Daily average temperature (°F)',
        labelAnchor: 'center',
        labelArrow: 'none',
        tickSize: 0,
      },
      y: {
        label: 'Daily peak demand (MW)',
        tickFormat: (d: number) => `${(d / 1000).toFixed(0)}k`,
        grid: true,
        tickSize: 0,
        nice: true,
        zero: false,
      },
      color: {
        domain: ['winter', 'spring', 'summer', 'fall'],
        range: [
          SEASON_COLORS.winter,
          SEASON_COLORS.spring,
          SEASON_COLORS.summer,
          SEASON_COLORS.fall,
        ],
        legend: true,
      },
      marks: [
        Plot.gridY({ stroke: '#e1e0d9', strokeOpacity: 1 }),
        Plot.dot(tempDemandDaily, {
          x: 'temp_avg_f',
          y: 'peak_mw',
          fill: 'season',
          r: 3.5,
          fillOpacity: 0.6,
          tip: true,
          channels: { date: 'date' },
          title: (d: (typeof tempDemandDaily)[number]) =>
            `${d.date}\n${d.temp_avg_f}°F avg\n${d.peak_mw.toLocaleString()} MW peak`,
        }),
        Plot.line(trend, {
          x: 'temp',
          y: 'peak',
          stroke: '#0b0b0b',
          strokeWidth: 2,
          curve: 'basis',
        }),
      ],
    })

    el.append(chart)
    return () => chart.remove()
  }, [width])

  return (
    <div
      ref={containerRef}
      role="img"
      aria-label="Scatter plot of daily average temperature versus daily peak electricity demand in ISO New England. Demand rises sharply on both cold and hot days, forming a V shape with its low point on mild days."
      data-testid="vcurve-chart"
    />
  )
}
