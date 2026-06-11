import { Activity, Brain, Database, GitBranch, Target, Zap } from 'lucide-react'
import PageHeader from '../components/PageHeader'

const MODELS = [
  { name: 'Logistic Regression', type: 'Baseline', desc: 'Linear probabilistic classifier for binary outcomes' },
  { name: 'Decision Tree',       type: 'Tree',     desc: 'Rule-based splits on feature thresholds' },
  { name: 'Random Forest',       type: 'Ensemble', desc: 'Bagged ensemble of decision trees for variance reduction' },
  { name: 'RF + SMOTE',          type: 'Balanced', desc: 'Random Forest with synthetic minority oversampling' },
  { name: 'XGBoost',             type: 'Boosting', desc: 'Gradient boosted trees with regularization' },
  { name: 'CatBoost',            type: 'Boosting', desc: 'Categorical feature-native gradient boosting' },
  { name: 'LightGBM',            type: 'Production', desc: 'Leaf-wise boosting, optimized for recall on imbalanced data', prod: true },
]

const FEATURES = [
  { icon: Brain,      label: 'LightGBM Engine',     desc: 'Production-grade gradient boosting for maximum recall' },
  { icon: Target,     label: '10% Threshold',        desc: 'Conservative cutoff optimized for clinical sensitivity' },
  { icon: Database,   label: '7 Models Trained',     desc: 'Comprehensive comparison across algorithm families' },
  { icon: GitBranch,  label: 'SMOTE Balancing',      desc: 'Synthetic oversampling to handle class imbalance' },
  { icon: Zap,        label: 'Real-time Prediction', desc: 'Sub-second inference for clinical workflows' },
  { icon: Activity,   label: 'Explainability',       desc: 'Rule-based risk factor attribution per prediction' },
]

export default function About() {
  return (
    <div className="flex-1 p-6 max-w-5xl mx-auto w-full animate-fade-up">
      <PageHeader title="About This Project" subtitle="Architecture, models, and design decisions" />

      {/* Hero */}
      <div className="card p-6 mb-6 bg-gradient-to-br from-brand-600 to-brand-800 border-none relative overflow-hidden">
        <div className="absolute right-0 bottom-0 w-48 h-48 rounded-full bg-white/5 -mr-10 -mb-10" />
        <div className="relative z-10">
          <div className="text-brand-200 text-xs font-semibold uppercase tracking-wide mb-2">NeuralStroke Platform</div>
          <h2 className="text-white text-xl font-bold mb-2">Clinical Stroke Risk Intelligence</h2>
          <p className="text-brand-100 text-sm leading-relaxed max-w-2xl">
            A production-grade machine learning system for early stroke risk assessment. Built on seven trained
            classifiers with LightGBM selected as the production model for its superior recall on severely
            imbalanced healthcare data.
          </p>
        </div>
      </div>

      {/* Features grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        {FEATURES.map(({ icon: Icon, label, desc }) => (
          <div key={label} className="card p-4 card-hover">
            <div className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center mb-3">
              <Icon className="w-4.5 h-4.5 text-brand-600" />
            </div>
            <div className="font-semibold text-slate-800 text-sm">{label}</div>
            <div className="text-xs text-slate-500 mt-1 leading-relaxed">{desc}</div>
          </div>
        ))}
      </div>

      {/* Model list */}
      <div className="card overflow-hidden mb-6">
        <div className="px-5 py-4 border-b border-slate-100 font-semibold text-slate-800 text-sm">Trained Models</div>
        <div className="divide-y divide-slate-50">
          {MODELS.map(m => (
            <div key={m.name} className={`flex items-center gap-4 px-5 py-3.5 ${m.prod ? 'bg-brand-50/50' : 'hover:bg-slate-50'}`}>
              <span className={`badge text-[11px] shrink-0 ${m.prod ? 'badge-blue' : 'bg-slate-100 text-slate-600'}`}>{m.type}</span>
              <div>
                <div className="font-medium text-slate-800 text-sm flex items-center gap-2">
                  {m.name}
                  {m.prod && <span className="badge-blue text-[10px]">★ Production</span>}
                </div>
                <div className="text-xs text-slate-500">{m.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dataset note */}
      <div className="card p-5 bg-amber-50 border border-amber-100">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center shrink-0 mt-0.5">
            <Activity className="w-4 h-4 text-amber-600" />
          </div>
          <div>
            <div className="font-semibold text-amber-800 text-sm mb-1">Clinical Disclaimer</div>
            <p className="text-amber-700 text-xs leading-relaxed">
              This platform is built for academic and research demonstration purposes.
              The models were trained on the Kaggle Stroke Prediction Dataset. Predictions
              should not substitute clinical diagnosis. A 10% probability threshold is used
              to maximize recall (sensitivity), accepting higher false-positive rates to avoid
              missing at-risk patients.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
