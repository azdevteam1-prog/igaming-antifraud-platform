import clsx from 'clsx'

const colors: Record<string, string> = {
  Low: 'bg-green-900 text-green-300',
  Medium: 'bg-yellow-900 text-yellow-300',
  High: 'bg-orange-900 text-orange-300',
  Critical: 'bg-red-900 text-red-300',
}

export function RiskBadge({ label }: { label: string }) {
  return (
    <span className={clsx('px-2 py-0.5 rounded text-xs font-semibold', colors[label] || 'bg-gray-700 text-gray-300')}>
      {label}
    </span>
  )
}
