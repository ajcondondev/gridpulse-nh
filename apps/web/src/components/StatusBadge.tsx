import type { SourceStatus } from '../types/source'

const statusConfig: Record<SourceStatus, { label: string; classes: string; title: string }> = {
  active: {
    label: 'Active',
    classes: 'bg-emerald-100 text-emerald-800',
    title: 'Live data — works now with no special setup',
  },
  test_fixture_only: {
    label: 'Test Only',
    classes: 'bg-blue-100 text-blue-800',
    title: 'Synthetic data — for automated tests and local dev only, not shown in production',
  },
  requires_key: {
    label: 'Requires Key',
    classes: 'bg-amber-100 text-amber-800',
    title: 'Connector is implemented but needs an API key configured in .env',
  },
  manual_import: {
    label: 'Manual Import',
    classes: 'bg-purple-100 text-purple-800',
    title: 'User must download and import the file manually',
  },
  planned: {
    label: 'Planned',
    classes: 'bg-gray-100 text-gray-600',
    title: 'Connector is planned but not yet implemented',
  },
  research: {
    label: 'Evaluating',
    classes: 'bg-orange-100 text-orange-700',
    title: 'Source access is being evaluated — no confirmed stable API yet',
  },
  not_implemented: {
    label: 'Not Implemented',
    classes: 'bg-gray-100 text-gray-400',
    title: 'Catalog placeholder only — no connector has been built',
  },
}

interface Props {
  status: SourceStatus
}

export function StatusBadge({ status }: Props) {
  const cfg = statusConfig[status] ?? statusConfig.not_implemented
  return (
    <span
      title={cfg.title}
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap cursor-default ${cfg.classes}`}
    >
      {cfg.label}
    </span>
  )
}
