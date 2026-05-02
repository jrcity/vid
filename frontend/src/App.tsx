import { Outlet } from 'react-router-dom'
import HomePage from './pages/HomePage'
import Navbar from './components/Navbar'

function App() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-lg mx-auto w-full px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}

export default App
