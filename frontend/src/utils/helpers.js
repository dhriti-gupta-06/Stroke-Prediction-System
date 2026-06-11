export function getRiskColor(risk) {
  switch (risk?.toLowerCase()) {
    case 'low':      return { text: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', hex: '#059669' }
    case 'moderate': return { text: 'text-amber-700',   bg: 'bg-amber-50',   border: 'border-amber-200',   hex: '#d97706' }
    case 'high':     return { text: 'text-orange-700',  bg: 'bg-orange-50',  border: 'border-orange-200',  hex: '#ea580c' }
    case 'critical': return { text: 'text-red-700',     bg: 'bg-red-50',     border: 'border-red-200',     hex: '#dc2626' }
    default:         return { text: 'text-slate-700',   bg: 'bg-slate-50',   border: 'border-slate-200',   hex: '#64748b' }
  }
}

export function getPredictionColor(pred) {
  return pred === 'Stroke'
    ? { text: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200' }
    : { text: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' }
}

export function cn(...classes) {
  return classes.filter(Boolean).join(' ')
}
