// src/components/PatientModal.jsx
import { useEffect, useState } from 'react'
import { X, User, Activity, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react'
import Spinner from './Spinner'

const API = 'http://127.0.0.1:5000/api'

function InfoRow({ label, value }) {
  if (value === null || value === undefined || value === '') return null
  return (
    <div className="flex items-start gap-2 py-1.5 border-b border-slate-50 last:border-0">
      <span className="text-xs text-slate-400 w-40 shrink-0">{label}</span>
      <span className="text-xs font-medium text-slate-700">{String(value)}</span>
    </div>
  )
}

export default function PatientModal({ patientId, onClose }) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    if (!patientId) return
    setLoading(true); setError(null)
    fetch(`${API}/patient/${encodeURIComponent(patientId)}`)
      .then(r => r.json())
      .then(d => {
        if (d.error) throw new Error(d.error)
        setData(d)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [patientId])

  // Close on backdrop click
  const onBackdrop = e => { if (e.target === e.currentTarget) onClose() }

  return (
    <div
      onClick={onBackdrop}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col animate-fade-up">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-brand-500" />
            <span className="font-semibold text-slate-800 text-sm">Patient Details</span>
            {patientId && (
              <span className="ml-2 px-2 py-0.5 bg-brand-50 text-brand-700 rounded-lg text-xs font-mono font-semibold">
                {patientId}
              </span>
            )}
          </div>
          <button onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-slate-400 hover:text-slate-700">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {loading && (
            <div className="flex items-center justify-center py-16">
              <Spinner size="lg" />
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
              <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
            </div>
          )}

          {!loading && !error && data && (
            <div className="space-y-6">

              {/* Patient Information */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <User className="w-3.5 h-3.5 text-brand-500" />
                  <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Patient Information</span>
                </div>
                <div className="bg-slate-50 rounded-xl px-4 py-2">
                  <InfoRow label="Patient ID"         value={data.patient.patient_id} />
                  <InfoRow label="Age"                value={data.patient.age} />
                  <InfoRow label="Gender"             value={data.patient.gender} />
                  <InfoRow label="Hypertension"       value={data.patient.hypertension === 1 ? 'Yes' : 'No'} />
                  <InfoRow label="Heart Disease"      value={data.patient.heart_disease === 1 ? 'Yes' : 'No'} />
                  <InfoRow label="Ever Married"       value={data.patient.ever_married} />
                  <InfoRow label="Work Type"          value={data.patient.work_type} />
                  <InfoRow label="Residence Type"     value={data.patient.residence_type} />
                  <InfoRow label="Avg Glucose Level"  value={data.patient.avg_glucose_level ? `${data.patient.avg_glucose_level} mg/dL` : null} />
                  <InfoRow label="BMI"                value={data.patient.bmi} />
                  <InfoRow label="Smoking Status"     value={data.patient.smoking_status} />
                  <InfoRow label="First Recorded"     value={data.patient.created_at} />
                </div>
              </div>

              {/* Latest Prediction Summary */}
              {data.prediction_history?.length > 0 && (() => {
                const latest = data.prediction_history[0]
                const isStroke = latest.prediction === 'Stroke'
                return (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Activity className="w-3.5 h-3.5 text-brand-500" />
                      <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Latest Prediction</span>
                    </div>
                    <div className={`rounded-xl p-4 border ${isStroke ? 'bg-red-50 border-red-100' : 'bg-emerald-50 border-emerald-100'}`}>
                      <div className="flex items-center gap-3">
                        {isStroke
                          ? <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
                          : <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />}
                        <div>
                          <div className={`font-bold text-base ${isStroke ? 'text-red-700' : 'text-emerald-700'}`}>
                            {latest.prediction}
                          </div>
                          <div className="text-xs text-slate-500 mt-0.5">
                            Risk: <strong>{latest.risk_score}%</strong> · Model: {latest.model} · Source: {latest.source} · {latest.date}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })()}

              {/* Prediction History */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Clock className="w-3.5 h-3.5 text-brand-500" />
                  <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
                    Prediction History ({data.prediction_history?.length ?? 0})
                  </span>
                </div>

                {!data.prediction_history?.length ? (
                  <div className="text-center py-6 text-slate-400 text-xs">No prediction history found.</div>
                ) : (
                  <div className="overflow-x-auto rounded-xl border border-slate-100">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-100">
                          {['Date & Time', 'Model', 'Risk %', 'Prediction', 'Source'].map(h => (
                            <th key={h} className="px-3 py-2.5 text-left font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {data.prediction_history.map((h, i) => (
                          <tr key={i} className="hover:bg-slate-50 transition-colors">
                            <td className="px-3 py-2.5 text-slate-500 whitespace-nowrap">{h.date || '—'}</td>
                            <td className="px-3 py-2.5 text-slate-600 font-medium">{h.model}</td>
                            <td className="px-3 py-2.5 font-semibold text-slate-700">{h.risk_score}%</td>
                            <td className="px-3 py-2.5">
                              <span className={`px-2 py-0.5 rounded-md font-semibold ${
                                h.prediction === 'Stroke'
                                  ? 'bg-red-50 text-red-700'
                                  : 'bg-emerald-50 text-emerald-700'
                              }`}>
                                {h.prediction}
                              </span>
                            </td>
                            <td className="px-3 py-2.5">
                              <span className={`px-2 py-0.5 rounded-md text-[10px] font-medium ${
                                h.source?.toLowerCase() === 'batch'
                                  ? 'bg-purple-50 text-purple-600'
                                  : 'bg-brand-50 text-brand-600'
                              }`}>
                                {h.source}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-100 flex justify-end">
          <button onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}