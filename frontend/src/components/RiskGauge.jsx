import { getRiskColor } from '../utils/helpers'

export default function RiskGauge({ probability, risk }) {
  const pct     = Math.min(Math.max(probability, 0), 100)
  const angle   = -135 + (pct / 100) * 270   // -135° to +135°
  const color   = getRiskColor(risk)
  const sectors = [
    { color: '#059669', label: 'Low',      start: -135, end: -67 },
    { color: '#d97706', label: 'Moderate', start: -67,  end: 0   },
    { color: '#ea580c', label: 'High',     start: 0,    end: 67  },
    { color: '#dc2626', label: 'Critical', start: 67,   end: 135 },
  ]

  // Arc path helper
  function arc(cx, cy, r, startDeg, endDeg) {
    const toRad = d => (d * Math.PI) / 180
    const x1 = cx + r * Math.cos(toRad(startDeg))
    const y1 = cy + r * Math.sin(toRad(startDeg))
    const x2 = cx + r * Math.cos(toRad(endDeg))
    const y2 = cy + r * Math.sin(toRad(endDeg))
    const large = endDeg - startDeg > 180 ? 1 : 0
    return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`
  }

  const cx = 100, cy = 90, r = 70
  const needleRad = ((angle) * Math.PI) / 180
  const nx = cx + (r - 8) * Math.cos(needleRad)
  const ny = cy + (r - 8) * Math.sin(needleRad)

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 120" className="w-48 h-auto">
        {/* Track */}
        <path d={arc(cx, cy, r, -135, 135)} fill="none" stroke="#e2e8f0" strokeWidth="14" strokeLinecap="round" />
        {/* Colored sectors */}
        {sectors.map(s => (
          <path key={s.label} d={arc(cx, cy, r, s.start, s.end)}
            fill="none" stroke={s.color} strokeWidth="14" strokeLinecap="butt" opacity="0.25" />
        ))}
        {/* Progress */}
        <path d={arc(cx, cy, r, -135, -135 + (pct / 100) * 270)}
          fill="none" stroke={color.hex} strokeWidth="14" strokeLinecap="round" />
        {/* Needle */}
        <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#1e293b" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r="5" fill="#1e293b" />
        {/* Value text */}
        <text x={cx} y={cy + 20} textAnchor="middle" fontSize="20" fontWeight="700" fill="#1e293b"
          fontFamily="Inter, sans-serif">{pct}%</text>
      </svg>
      <span className={`badge mt-1 ${color.bg} ${color.text} text-sm font-semibold px-3 py-1`}>{risk} Risk</span>
    </div>
  )
}
