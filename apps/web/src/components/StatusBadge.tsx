import type { SourceStatus } from '../types/source'

const statusConfig: Record<SourceStatus, { label: string; classes: string }> = {
  active: { label: 'Active', classes: 'bg-emerald-100 text-emerald-800' },
  mock: { label: 'Mock', classes: 'bg-blue-100 text-blue-800' },
  planned: { label: 'Planned', classes: 'bg-gray-100 text-gray-600' },
  unavailable: { label: 'Unavailable', classes: 'bg-red-100 text-red-700' },
}

interface Props {
  status: SourceStatus
}

export function StatusBadge({ status }: Props) {
  const cfg = statusConfig[status]
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${cfg.classes}`}
    >
      {cfg.label}
    </span>
  )
}
