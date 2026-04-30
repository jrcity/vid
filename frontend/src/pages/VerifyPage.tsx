import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { useVerify } from '../hooks/useVidApi'
import { MdVerified, MdErrorOutline, MdInfoOutline, MdHistoryEdu } from 'react-icons/md'
import SEO from '../components/SEO'
import clsx from 'clsx'

const VerifyPage: React.FC = () => {
  const { vidId } = useParams<{ vidId: string }>()
  const { data, isLoading, error } = useVerify(vidId)

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <SEO title="Verifying..." />
        <div className="w-12 h-12 border-4 border-slate-200 border-t-brand-accent rounded-full animate-spin" />
        <p className="text-slate-500 font-medium animate-pulse">Verifying Virtual ID...</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
        <SEO title="Verification Failed" />
        <div className="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center text-4xl">
          <MdErrorOutline />
        </div>
        <h2 className="text-xl font-bold text-brand-dark">Verification Failed</h2>
        <p className="text-slate-500 max-w-xs">The provided VID could not be found or has been revoked.</p>
        <Link to="/" className="native-button bg-slate-100 px-8 text-slate-600 mt-4">Go Back</Link>
      </div>
    )
  }

  const scoreColor = data.score >= 80 ? 'text-emerald-500' : data.score >= 55 ? 'text-amber-500' : 'text-red-500'
  const scoreBg = data.score >= 80 ? 'bg-emerald-50' : data.score >= 55 ? 'bg-amber-50' : 'bg-red-50'

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-500">
      <SEO title="Verified ID" description={`Public verification for VID ${data.vid_id}. Status: ${data.trust_grade}.`} />

      <header className="text-center">
        <div className="mx-auto w-16 h-16 bg-emerald-50 text-emerald-500 rounded-full flex items-center justify-center text-4xl mb-4">
          <MdVerified />
        </div>
        <h1 className="text-2xl font-bold text-brand-dark">Verified Identity</h1>
        <p className="text-slate-500 text-sm">Authentic Pan-African Network ID</p>
      </header>

      <section className="space-y-4">
        {/* The Card View (Similar to CertificateViewPage but for public data) */}
        <div className="native-card text-brand-dark p-7 aspect-[1.6/1] relative overflow-hidden flex flex-col justify-between shadow-2xl border-none"
          style={{
            background: 'linear-gradient(135deg, #BF953F 0%, #FCF6BA 25%, #B38728 50%, #FBF5B7 75%, #AA771C 100%)',
            boxShadow: 'inset 0 0 50px rgba(0,0,0,0.1), 0 20px 40px -10px rgba(170, 119, 28, 0.3)'
          }}
        >
          {/* High-End Guilloche Security Pattern */}
          <div className="absolute inset-0 opacity-[0.15] pointer-events-none" 
            style={{ 
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 50 Q 25 0, 50 50 T 100 50' fill='none' stroke='%23AA771C' stroke-width='0.5'/%3E%3Cpath d='M0 60 Q 25 10, 50 60 T 100 60' fill='none' stroke='%23AA771C' stroke-width='0.5'/%3E%3Cpath d='M0 40 Q 25 -10, 50 40 T 100 40' fill='none' stroke='%23AA771C' stroke-width='0.5'/%3E%3C/svg%3E")`,
              backgroundSize: '100px 20px'
            }} 
          />
          
          {/* Metallic Shine Overlay */}
          <div className="absolute inset-0 bg-gradient-to-tr from-white/20 via-transparent to-black/10 pointer-events-none" />

          {/* Unified VID Emblem Watermark (Central) */}
          <div className="absolute inset-0 flex items-center justify-center opacity-[0.1] pointer-events-none select-none">
            <div className="flex flex-col items-center text-center gap-4 rotate-[-15deg]">
              <svg width="180" height="180" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-brand-dark">
                <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor" />
              </svg>
              <div className="space-y-1">
                <h1 className="text-6xl font-black tracking-widest text-brand-dark/20">VID</h1>
                <p className="text-sm font-bold text-brand-dark/40 tracking-[0.3em] uppercase max-w-[280px]">
                  Empowering African Digital Identity through Mobile Innovation
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-start z-10">
            <div className="space-y-1">
              <p className="text-[10px] uppercase tracking-[0.3em] text-brand-dark/60 font-black">Virtual {data.vid_label}</p>
              <h2 className="text-3xl font-black tracking-tight text-brand-dark/50 italic">Confidential Holder</h2>
            </div>
            <div className="w-16 h-16 bg-white/40 backdrop-blur-xl rounded-2xl flex items-center justify-center text-5xl shadow-xl border border-white/20">
              🌍
            </div>
          </div>

          <div className="z-10 flex items-end justify-between">
            <div className="space-y-2">
              <div>
                <p className="text-[9px] uppercase tracking-[0.2em] text-brand-dark/50 font-bold">ID Number</p>
                <p className="font-mono text-sm tracking-widest text-brand-dark font-black">{data.vid_id}</p>
              </div>
              <div className="flex gap-8">
                <div>
                  <p className="text-[9px] uppercase tracking-[0.2em] text-brand-dark/50 font-bold">Issued</p>
                  <p className="text-[10px] font-medium text-brand-dark/80">{new Date(data.issued_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-[9px] uppercase tracking-[0.2em] text-brand-dark/50 font-bold">Region</p>
                  <p className="text-xs font-black tracking-wide text-brand-dark/80">{data.region}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Polished Gold Border */}
          <div className="absolute inset-0 border-[1.5px] border-white/30 rounded-native pointer-events-none" />
        </div>

        <div className={`native-card p-6 space-y-4 ${scoreBg}`}>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[8px] uppercase text-slate-400">Nationality</p>
              <p className="text-sm font-semibold text-brand-dark">{data.nationality}</p>
            </div>
            <div>
              <p className="text-[8px] uppercase text-slate-400">Region</p>
              <p className="text-sm font-semibold text-brand-dark">{data.region}</p>
            </div>
            <div>
              <p className="text-[8px] uppercase text-slate-400">Trust Score</p>
              <p className={clsx("text-sm font-bold", scoreColor)}>{data.score}/100</p>
            </div>
            <div>
              <p className="text-[8px] uppercase text-slate-400">Expires</p>
              <p className="text-sm font-semibold text-brand-dark">{new Date(data.expires_at).toLocaleDateString()}</p>
            </div>
          </div>
        </div>

        <div className="native-card p-5 bg-blue-50 border-blue-100 flex gap-4">
          <MdInfoOutline className="text-blue-500 text-xl flex-shrink-0" />
          <p className="text-xs text-blue-700 leading-relaxed">
            This verification is based on real-time signals from mobile network operators. The trust grade represents the likelihood of the holder&apos;s identity being authentic.
          </p>
        </div>

        <div className="native-card p-5 flex gap-4 items-center">
          <MdHistoryEdu className="text-slate-400 text-xl flex-shrink-0" />
          <div>
            <p className="text-[10px] uppercase text-slate-400">Issuing Authority</p>
            <p className="text-xs font-bold text-brand-dark">VID Trust Network • Pan-African Protocol</p>
          </div>
        </div>
      </section>

      <footer className="mt-4">
        <Link to="/" className="native-button bg-brand-dark text-white w-full">
          Done
        </Link>
      </footer>
    </div>
  )
}

export default VerifyPage
