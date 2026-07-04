import * as Plot from '@observablehq/plot'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import eventWindowJson from '@data/event_window.json'
import {
  FUEL_COLORS,
  FUEL_ORDER,
  GRID_HAIRLINE,
  INK_MUTED,
  formatLocalHour,
  useContainerWidth,
} from '../chartTheme'

interface EventHour {
  ts_utc: string
  demand_mw: number
  temp_f: number | null
  // share_<fuel> columns plus the derived ts.
  [key: string]: string | number | null | Date
}

interface EventAnnotation {
  ts_utc: string
  title: string
  text: string
}

interface EventWindow {
  kind: string
  start_date: string
  end_date: string
  hourly: EventHour[]
  annotations: EventAnnotation[]
}

const event = eventWindowJson as unknown as EventWindow

const hours: (EventHour & { ts: Date })[] = event.hourly.map((h) => ({
  ...h,
  ts: new Date(h.ts_utc),
}))

const fuelShares = hours.flatMap((h) =>
  FUEL_ORDER.map((fuel) => {
    const raw = h[`share_${fuel}`]
    return {
      ts: h.ts,
      fuel,
      share: typeof raw === 'number' ? raw : 0,
    }
  }),
)

const PANEL_MARGIN_LEFT = 52
const PANEL_MARGIN_RIGHT = 16
const PLAY_MS_PER_HOUR = 110

function panelStyle(width: number, height: number) {
  return {
    width,
    height,
    marginLeft: PANEL_MARGIN_LEFT,
    marginRight: PANEL_MARGIN_RIGHT,
    marginBottom: 4,
    marginTop: 24,
    style: { fontSize: '11px', background: 'transparent', color: INK_MUTED },
  }
}

