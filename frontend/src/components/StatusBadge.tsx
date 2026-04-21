import clsx from 'clsx'

const colors: Record<string, string> = {
  approved: 'bg-green-900 text-green-300',
  pending: 'bg-blue-900 text-blue-300',
  review: 'bg-yellow-900 text-yellow-300',
  flagged: 'bg-orange-900 text-orange-300',
  hold: 'bg-purple-900 text-purple-300',
  declined: 'bg-red-900 text-red-300',
  reversed: 'bg-gray-700 text-gray-300',
  open: 'bg-red-900 text-red-300',
  in_progress: 'bg-yellow-900 text-yellow-300',
  resolved: 'bg-green-900 text-green-300',
  false_positive: 'bg-gray-700 text-gray-300',
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx('px-2 py-0.5 rounded text-xs font-semibold capitalize', colors[status] || 'bg-gray-700 text-gray-300')}>
      {status}
    </span>
  )
}
