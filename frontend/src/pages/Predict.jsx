import { useState } from 'react'
import { predict, savePrediction } from '../services/api'
import PageHeader from '../components/PageHeader'
import RiskGauge from '../components/RiskGauge'
import Spinner from '../components/Spinner'
import { getRiskColor, getPredictionColor } from '../utils/helpers'
import {
  AlertCircle, CheckCircle2, ChevronRight, RotateCcw,
  Brain, ShieldAlert, Save, Search, UserPlus
} from 'lucide-react'

const API = 'http://127.0.0.1:5000/api'

const INITIAL = {
  id: '', gender: '', age: '', hypertension: '',
  heart_disease: '', ever_married: '', work_type: '',
  Residence_type: '', avg_glucose_level: '', bmi: '',
  smoking_status: ''
}

const SELECT_OPTS = {
  gender:         ['Male','Female','Other'],
  hypertension:   ['0','1'],
  heart_disease:  ['0','1'],
  ever_married:   ['Yes','No'],
  work_type:      ['Private','Self-employed','Govt_job','children','Never_worked'],
  Residence_type: ['Urban','Rural'],
  smoking_status: ['never smoked','formerly smoked','smokes','Unknown'],
}

const FIELDS = [
  [
    { key: 'id',                label: 'Patient ID',         type: 'number', placeholder: 'e.g. 12345' },
    { key: 'gender',            label: 'Gender',             type: 'select' },
    { key: 'age',               label: 'Age',                type: 'number', placeholder: 'Years' },
    { key: 'ever_married',      label: 'Ever Married',       type: 'select' },
  ],
  [
    { key: 'hypertension',      label: 'Hypertension',       type: 'select', hint: '0 = No, 1 = Yes' },
    { key: 'heart_disease',     label: 'Heart Disease',      type: 'select', hint: '0 = No, 1 = Yes' },
    { key: 'work_type',         label: 'Work Type',          type: 'select' },
    { key: 'Residence_type',    label: 'Residence',          type: 'select' },
  ],
  [
    { key: 'avg_glucose_level', label: 'Avg Glucose Level',  type: 'number', placeholder: 'mg/dL, e.g. 150' },
    { key: 'bmi',               label: 'BMI',                type: 'number', placeholder: 'e.g. 26.5' },
    { key: 'smoking_status',    label: 'Smoking Status',     type: 'select' },
  ]
]