export function EventReplay() {
  const { ref, width } = useContainerWidth()
  const chartsRef = useRef<HTMLDivElement>(null)
  const [index, setIndex] = useState(hours.length - 1)
  const [playing, setPlaying] = useState(false)
  const prefersReducedMotion = useReducedMotion()

  const current = hours[index]

  // x pixel position of the cursor, derived from Plot's own scale.
  const xScale = useMemo(() => {
    if (width <= 0) return null
    const probe = Plot.plot({
      ...panelStyle(width, 60),
      x: { type: 'utc', domain: [hours[0].ts, hours[hours.length - 1].ts] },
      marks: [],
    })
    const scale = probe.scale('x')
    probe.remove()
    return scale
  }, [width])

  const cursorX = xScale?.apply ? (xScale.apply(current.ts) as number) : null

  // Play loop.
  useEffect(() => {
    if (!playing) return
    const timer = window.setInterval(() => {
      setIndex((i) => {
        if (i >= hours.length - 1) {
          setPlaying(false)
          return i
        }
        return i + 1
      })
    }, PLAY_MS_PER_HOUR)
    return () => window.clearInterval(timer)
  }, [playing])

  const handleReplay = useCallback(() => {
    setIndex(0)
    setPlaying(true)
  }, [])

  // Render the three aligned panels once per width change.
  useEffect(() => {
    const el = chartsRef.current
    if (!el || width <= 0) return
    const xDomain: [Date, Date] = [hours[0].ts, hours[hours.length - 1].ts]

    const tempPanel = Plot.plot({
      ...panelStyle(width, 132),
      x: { type: 'utc', domain: xDomain, axis: null },
      y: { label: 'Temp (°F)', labelArrow: 'none', tickSize: 0, grid: true, nice: true, ticks: 4 },
      marks: [
        Plot.gridY({ stroke: GRID_HAIRLINE }),
        Plot.lineY(hours, { x: 'ts', y: 'temp_f', stroke: '#c98500', strokeWidth: 1.75 }),
      ],
    })

    const demandPanel = Plot.plot({
      ...panelStyle(width, 160),
      x: { type: 'utc', domain: xDomain, axis: null },
      y: {
        label: 'Demand (MW)',
        labelArrow: 'none',
        tickFormat: (d: number) => `${(d / 1000).toFixed(0)}k`,
        tickSize: 0,
        grid: true,
        nice: true,
        zero: false,
        ticks: 4,
      },
      marks: [
        Plot.gridY({ stroke: GRID_HAIRLINE }),
        Plot.lineY(hours, { x: 'ts', y: 'demand_mw', stroke: '#2a78d6', strokeWidth: 2 }),
      ],
    })

    const mixPanel = Plot.plot({
      ...panelStyle(width, 160),
      marginBottom: 28,
      x: { type: 'utc', domain: xDomain, tickSize: 0, label: null },
      y: {
        label: 'Fuel share',
        labelArrow: 'none',
        tickFormat: (d: number) => `${Math.round(d * 100)}%`,
        tickSize: 0,
        domain: [0, 1],
        ticks: 4,
      },
      color: { domain: [...FUEL_ORDER], range: FUEL_ORDER.map((f) => FUEL_COLORS[f]) },
      marks: [
        Plot.areaY(fuelShares, {
          x: 'ts',
          y: 'share',
          fill: 'fuel',
          order: [...FUEL_ORDER],
        }),
      ],
    })

    el.replaceChildren(tempPanel, demandPanel, mixPanel)
    return () => el.replaceChildren()
  }, [width])

  const oilShareRaw = current['share_oil']
  const oilShare = typeof oilShareRaw === 'number' ? oilShareRaw : 0
  const activeAnnotations = event.annotations.filter(
    (a) => new Date(a.ts_utc).getTime() <= current.ts.getTime(),
  )

  return (
    <div ref={ref} data-testid="event-replay">
      {/* HUD */}
      <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1 mb-3 tabular-nums">
        <span className="text-sm font-semibold text-slate-800 min-w-[11rem]">
          {formatLocalHour(current.ts_utc)}
        </span>
        <span className="text-sm text-slate-600">
          <span className="inline-block w-2.5 h-2.5 rounded-full mr-1.5 align-baseline" style={{ background: '#c98500' }} />
          {current.temp_f != null ? `${Math.round(current.temp_f)}°F` : '—'}
        </span>
        <span className="text-sm text-slate-600">
          <span className="inline-block w-2.5 h-2.5 rounded-full mr-1.5 align-baseline" style={{ background: '#2a78d6' }} />
          {current.demand_mw.toLocaleString()} MW
        </span>
        <span className="text-sm text-slate-600">
          <span className="inline-block w-2.5 h-2.5 rounded-full mr-1.5 align-baseline" style={{ background: FUEL_COLORS.oil }} />
          oil {Math.round(oilShare * 100)}%
        </span>
      </div>

      {/* Aligned panels + cursor overlay */}
      <div className="relative">
        <div ref={chartsRef} />
        {cursorX != null && (
          <div
            aria-hidden
            className="absolute top-0 bottom-7 w-px bg-slate-900/60 pointer-events-none"
            style={{ left: cursorX }}
          />
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 mt-2">
        <button
          type="button"
          onClick={() => (playing ? setPlaying(false) : index >= hours.length - 1 ? handleReplay() : setPlaying(true))}
          className="px-3 py-1.5 rounded-md bg-slate-900 text-white text-xs font-medium hover:bg-slate-700 transition-colors min-w-[4.5rem]"
          data-testid="replay-button"
        >
          {playing ? 'Pause' : index >= hours.length - 1 ? 'Replay' : 'Play'}
        </button>
        <input
          type="range"
          min={0}
          max={hours.length - 1}
          value={index}
          onChange={(e) => {
            setPlaying(false)
            setIndex(Number(e.target.value))
          }}
          className="flex-1 accent-slate-900"
          aria-label="Scrub through the event hour by hour"
        />
      </div>

      {/* Annotations */}
      <div className="mt-4 grid gap-2 sm:grid-cols-3" aria-live="polite">
        <AnimatePresence>
          {activeAnnotations.map((a) => (
            <motion.button
              key={a.ts_utc + a.title}
              type="button"
              initial={prefersReducedMotion ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={prefersReducedMotion ? undefined : { opacity: 0 }}
              transition={{ duration: 0.25 }}
              onClick={() => {
                setPlaying(false)
                const i = hours.findIndex((h) => h.ts_utc >= a.ts_utc)
                if (i >= 0) setIndex(i)
              }}
              className="text-left border border-slate-200 bg-slate-50 rounded-lg px-3 py-2 hover:border-slate-300 transition-colors"
            >
              <p className="text-xs font-semibold text-slate-800">{a.title}</p>
              <p className="text-xs text-slate-500 mt-0.5 leading-snug">{a.text}</p>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
