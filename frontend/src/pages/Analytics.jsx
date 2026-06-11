import { useEffect, useState } from 'react'
import { getMetrics } from '../services/api'
import PageHeader from '../components/PageHeader'
import Spinner from '../components/Spinner'
import { Crown, Info } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts'

const METRIC_KEYS = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']
const TAB_KEYS = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'confusion_matrix']
const METRIC_LABELS = { accuracy: 'Accuracy', precision: 'Precision', recall: 'Recall', f1_score: 'F1 Score', roc_auc: 'ROC-AUC' , confusion_matrix: 'Confusion Matrix'}
const MODEL_COLORS = {
  'LightGBM': '#0a78ed', 'XGBoost': '#a855f7', 'CatBoost': '#14b8a6',
  'Random Forest + SMOTE': '#f97316', 'Random Forest': '#f59e0b',
  'Decision Tree': '#94a3b8', 'Logistic Regression': '#cbd5e1'
}
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
  const [selected, setSelected] = useState(null)
  

// always safely read localStorage
  const formData = JSON.parse(localStorage.getItem("patientData") || "null");
  const storedResult = JSON.parse(localStorage.getItem("predictionResult") || "null");




  useEffect(() => {
    getMetrics()
      .then(d => { setData(d); setSelected(d.find(m => m.is_production) || d[0]) })
      .finally(() => setLoad(false))
  }, [])

  if (loading) return <div className="flex-1 flex items-center justify-center"><Spinner size="lg" /></div>

  const barData  = activeMetric !== 'confusion_matrix' ? data.map(m => ({ name: SHORT(m.model), fullName: m.model, [METRIC_LABELS[activeMetric]]: m[activeMetric], prod: m.is_production })) : []
  const radarData = selected ? METRIC_KEYS.map(k => ({
    metric: METRIC_LABELS[k], value: selected[k]
  })) : []
  const allRadar = METRIC_KEYS.map(k => ({
    metric: METRIC_LABELS[k],
    ...Object.fromEntries(data.map(m => [SHORT(m.model), m[k]]))
  }))

  const downloadCSV = async () => {
  const res = await fetch("http://127.0.0.1:5000/api/download-metrics");

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "model_analytics.csv";
  a.click();
};

  // ✅ ADD THIS HERE (NOT replace anything above)
