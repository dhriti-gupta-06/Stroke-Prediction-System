import { useEffect, useState } from 'react'
import { getMetrics, getPredictions } from '../services/api'
import PageHeader from '../components/PageHeader'
import Spinner from '../components/Spinner'
import { Search, ChevronLeft, ChevronRight as ChevRight } from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'

const METRIC_KEYS = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']
const TAB_KEYS = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']
const METRIC_LABELS = { accuracy: 'Accuracy', precision: 'Precision', recall: 'Recall', f1_score: 'F1 Score', roc_auc: 'ROC-AUC', confusion_matrix: 'Confusion Matrix' }

const BAR_COLOR = '#0a78ed'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg p-3 text-xs">
      <div className="font-semibold text-slate-700 mb-1.5">{label}</div>
      {payload.map(p => (
        <div key={p.name} className="flex justify-between gap-4">
          <span className="text-slate-500">{p.name}</span>
          <span className="font-semibold" style={{ color: p.color }}>{p.value}%</span>
        </div>
      ))}
    </div>
  )
}

const SHORT = n => n.replace('Random Forest + SMOTE', 'RF+SMOTE').replace('Random Forest', 'RF')
  .replace('Logistic Regression', 'LogReg').replace('Decision Tree', 'DecTree')

export default function Analytics() {
  const [data, setData]     = useState([])
  const [loading, setLoad]  = useState(true)
  const [activeMetric, setActiveMetric] = useState('roc_auc')
  

  // Records table state
  const [records, setRecords]     = useState([])
  const [recPage, setRecPage]     = useState(1)
  const [recTotal, setRecTotal]   = useState(0)
  const [recPages, setRecPages]   = useState(1)
  const [recSearch, setRecSearch] = useState('')
  const [recFilter, setRecFilter] = useState('')
  const [recLoading, setRecLoad]  = useState(false)

  useEffect(() => {
    getMetrics()
      .then(d => setData(d))
      .finally(() => setLoad(false))
  }, [])

  useEffect(() => {
    setRecLoad(true)
    getPredictions({ page: recPage, search: recSearch, prediction: recFilter })
      .then(d => { setRecords(d.records || []); setRecTotal(d.total || 0); setRecPages(d.pages || 1) })
      .catch(() => {})
      .finally(() => setRecLoad(false))
  }, [recPage, recSearch, recFilter])

  if (loading) return <div className="flex-1 flex items-center justify-center"><Spinner size="lg" /></div>

  const barData = data.map(m => ({
    name: SHORT(m.model),
    fullName: m.model,
    [METRIC_LABELS[activeMetric]]: m[activeMetric],
    prod: m.is_production
  }))
  

  const downloadCSV = async () => {
    const res = await fetch("http://127.0.0.1:5000/api/download-metrics")
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a"); a.href = url; a.download = "model_analytics.csv"; a.click()
  }

  const downloadStrokePDF = async (formData) => {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/download-stroke-pdf", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formData)
      })
      if (!response.ok) { const err = await response.json(); throw new Error(err.error || "Failed to generate PDF") }
      const blob = await response.blob()
      if (blob.type !== "application/pdf") throw new Error("Invalid PDF response from server")
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a"); a.href = url; a.download = "stroke_risk_report.pdf"
      document.body.appendChild(a); a.click(); a.remove(); window.URL.revokeObjectURL(url)
    } catch (error) { alert("Failed to download PDF: " + error.message) }
  }

  return (
    <div className="flex-1 p-6 max-w-6xl mx-auto w-full animate-fade-up">
      <div className="flex justify-between items-center mb-6">
        <PageHeader title="Model Analytics" subtitle="Performance comparison of all 7 trained models" />
        <button onClick={downloadCSV} className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition">Download CSV</button>
        <button
          onClick={() => {
            const payload = JSON.parse(localStorage.getItem("patientData") || "{}")
            const result  = JSON.parse(localStorage.getItem("predictionResult") || "{}")
            if (!payload || Object.keys(payload).length === 0) { alert("No patient data found. Please run prediction first."); return }
            downloadStrokePDF({ ...payload, prediction: result.final_prediction, probability: result.probability, risk_level: result.risk_level })
          }}
          className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition"
        >Download PDF</button>
      </div>

      {/* Metric tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {TAB_KEYS.map(k => (
          <button key={k} onClick={() => setActiveMetric(k)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-150 ${
              activeMetric === k ? 'bg-brand-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-brand-300'
            }`}>{METRIC_LABELS[k]}</button>
        ))}
      </div>

      <div className="card p-5 mb-6">
      <div className="font-semibold text-slate-800 text-sm mb-4">
        {METRIC_LABELS[activeMetric]} by Model
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={barData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />

          <XAxis
            dataKey="name"
            tick={{ fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />

          <YAxis
            domain={[0, 100]}
            unit="%"
            axisLine={false}
            tickLine={false}
          />

          <Tooltip content={<CustomTooltip />} />

          <Bar
            dataKey={METRIC_LABELS[activeMetric]}
            fill="#0a78ed"
            radius={[6, 6, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
      {/* ── Prediction Records Table (dynamic from SQL) ── */}
      <div className="card overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 font-semibold text-slate-800 text-sm flex items-center gap-3 flex-wrap">
          Prediction Records
          <span className="text-xs text-slate-400 font-normal">{recTotal} total records</span>
          <div className="ml-auto flex gap-2 flex-wrap">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                value={recSearch}
                onChange={e => { setRecSearch(e.target.value); setRecPage(1) }}
                placeholder="Search patient…"
                className="pl-8 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-brand-400 w-40"
              />
            </div>
            <select
              value={recFilter}
              onChange={e => { setRecFilter(e.target.value); setRecPage(1) }}
              className="text-xs border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:border-brand-400"
            >
              <option value="">All Predictions</option>
              <option value="Stroke">Stroke</option>
              <option value="No Stroke">No Stroke</option>
            </select>
          </div>
        </div>

        {recLoading ? (
          <div className="flex items-center justify-center py-12"><Spinner /></div>
        ) : records.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">No records saved yet. Use Save Data on the Patient Analysis page.</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100">
                    {['ID','Patient ID','Age','Gender','Prediction','Probability','LR','DT','RF','RF+S','XGB','Cat','LGB','Timestamp'].map(h => (
                      <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {records.map(r => (
                    <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-3 py-2.5 font-mono text-xs text-slate-500">{r.id}</td>
                      <td className="px-3 py-2.5 text-xs text-slate-600">{r.patient_id || '—'}</td>
                      <td className="px-3 py-2.5 text-xs text-slate-600">{r.age}</td>
                      <td className="px-3 py-2.5 text-xs text-slate-600">{r.gender}</td>
                      <td className="px-3 py-2.5">
                        <span className={`badge text-[10px] ${r.final_prediction === 'Stroke' ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}>
                          {r.final_prediction}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-xs font-semibold text-slate-600">{r.probability}%</td>
                      {['pred_logistic_regression','pred_decision_tree','pred_random_forest','pred_random_forest_smote','pred_xgboost','pred_catboost','pred_lightgbm'].map(k => (
                        <td key={k} className="px-3 py-2.5">
                          <span className={`text-[10px] font-medium ${r[k] === 'Stroke' ? 'text-red-600' : 'text-emerald-600'}`}>
                            {r[k] ? (r[k] === 'Stroke' ? '✕' : '✓') : '—'}
                          </span>
                        </td>
                      ))}
                      <td className="px-3 py-2.5 text-[10px] text-slate-400 whitespace-nowrap">
                        {r.timestamp ? new Date(r.timestamp).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* Pagination */}
            <div className="flex items-center justify-between px-5 py-3 border-t border-slate-100">
              <span className="text-xs text-slate-400">Page {recPage} of {recPages}</span>
              <div className="flex gap-2">
                <button onClick={() => setRecPage(p => Math.max(1, p - 1))} disabled={recPage === 1}
                  className="p-1.5 rounded-lg border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition-colors">
                  <ChevronLeft className="w-3.5 h-3.5 text-slate-600" />
                </button>
                <button onClick={() => setRecPage(p => Math.min(recPages, p + 1))} disabled={recPage === recPages}
                  className="p-1.5 rounded-lg border border-slate-200 disabled:opacity-40 hover:bg-slate-50 transition-colors">
                  <ChevRight className="w-3.5 h-3.5 text-slate-600" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}