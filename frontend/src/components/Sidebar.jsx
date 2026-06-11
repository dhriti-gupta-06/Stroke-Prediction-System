import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, UserSearch, Upload,
  BarChart3, Info, Activity, TrendingUp
} from 'lucide-react'

const NAV = [
  { to: '/',                icon: LayoutDashboard, label: 'Dashboard'          },
  { to: '/predict',         icon: UserSearch,      label: 'Patient Analysis'   },
  { to: '/batch',           icon: Upload,          label: 'Batch Prediction'   },
  { to: '/analytics',       icon: BarChart3,       label: 'Model Analytics'    },
  { to: '/model-performance', icon: TrendingUp,    label: 'Model Performance'  },
  { to: '/about',           icon: Info,            label: 'About'              },
]

// rest of component unchanged

export default function Sidebar() {
  return (
    <aside className="hidden md:flex flex-col w-56 shrink-0 bg-white border-r border-slate-100 h-screen sticky top-0">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-slate-100">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center shrink-0">
          <Activity className="w-4 h-4 text-white" />
        </div>
        <div>
          <div className="text-sm font-bold text-slate-800 leading-none">NeuralStroke</div>
          <div className="text-[10px] text-slate-400 mt-0.5 font-medium tracking-wide uppercase">Clinical AI</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'text-brand-700 bg-brand-50'
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
              }`
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-100">
        <div className="rounded-xl bg-brand-50 border border-brand-100 p-3">
          <div className="text-xs font-semibold text-brand-700">LightGBM Active</div>
          <div className="text-[11px] text-brand-500 mt-0.5">Production model · v1.0</div>
        </div>
      </div>
    </aside>
  )
}