export default function Predict() {
  const [form,    setForm]    = useState(INITIAL)
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)
  const [saving,  setSaving]  = useState(false)
  const [saved,   setSaved]   = useState(false)

  // ── Patient lookup state ──────────────────────────────────────────────────
  const [lookupId,      setLookupId]      = useState('')
  const [lookupStatus,  setLookupStatus]  = useState(null)   // null | 'found' | 'not-found' | 'new'
  const [lookupLoading, setLookupLoading] = useState(false)
  const [generatedId,   setGeneratedId]   = useState(null)   // shown after save for new patient

  const handleChange = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }))

  // ── Look up an existing patient ───────────────────────────────────────────
  const handleLookup = async () => {
    const pid = lookupId.trim()
    if (!pid) return
    setLookupLoading(true); setLookupStatus(null)
    try {
      const res  = await fetch(`${API}/check-patient`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: pid }),
      })
      const data = await res.json()
      if (data.exists && data.patient) {
        const p = data.patient
        setForm(prev => ({
          ...prev,
          id:                p.patient_id || prev.id,
          gender:            p.gender            || prev.gender,
          age:               p.age               ?? prev.age,
          hypertension:      p.hypertension      ?? prev.hypertension,
          heart_disease:     p.heart_disease     ?? prev.heart_disease,
          ever_married:      p.ever_married      || prev.ever_married,
          work_type:         p.work_type         || prev.work_type,
          Residence_type:    p.residence_type    || prev.Residence_type,
          avg_glucose_level: p.avg_glucose_level ?? prev.avg_glucose_level,
          bmi:               p.bmi               ?? prev.bmi,
          smoking_status:    p.smoking_status    || prev.smoking_status,
        }))
        setLookupStatus('found')
      } else {
        setLookupStatus('not-found')
      }
    } catch {
      setLookupStatus('not-found')
    } finally {
      setLookupLoading(false)
    }
  }

  const handleSubmit = async e => {
    e.preventDefault()
    setError(null); setLoading(true); setSaved(false); setGeneratedId(null)
    try {
      const res = await predict(form)
      setResult(res)
      localStorage.setItem("patientData", JSON.stringify(form))
      localStorage.setItem("predictionResult", JSON.stringify(res))
    } catch (err) {
      setError(err.response?.data?.error ?? 'Prediction failed. Please check inputs.')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!result || saving || saved) return
    setSaving(true)
    try {
      const res = await savePrediction({ patient: form, result })
      setSaved(true)
      // If backend returned a generated patient_id, surface it
      if (res?.patient_id && !form.id) {
        setGeneratedId(res.patient_id)
      }
    } catch (err) {
      alert('Save failed: ' + (err.response?.data?.error ?? err.message))
    } finally {
      setSaving(false)
    }
  }

  const downloadPDF = async () => {
    if (!result) return
    try {
      const payload = { ...form, prediction: result.final_prediction,
        probability: result.probability, risk_level: result.risk_level, explanation: result.explanation }
      const response = await fetch("http://127.0.0.1:5000/api/download-stroke-pdf", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
      })
      if (!response.ok) { const err = await response.json(); throw new Error(err.error || "PDF failed") }
      const blob = await response.blob()
      const url  = window.URL.createObjectURL(blob)
      const a    = document.createElement("a")
      a.href = url; a.download = "stroke_risk_report.pdf"; a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) { alert("PDF Error: " + err.message) }
  }

  const reset = () => {
    setForm(INITIAL); setResult(null); setError(null); setSaved(false)
    setLookupId(''); setLookupStatus(null); setGeneratedId(null)
  }

  const riskColor = result ? getRiskColor(result.risk_level) : null
  const predColor = result ? getPredictionColor(result.final_prediction) : null

  return (
    <div className="flex-1 p-6 max-w-6xl mx-auto w-full animate-fade-up">
      <PageHeader
        title="Patient Risk Analysis"
        subtitle="Stroke prediction using LightGBM production model"
        action={result && (
          <button onClick={reset} className="btn-secondary">
            <RotateCcw className="w-4 h-4" /> New Patient
          </button>
        )}
      />

      {/* ── Patient Lookup Bar (NEW — above form) ── */}
      {!result && (
        <div className="card p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <UserPlus className="w-4 h-4 text-brand-500" />
            <span className="text-sm font-semibold text-slate-700">Existing Patient Lookup</span>
            <span className="text-xs text-slate-400 font-normal ml-1">(optional — leave blank for new patient)</span>
          </div>
          <div className="flex gap-2">
            <input
              value={lookupId}
              onChange={e => { setLookupId(e.target.value); setLookupStatus(null) }}
              onKeyDown={e => e.key === 'Enter' && handleLookup()}
              placeholder="Enter existing Patient ID, e.g. STR20260001"
              className="input-field flex-1 text-sm"
            />
            <button
              onClick={handleLookup}
              disabled={!lookupId.trim() || lookupLoading}
              className="btn-secondary shrink-0 gap-1.5"
            >
              {lookupLoading ? <Spinner size="sm" /> : <Search className="w-4 h-4" />}
              Lookup
            </button>
          </div>

          {lookupStatus === 'found' && (
            <div className="flex items-center gap-2 mt-2 text-emerald-700 text-xs">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Patient found — form auto-filled. You can update values before predicting.
            </div>
          )}
          {lookupStatus === 'not-found' && (
            <div className="flex items-center gap-2 mt-2 text-amber-600 text-xs">
              <AlertCircle className="w-3.5 h-3.5" />
              Patient ID not found. Fill in details to create a new record.
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Form */}
        <div className={`${result ? 'lg:col-span-3' : 'lg:col-span-5'} card p-6`}>
          <div className="flex items-center gap-2 mb-5">
            <Brain className="w-4 h-4 text-brand-500" />
            <span className="font-semibold text-slate-800 text-sm">Patient Information</span>
          </div>
          <form onSubmit={handleSubmit}>
            {FIELDS.map((row, ri) => (
              <div key={ri} className={`grid gap-4 mb-4 ${ri === 2 ? 'grid-cols-1 sm:grid-cols-3' : 'grid-cols-2 sm:grid-cols-4'}`}>
                {row.map(({ key, label, type, placeholder, hint }) => (
                  <div key={key}>
                    <label className="label">{label}{hint && <span className="ml-1 text-slate-400 normal-case font-normal">({hint})</span>}</label>
                    {type === 'select' ? (
                      <select name={key} value={form[key]} onChange={handleChange} required className="input-field">
                        <option value="">Select…</option>
                        {SELECT_OPTS[key].map(o => <option key={o} value={o}>{o}</option>)}
                      </select>
                    ) : (
                      <input name={key} type={type} value={form[key]} onChange={handleChange}
                        placeholder={placeholder} required step="any" className="input-field" />
                    )}
                  </div>
                ))}
              </div>
            ))}

            {error && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm mb-4">
                <AlertCircle className="w-4 h-4 shrink-0" /> {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full justify-center mt-2">
              {loading ? <><Spinner size="sm" /> Analyzing…</> : <>Analyze Risk <ChevronRight className="w-4 h-4" /></>}
            </button>
          </form>
        </div>

        {/* Results */}
        {result && (
          <div className="lg:col-span-2 space-y-4 animate-fade-up">

            <button onClick={downloadPDF} className="btn-primary w-full justify-center">
              Download Report
            </button>

            <button
              onClick={handleSave}
              disabled={saving || saved}
              className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 border ${
                saved
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-700 cursor-default'
                  : 'bg-white border-slate-200 text-slate-700 hover:border-brand-300 hover:text-brand-700'
              }`}
            >
              {saving ? (
                <><Spinner size="sm" /> Saving…</>
              ) : saved ? (
                <><CheckCircle2 className="w-4 h-4" /> Saved</>
              ) : (
                <><Save className="w-4 h-4" /> Save Data</>
              )}
            </button>

            {/* Generated Patient ID banner */}
            {generatedId && (
              <div className="p-3 rounded-xl bg-brand-50 border border-brand-100 text-xs text-brand-700 flex items-center gap-2">
                <UserPlus className="w-3.5 h-3.5 shrink-0" />
                New Patient ID generated: <span className="font-mono font-bold">{generatedId}</span>
              </div>
            )}

            {/* Main result */}
            <div className={`card p-5 border ${predColor.border}`}>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Diagnosis</span>
                {result.final_prediction === 'Stroke'
                  ? <ShieldAlert className="w-5 h-5 text-red-500" />
                  : <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                }
              </div>
              <div className={`text-2xl font-bold mb-1 ${predColor.text}`}>{result.final_prediction}</div>
              <div className="text-sm text-slate-500">Patient ID: {result.patient_id}</div>
              <div className="mt-4 flex justify-center">
                <RiskGauge probability={result.probability} risk={result.risk_level} />
              </div>
            </div>

            {/* Model consensus */}
            <div className="card p-5">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">All Model Predictions</div>
              <div className="space-y-2">
                {result.model_results?.map(m => {
                  const mc = getPredictionColor(m.prediction)
                  return (
                    <div key={m.model} className="flex items-center gap-2 text-sm">
                      <div className="flex-1 flex items-center gap-1.5 min-w-0">
                        {m.is_production && <span className="badge-blue text-[10px] shrink-0">★</span>}
                        <span className="text-slate-600 truncate">{m.model}</span>
                      </div>
                      <div className="w-20">
                        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${m.prediction === 'Stroke' ? 'bg-red-400' : 'bg-emerald-400'}`}
                            style={{ width: `${m.probability}%` }} />
                        </div>
                      </div>
                      <span className={`text-xs font-semibold w-10 text-right ${mc.text}`}>{m.probability}%</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Explanation */}
            <div className="card p-5">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Risk Factors</div>
              <ul className="space-y-2">
                {result.explanation?.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                    <span className="mt-0.5 w-5 h-5 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center text-xs font-bold shrink-0">{i+1}</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}