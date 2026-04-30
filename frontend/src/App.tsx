import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import Navbar from './components/Navbar'
import EnrollPage from './pages/EnrollPage'
import CertificateViewPage from './pages/CertificateViewPage'
import VerifyPage from './pages/VerifyPage'

function App() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-lg mx-auto w-full px-4 py-6">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/enroll" element={<EnrollPage />} />
          <Route path="/certificate" element={<CertificateViewPage />} />
          <Route path="/verify/:vidId" element={<VerifyPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
