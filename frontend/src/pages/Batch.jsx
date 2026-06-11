import { useState, useRef, useCallback } from 'react'
import { batchPredict, downloadResults, downloadTemplate } from '../services/api'
import PageHeader from '../components/PageHeader'
import Spinner from '../components/Spinner'
import { getRiskColor, getPredictionColor } from '../utils/helpers'
import { Upload, Download, FileSpreadsheet, AlertCircle, CheckCircle2, X, ArrowDownToLine } from 'lucide-react'

function SummaryCard({ label, value, color }) {
  return (
    <div className="card p-4 text-center">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-slate-400 font-medium mt-0.5">{label}</div>
    </div>
  )
}

export default function Batch() {
  const [file,      setFile]      = useState(null)
  const [dragging,  setDragging]  = useState(false)
  const [loading,   setLoading]   = useState(false)
  const [result,    setResult]    = useState(null)
  const [error,     setError]     = useState(null)
  const inputRef = useRef()

  const handleFile = f => {
    if (!f) return
    const ok = f.name.match(/\.(csv|xlsx|xls)$/i)
    if (!ok) { setError('Only CSV or Excel (.xlsx) files are supported.'); return }
    setFile(f)
    setError(null)
    setResult(null)
  }

  const onDrop = useCallback(e => {
    e.preventDefault(); setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }, [])

  const onDragOver  = e => { e.preventDefault(); setDragging(true)  }
  const onDragLeave = ()  => setDragging(false)

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true); setError(null)
    try {
      const res = await batchPredict(file)
      setResult(res)
    } catch (err) {
      setError(err.response?.data?.error ?? 'Upload failed. Check file format.')
    } finally {
      setLoading(false)
    }
  }

  const riskBadge = (risk) => {
    const c = getRiskColor(risk)
    return <span className={`badge ${c.bg} ${c.text} text-[11px]`}>{risk}</span>
  }

  return (
    <div className="flex-1 p-6 max-w-6xl mx-auto w-full animate-fade-up">
      <PageHeader
        title="Batch Prediction"
        subtitle="Upload a CSV or Excel file to analyze multiple patients at once"
        action={
          <button onClick={downloadTemplate} className="btn-secondary">
            <ArrowDownToLine className="w-4 h-4" /> Sample Template
          </button>
        }
      />

      {/* Upload area */}
      {!result && (
        <div className="card p-6 mb-6">
          <div
            onDrop={onDrop} onDragOver={onDragOver} onDragLeave={onDragLeave}
            onClick={() => inputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200 ${
              dragging
                ? 'border-brand-400 bg-brand-50'
                : 'border-slate-200 hover:border-brand-300 hover:bg-slate-50'
            }`}
          >
            <input ref={inputRef} type="file" accept=".csv,.xlsx,.xls" className="hidden"
              onChange={e => handleFile(e.target.files[0])} />
            <FileSpreadsheet className="w-10 h-10 text-brand-300 mx-auto mb-3" />
            {file ? (
              <div className="flex items-center justify-center gap-2">
                <span className="text-slate-700 font-medium text-sm">{file.name}</span>
                <button onClick={e => { e.stopPropagation(); setFile(null) }}
                  className="text-slate-400 hover:text-red-500 transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <>
                <div className="text-slate-600 font-medium mb-1">Drop file here or <span className="text-brand-600">browse</span></div>
                <div className="text-slate-400 text-xs">Supports CSV, XLSX · Max 10 MB</div>
              </>
            )}
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 mt-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" /> {error}
            </div>
          )}

          <div className="mt-4 flex gap-3 justify-end">
            <button onClick={handleSubmit} disabled={!file || loading} className="btn-primary">
              {loading ? <><Spinner size="sm" /> Processing…</> : <><Upload className="w-4 h-4" /> Run Predictions</>}
            </button>
          </div>

          {/* Column hint */}
          <div className="mt-5 p-4 bg-slate-50 rounded-xl border border-slate-100">
            <div className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wide">Required Columns</div>
            <div className="flex flex-wrap gap-1.5">
              {['id','gender','age','hypertension','heart_disease','ever_married','work_type','Residence_type','avg_glucose_level','bmi','smoking_status'].map(c => (
                <code key={c} className="text-[11px] bg-white border border-slate-200 rounded-md px-2 py-0.5 text-slate-600 font-mono">{c}</code>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-5 animate-fade-up">
          {/* Summary */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <SummaryCard label="Total Patients"     value={result.total}           color="text-slate-800" />
            <SummaryCard label="Stroke Risk"         value={result.stroke_count}    color="text-red-600"   />
            <SummaryCard label="No Stroke"           value={result.no_stroke_count} color="text-emerald-600" />
            <SummaryCard label="Avg Probability"     value={`${result.avg_probability}%`} color="text-brand-600" />
          </div>

          {/* Table */}
          <div className="card overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <div className="font-semibold text-slate-800 text-sm">Prediction Results</div>
              <div className="flex gap-3">
                <button onClick={() => { setResult(null); setFile(null) }} className="btn-secondary text-sm px-3 py-1.5">
                  <Upload className="w-3.5 h-3.5" /> New Upload
                </button>
                <button onClick={() => downloadResults(result.results)} className="btn-primary text-sm px-3 py-1.5">
                  <Download className="w-3.5 h-3.5" /> Download Excel
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100">
                    {['ID','Age','Gender','Prediction','Probability','Risk'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {result.results.map((row, i) => {
                    const pc = getPredictionColor(row.Prediction)
                    return (
                      <tr key={i} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-mono text-slate-600 text-xs">{row.id}</td>
                        <td className="px-4 py-3 text-slate-700">{row.age}</td>
                        <td className="px-4 py-3 text-slate-700">{row.gender}</td>
                        <td className="px-4 py-3">
                          <span className={`badge ${pc.bg} ${pc.text} text-[11px]`}>{row.Prediction}</span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${row.Prediction === 'Stroke' ? 'bg-red-400' : 'bg-emerald-400'}`}
                                style={{ width: `${row.Probability}%` }} />
                            </div>
                            <span className="text-xs text-slate-500">{row.Probability}%</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">{riskBadge(row.Risk_Category)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