const downloadStrokePDF = async (formData) => {
  try {
    const response = await fetch(
      "http://127.0.0.1:5000/api/download-stroke-pdf",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      }
    );

    // ❗ If backend returns error (not PDF)
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || "Failed to generate PDF");
    }

    const blob = await response.blob();

    // Ensure it's actually a PDF
    if (blob.type !== "application/pdf") {
      throw new Error("Invalid PDF response from server");
    }

    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "stroke_risk_report.pdf";
    document.body.appendChild(a);
    a.click();

    // cleanup
    a.remove();
    window.URL.revokeObjectURL(url);

  } catch (error) {
    console.error("PDF download failed:", error.message);
    alert("Failed to download PDF: " + error.message);
  }
};

  return (
    <div className="flex-1 p-6 max-w-6xl mx-auto w-full animate-fade-up">
      <div className="flex justify-between items-center mb-6">
  <PageHeader
    title="Model Analytics"
    subtitle="Performance comparison of all 7 trained models"
  />
  
  <button
    onClick={downloadCSV}
    className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition"
  >
    Download CSV
  </button>
  <button
    onClick={() => {
      const payload = JSON.parse(localStorage.getItem("patientData") || "{}");
      const result = JSON.parse(localStorage.getItem("predictionResult") || "{}");

      if (!payload || Object.keys(payload).length === 0) {
        alert("No patient data found. Please run prediction first.");
        return;
      }

      downloadStrokePDF({
        ...payload,
        prediction: result.final_prediction,
        probability: result.probability,
        risk_level: result.risk_level
      });
    }}
    className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition"
  >
    Download PDF
  </button>
</div>

      {/* Metric tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {TAB_KEYS.map(k => (
          <button key={k} onClick={() => setActiveMetric(k)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-150 ${
              activeMetric === k
                ? 'bg-brand-600 text-white'
                : 'bg-white text-slate-600 border border-slate-200 hover:border-brand-300'
            }`}
          >{METRIC_LABELS[k]}</button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Bar chart */}
        <div className="card p-5 lg:col-span-2">

  <div className="font-semibold text-slate-800 text-sm mb-4">
    {activeMetric === 'confusion_matrix'
      ? 'Confusion Matrix'
      : `${METRIC_LABELS[activeMetric]} by Model`}
  </div>

  {activeMetric !== 'confusion_matrix' ? (

    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={barData} margin={{ top: 4, right: 8, left: -10, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          axisLine={false}
          tickLine={false}
          unit="%"
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar
          dataKey={METRIC_LABELS[activeMetric]}
          fill={BAR_COLOR}
          radius={[6,6,0,0]}
          label={{
            position: 'top',
            fontSize: 10,
            fill: '#64748b',
            formatter: v => `${v}%`
          }}
        />
      </BarChart>
    </ResponsiveContainer>

  ) : (

    <div>

      <div className="mb-4">
        <select
          value={selected?.model || ''}
          onChange={(e) =>
            setSelected(
              data.find(m => m.model === e.target.value)
            )
          }
          className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
        >
          {data.map(m => (
            <option key={m.model} value={m.model}>
              {m.model}
            </option>
          ))}
        </select>
      </div>

      {selected && (
        <div className="grid grid-cols-2 gap-4 max-w-md mx-auto">

          <div className="bg-green-100 rounded-xl p-6 text-center">
            <div className="text-xs text-slate-600">True Negative</div>
            <div className="text-2xl font-bold">
              {selected.confusion_matrix[0][0]}
            </div>
          </div>

          <div className="bg-red-100 rounded-xl p-6 text-center">
            <div className="text-xs text-slate-600">False Positive</div>
            <div className="text-2xl font-bold">
              {selected.confusion_matrix[0][1]}
            </div>
          </div>

          <div className="bg-orange-100 rounded-xl p-6 text-center">
            <div className="text-xs text-slate-600">False Negative</div>
            <div className="text-2xl font-bold">
              {selected.confusion_matrix[1][0]}
            </div>
          </div>

          <div className="bg-blue-100 rounded-xl p-6 text-center">
            <div className="text-xs text-slate-600">True Positive</div>
            <div className="text-2xl font-bold">
              {selected.confusion_matrix[1][1]}
            </div>
          </div>

        </div>
      )}

    </div>

  )}

</div>

        {/* Selected model radar */}
        <div className="card p-5">
          <div className="font-semibold text-slate-800 text-sm mb-1">Model Profile</div>
          <div className="flex gap-2 mb-3 flex-wrap">
            {data.map(m => (
              <button key={m.model} onClick={() => setSelected(m)}
                className={`text-[11px] px-2 py-1 rounded-lg font-medium transition-colors ${
                  selected?.model === m.model ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}>
                {SHORT(m.model)}
              </button>
            ))}
          </div>
          {selected && (
            <>
              <div className="flex items-center gap-2 mb-2">
                <span className="font-semibold text-slate-700 text-sm">{selected.model}</span>
                {selected.is_production && <span className="badge-blue text-[10px] flex items-center gap-1"><Crown className="w-2.5 h-2.5" /> Production</span>}
              </div>
              <ResponsiveContainer width="100%" height={180}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar name={selected.model} dataKey="value" stroke={MODEL_COLORS[selected.model] ?? '#0a78ed'}
                    fill={MODEL_COLORS[selected.model] ?? '#0a78ed'} fillOpacity={0.2} />
                </RadarChart>
              </ResponsiveContainer>
            </>
          )}
        </div>
      </div>

      {/* Full metrics table */}
      <div className="card overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 font-semibold text-slate-800 text-sm flex items-center gap-2">
          Full Performance Table
          <span className="ml-auto text-xs text-slate-400 font-normal flex items-center gap-1">
            <Info className="w-3.5 h-3.5" /> Threshold: 10%
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100">
                <th className="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Model</th>
                {METRIC_KEYS.map(k => (
                  <th key={k} className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wide">{METRIC_LABELS[k]}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {data.sort((a, b) => b.roc_auc - a.roc_auc).map(m => (
                <tr key={m.model} className={`hover:bg-slate-50 transition-colors ${m.is_production ? 'bg-brand-50/40' : ''}`}>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: MODEL_COLORS[m.model] }} />
                      <span className="font-medium text-slate-700">{m.model}</span>
                      {m.is_production && <span className="badge-blue text-[10px]">★ Production</span>}
                    </div>
                  </td>
                  {METRIC_KEYS.map(k => (
                    <td key={k} className={`px-4 py-3 text-right font-semibold ${
                      k === activeMetric ? 'text-brand-700' : 'text-slate-600'
                    }`}>{m[k]}%</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
