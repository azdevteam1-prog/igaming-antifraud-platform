interface Props {
  title: string
  value: string | number
  sub?: string
  color?: string
}

export function KpiCard({ title, value, sub, color = 'text-white' }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-xs text-gray-400 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}
