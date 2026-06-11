import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Activity, Menu, X, LayoutDashboard, UserSearch, Upload, BarChart3, Info, TrendingUp } from 'lucide-react'

const NAV = [
  { to: '/',                  icon: LayoutDashboard, label: 'Dashboard'          },
  { to: '/predict',           icon: UserSearch,      label: 'Patient Analysis'   },
  { to: '/batch',             icon: Upload,          label: 'Batch Prediction'   },
  { to: '/analytics',         icon: BarChart3,       label: 'Model Analytics'    },
  { to: '/model-performance', icon: TrendingUp,      label: 'Model Performance'  },
  { to: '/about',             icon: Info,            label: 'About'              },
]

// rest of component unchanged

export default function Topbar() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <header className="md:hidden sticky top-0 z-40 bg-white border-b border-slate-100 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
            <Activity className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-bold text-slate-800 text-sm">NeuralStroke</span>
        </div>
        <button onClick={() => setOpen(o => !o)} className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors">
          {open ? <X className="w-5 h-5 text-slate-600" /> : <Menu className="w-5 h-5 text-slate-600" />}
        </button>
      </header>
      {open && (
        <div className="md:hidden fixed inset-0 z-30 bg-black/20" onClick={() => setOpen(false)}>
          <nav className="absolute top-[53px] left-0 right-0 bg-white border-b border-slate-100 px-4 py-2 space-y-0.5">
            {NAV.map(({ to, icon: Icon, label }) => (
              <NavLink key={to} to={to} end={to === '/'} onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive ? 'text-brand-700 bg-brand-50' : 'text-slate-600 hover:bg-slate-50'
                  }`
                }
              >
                <Icon className="w-4 h-4" />{label}
              </NavLink>
            ))}
          </nav>
        </div>
      )}
    </>
  )
}
