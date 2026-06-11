import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard } from '../services/api'
import Spinner from '../components/Spinner'
import PageHeader from '../components/PageHeader'
import { Activity, UserSearch, Upload, BarChart3, CheckCircle2, Crown, Target } from 'lucide-react'

const MODEL_COLORS = {
  'LightGBM': 'bg-brand-600', 'XGBoost': 'bg-purple-500', 'CatBoost': 'bg-teal-500',
  'Random Forest + SMOTE': 'bg-orange-500', 'Random Forest': 'bg-amber-500',
  'Decision Tree': 'bg-slate-400', 'Logistic Regression': 'bg-slate-300',
}

function MetricPill({ label, value }) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className="text-2xl font-bold text-slate-800">{value}%</span>
      <span className="text-xs text-slate-400 font-medium">{label}</span>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex-1 flex items-center justify-center min-h-screen">
      <Spinner size="lg" />
    </div>
  )

  const pm = data?.production_model ?? {}
  const lb = data?.leaderboard ?? []

  return (
    <div className="flex-1 p-6 max-w-6xl mx-auto w-full animate-fade-up">
      <PageHeader
        title="Clinical Risk Intelligence"
        subtitle="AI-powered stroke risk assessment platform"
        action={
          <Link to="/predict" className="btn-primary">
            <UserSearch className="w-4 h-4" /> New Analysis
          </Link>
        }
      />

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        {[
          { to: '/predict',   icon: UserSearch, title: 'Patient Analysis',  desc: 'Assess individual stroke risk',    color: 'text-brand-600 bg-brand-50' },
          { to: '/batch',     icon: Upload,     title: 'Batch Prediction',  desc: 'Process multiple patients at once', color: 'text-purple-600 bg-purple-50' },
          { to: '/analytics', icon: BarChart3,  title: 'Model Analytics',   desc: 'Compare all 7 trained models',     color: 'text-teal-600 bg-teal-50'  },
        ].map(({ to, icon: Icon, title, desc, color }) => (
          <Link key={to} to={to}
            className="card card-hover p-5 flex items-center gap-4 group"
          >
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <div className="font-semibold text-slate-800 text-sm">{title}</div>
              <div className="text-xs text-slate-400 mt-0.5">{desc}</div>
            </div>
          </Link>
        ))}
      </div>

      {/* Production Model Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div className="card p-6 lg:col-span-1 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-600 to-brand-800 opacity-100 rounded-2xl" />
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <Crown className="w-4 h-4 text-brand-200" />
              <span className="text-xs font-semibold text-brand-200 uppercase tracking-wide">Production Model</span>
            </div>
            <div className="text-2xl font-bold text-white mb-1">LightGBM</div>
            <div className="text-brand-200 text-xs mb-5">Gradient Boosting · Optimized for recall</div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Accuracy',  value: pm.accuracy  },
                { label: 'ROC-AUC',   value: pm.roc_auc   },
                { label: 'Recall',    value: pm.recall    },
                { label: 'F1 Score',  value: pm.f1_score  },
              ].map(({ label, value }) => (
                <div key={label} className="bg-white/10 rounded-xl p-3">
                  <div className="text-lg font-bold text-white">{value}%</div>
                  <div className="text-[11px] text-brand-200 font-medium">{label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Leaderboard */}
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-4 h-4 text-brand-500" />
            <span className="font-semibold text-slate-800 text-sm">Model Leaderboard</span>
            <span className="ml-auto text-xs text-slate-400">Ranked by ROC-AUC</span>
          </div>
          <div className="space-y-2.5">
            {lb.map((m, i) => (
              <div key={m.model} className="flex items-center gap-3">
                <span className="w-5 text-center text-xs font-bold text-slate-400">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-slate-700 truncate">{m.model}</span>
                    {m.is_production && (
                      <span className="badge-blue text-[10px]">Production</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${MODEL_COLORS[m.model] ?? 'bg-slate-400'} transition-all`}
                        style={{ width: `${m.roc_auc}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-slate-500 w-12 text-right">{m.roc_auc}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { icon: Activity,   label: 'Models Trained',     value: data?.total_models ?? 7, color: 'text-brand-500 bg-brand-50' },
          { icon: CheckCircle2, label: 'Best ROC-AUC',     value: `${lb[0]?.roc_auc ?? '—'}%`, color: 'text-emerald-600 bg-emerald-50' },
          { icon: Target,     label: 'Threshold',          value: '10%', color: 'text-amber-600 bg-amber-50' },
          { icon: Crown,      label: 'Top Recall',         value: `${pm.recall}%`, color: 'text-purple-600 bg-purple-50' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="stat-card">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
              <Icon className="w-4.5 h-4.5" />
            </div>
            <div className="stat-value text-2xl mt-2">{value}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
