import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar  from './components/Topbar'
import Dashboard        from './pages/Dashboard'
import Predict          from './pages/Predict'
import Batch            from './pages/Batch'
import Analytics        from './pages/Analytics'
import About            from './pages/About'
import ModelPerformance from './pages/ModelPerformance'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-50">
      <Sidebar />
      <Topbar />
      <main className="flex-1 flex flex-col min-h-screen overflow-y-auto">
        <Routes>
          <Route path="/"                   element={<Dashboard        />} />
          <Route path="/predict"            element={<Predict          />} />
          <Route path="/batch"              element={<Batch            />} />
          <Route path="/analytics"          element={<Analytics        />} />
          <Route path="/model-performance"  element={<ModelPerformance />} />
          <Route path="/about"              element={<About            />} />
        </Routes>
      </main>
    </div>
  )
}