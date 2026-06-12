import { useEffect, useState, useCallback } from 'react'
import { getPredictions } from '../services/api'
import PageHeader from '../components/PageHeader'
import Spinner from '../components/Spinner'
import PatientModal from '../components/PatientModal'
import { Search, ChevronLeft, ChevronRight as ChevRight } from 'lucide-react'




const SHORT = n =>
  n.replace('Random Forest + SMOTE', 'RF+SMOTE').replace('Random Forest', 'RF')
   .replace('Logistic Regression', 'LogReg').replace('Decision Tree', 'DecTree')



function InsightRow({ label, items, valueKey, labelKey = 'model', unit = '', color = 'text-brand-600' }) {
  if (!items?.length) return null
  return (
    <div>
      <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">{label}</div>
      <div className="flex flex-wrap gap-2">
        {items.map((item, i) => (
          <div key={i} className="bg-slate-50 border border-slate-100 rounded-xl px-3 py-2 text-center min-w-[80px]">
            <div className={`text-sm font-bold ${color}`}>{item[valueKey]}{unit}</div>
            <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">{SHORT(item[labelKey])}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Analytics() {


  const [adv,        setAdv]      = useState(null)
  const [advLoading, setAdvLoad]  = useState(true)

  const [records,    setRecords]   = useState([])
  const [recPage,    setRecPage]   = useState(1)
  const [recTotal,   setRecTotal]  = useState(0)
  const [recPages,   setRecPages]  = useState(1)
  const [recSearch,  setRecSearch] = useState('')
  const [recFilter,  setRecFilter] = useState('')
  const [recLoading, setRecLoad]   = useState(false)

  // ── Modal state ───────────────────────────────────────────────────────────
  const [modalPid, setModalPid] = useState(null)

  

  const fetchAdv = useCallback(() => {
    setAdvLoad(true)
    fetch('http://127.0.0.1:5000/api/advanced-metrics')
      .then(r => r.json()).then(d => setAdv(d)).catch(() => setAdv(null))
      .finally(() => setAdvLoad(false))
  }, [])
  useEffect(() => { fetchAdv() }, [fetchAdv])

  useEffect(() => {
    setRecLoad(true)
    getPredictions({ page: recPage, search: recSearch, prediction: recFilter })
      .then(d => { setRecords(d.records || []); setRecTotal(d.total || 0); setRecPages(d.pages || 1) })
      .catch(() => {})
      .finally(() => setRecLoad(false))
  }, [recPage, recSearch, recFilter])

  

  

  const downloadCSV = async () => {
    const res  = await fetch("http://127.0.0.1:5000/api/download-metrics")
    const blob = await res.blob()
    const url  = window.URL.createObjectURL(blob)
    const a    = document.createElement("a")
    a.href = url; a.download = "model_analytics.csv"; a.click()
  }

  const downloadStrokePDF = async (formData) => {
    try {
      const response = await fetch("http://127.0.0.1:5000/api/download-stroke-pdf", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formData),
      })
      if (!response.ok) { const err = await response.json(); throw new Error(err.error || "Failed to generate PDF") }
      const blob = await response.blob()
      if (blob.type !== "application/pdf") throw new Error("Invalid PDF response from server")
      const url = window.URL.createObjectURL(blob)
      const a   = document.createElement("a")
      a.href = url; a.download = "stroke_risk_report.pdf"
      document.body.appendChild(a); a.click(); a.remove(); window.URL.revokeObjectURL(url)
    } catch (error) { alert("Failed to download PDF: " + error.message) }
  }

  return (
    <div className="flex-1 p-6 max-w-6xl mx-auto w-full animate-fade-up">

      {/* Modal */}
      {modalPid && <PatientModal patientId={modalPid} onClose={() => setModalPid(null)} />}

      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <PageHeader title="Model Analytics" subtitle="Performance comparison of all 7 trained models" />
        <button onClick={downloadCSV}
          className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition">
          Download CSV
        </button>
        <button
          onClick={() => {
            const payload = JSON.parse(localStorage.getItem("patientData") || "{}")
            const result  = JSON.parse(localStorage.getItem("predictionResult") || "{}")
            if (!payload || Object.keys(payload).length === 0) {
              alert("No patient data found. Please run prediction first."); return
            }
            downloadStrokePDF({ ...payload, prediction: result.final_prediction,
              probability: result.probability, risk_level: result.risk_level })
          }}
          className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition"
        >Download PDF</button>
      </div>

      

      

      {/* Advanced Insights */}
      {!advLoading && adv && adv.total > 0 && (
        <div className="card p-5 mb-6 space-y-5">
          <div className="font-semibold text-slate-800 text-sm flex items-center justify-between">
            Advanced Insights
            <span className="text-xs font-normal text-slate-400">
              {adv.total} records · {adv.batch_vs_single?.batch_count ?? 0} batch · {adv.batch_vs_single?.single_count ?? 0} individual
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <InsightRow label="Model Usage Frequency"  items={adv.usage_frequency}       valueKey="count"        color="text-brand-600" />
            <InsightRow label="Stroke Prediction Rate" items={adv.stroke_rate_per_model}  valueKey="stroke_rate"  unit="%" color="text-red-500" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <InsightRow label="Avg Risk Score per Model" items={adv.avg_risk_per_model} valueKey="avg_probability" unit="%" color="text-amber-600" />
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Confidence Distribution</div>
              <div className="flex flex-wrap gap-2">
                {adv.confidence_distribution?.map((b, i) => (
                  <div key={i} className="bg-slate-50 border border-slate-100 rounded-xl px-3 py-2 text-center min-w-[64px]">
                    <div className="text-sm font-bold text-teal-600">{b.count}</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">{b.range}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          {adv.batch_vs_single && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Batch vs Individual</div>
              <div className="flex flex-wrap gap-3">
                {[
                  { label: 'Ind. Avg Risk',     value: adv.batch_vs_single.single_avg_risk,    unit: '%', color: 'text-brand-600' },
                  { label: 'Batch Avg Risk',    value: adv.batch_vs_single.batch_avg_risk,     unit: '%', color: 'text-purple-600' },
                  { label: 'Ind. Stroke Rate',  value: adv.batch_vs_single.single_stroke_rate, unit: '%', color: 'text-red-500' },
                  { label: 'Batch Stroke Rate', value: adv.batch_vs_single.batch_stroke_rate,  unit: '%', color: 'text-orange-500' },
                ].map((item, i) => (
                  <div key={i} className="bg-slate-50 border border-slate-100 rounded-xl px-4 py-2.5 text-center min-w-[90px]">
                    <div className={`text-sm font-bold ${item.color}`}>{item.value}{item.unit}</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">{item.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Prediction Records */}
      <div className="card overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 font-semibold text-slate-800 text-sm flex items-center gap-3 flex-wrap">
          Prediction Records
          <span className="text-xs text-slate-400 font-normal">{recTotal} total records</span>
          <div className="ml-auto flex gap-2 flex-wrap">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input value={recSearch}
                onChange={e => { setRecSearch(e.target.value); setRecPage(1) }}
                placeholder="Search patient…"
                className="pl-8 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-brand-400 w-40" />
            </div>
            <select value={recFilter}
              onChange={e => { setRecFilter(e.target.value); setRecPage(1) }}
              className="text-xs border border-slate-200 rounded-lg px-2 py-1.5 focus:outline-none focus:border-brand-400">
              <option value="">All Predictions</option>
              <option value="Stroke">Stroke</option>
              <option value="No Stroke">No Stroke</option>
            </select>
          </div>
        </div>

        {recLoading ? (
          <div className="flex items-center justify-center py-12"><Spinner /></div>
        ) : records.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">
            No records saved yet. Use Save Data on the Patient Analysis page.
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100">
                    {['ID','Patient ID','Age','Gender','Prediction','Probability','LR','DT','RF','RF+S','XGB','Cat','LGB','Source','Timestamp'].map(h => (
                      <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {records.map((r, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="px-3 py-2.5 font-mono text-xs text-slate-500">{r.id}</td>

                      {/* ── Clickable Patient ID ── */}
                      <td className="px-3 py-2.5">
                        {r.patient_id ? (
                          <button
                            onClick={() => setModalPid(r.patient_id)}
                            className="text-xs font-medium text-brand-600 hover:text-brand-800 hover:underline underline-offset-2 transition-colors"
                          >
                            {r.patient_id}
                          </button>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>

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
                      <td className="px-3 py-2.5">
                        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-md ${r.source === 'batch' ? 'bg-purple-50 text-purple-600' : 'bg-brand-50 text-brand-600'}`}>
                          {r.source === 'batch' ? 'Batch' : 'Single'}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-[10px] text-slate-400 whitespace-nowrap">
                        {r.timestamp ? new Date(r.timestamp).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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