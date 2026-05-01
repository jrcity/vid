import React, { useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { MdVerified, MdInfoOutline, MdOutlineShare, MdDownload, MdPhoneIphone } from 'react-icons/md'
import { toPng } from 'html-to-image'
import toast from 'react-hot-toast'
import { Certificate } from '../types/vid'
import SEO from '../components/SEO'

const getEmojiFlag = (isoCode: string) => {
  if (!isoCode || isoCode === 'UNKNOWN') return '🌍'
  const codePoints = isoCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0))
  return String.fromCodePoint(...codePoints)
}

const CertificateViewPage: React.FC = () => {
  const { state } = useLocation()
  const navigate = useNavigate()
  const cardRef = useRef<HTMLDivElement>(null)

  const cert = state?.certificate as Certificate

  useEffect(() => {
    if (!cert) {
      navigate('/enroll')
    }
  }, [cert, navigate])

  if (!cert) return null

  const scoreColor = cert.trust_score.score >= 80
    ? 'text-emerald-500'
    : cert.trust_score.score >= 55
      ? 'text-amber-500'
      : 'text-red-500'

  const scoreBg = cert.trust_score.score >= 80
    ? 'bg-emerald-50'
    : cert.trust_score.score >= 55
      ? 'bg-amber-50'
      : 'bg-red-50'

  const handleShare = async () => {
    if (!cardRef.current) return

    try {
      const dataUrl = await toPng(cardRef.current, { cacheBust: true, backgroundColor: '#0F172A' })
      const blob = await (await fetch(dataUrl)).blob()
      const file = new File([blob], `VID_${cert.vid_id}.png`, { type: 'image/png' })

      if (navigator.share) {
        await navigator.share({
          title: 'My Virtual ID Certificate',
          text: `Check out my verified Virtual ID (VID) for ${cert.country.name}. Confidence Grade: ${cert.trust_score.grade}.`,
          files: [file]
        })
      } else {
        // Fallback for browsers that don't support file sharing
        const link = document.createElement('a')
        link.download = `VID_${cert.vid_id}.png`
        link.href = dataUrl
        link.click()
        toast.success('Certificate PNG downloaded for sharing!')
      }
    } catch (err) {
      console.error('Share failed', err)
      toast.error('Failed to generate sharing image')
    }
  }

  const handleDownload = () => {
    // For now, we use the PNG export as the primary download format.
    // A future improvement would be a backend endpoint for high-quality PDFs.
    handleShare()
  }

  return (
    <div className="flex flex-col gap-6 animate-in zoom-in-95 duration-500">
      <SEO title="Your Certificate" description={`Verified VID for ${cert.holder_name} in ${cert.country.name}.`} />

      <header className="text-center">
        <h1 className="text-2xl font-bold text-brand-dark">Your Virtual ID</h1>
        <p className="text-slate-500 text-sm">Successfully generated and verified</p>
      </header>

      {/* The ID Card (Ref for capture) */}
      <div
        ref={cardRef}
        className="native-card text-brand-dark p-7 aspect-[1.6/1] relative overflow-hidden flex flex-col justify-between shadow-2xl border-none"
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
            <p className="text-[10px] uppercase tracking-[0.3em] text-brand-dark/60 font-black">{cert.country.vid_label}</p>
            <h2 className="text-3xl font-black tracking-tight text-brand-dark/50 uppercase">{cert.holder_name}</h2>
          </div>
          <div className="w-16 h-16 bg-white/40 backdrop-blur-xl rounded-2xl flex items-center justify-center text-5xl shadow-xl border border-white/20">
            {getEmojiFlag(cert.country.iso)}
          </div>
        </div>

        <div className="z-10 flex items-end justify-between">
          <div className="space-y-4">
            <div className="space-y-2">
              <p className="text-[9px] uppercase tracking-[0.2em] text-brand-dark/50 font-bold">Network Corroboration</p>
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {cert.masked_phones?.map((p, i) => (
                  <p key={i} className="text-[11px] font-mono text-brand-dark bg-black/5 px-3 py-1 rounded-lg border border-black/5 backdrop-blur-sm">{p}</p>
                ))}
              </div>
            </div>
            <div className="flex gap-8">
              <div>
                <p className="text-[9px] uppercase tracking-[0.2em] text-brand-dark/50 font-bold">ID Number</p>
                <p className="font-mono text-sm tracking-widest text-brand-dark font-black">{cert.vid_id}</p>
              </div>
              <div>
                <p className="text-[9px] uppercase tracking-[0.2em] text-brand-dark/50 font-bold">Region</p>
                <p className="text-xs font-black tracking-wide text-brand-dark">{cert.country.region}</p>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-3">
            <div className="bg-white p-1 rounded-xl shadow-2xl border-4 border-black/5">
              <img src={cert.qr_data_url} alt="QR Code" className="w-16 h-16" />
            </div>
          </div>
        </div>

        {/* Polished Gold Border */}
        <div className="absolute inset-0 border-[1.5px] border-white/30 rounded-native pointer-events-none" />
      </div>

      {/* Trust Score Breakdown */}
      <section className="space-y-4">
        <div className={`native-card p-4 ${scoreBg} border-none flex items-center justify-between`}>
          <div className="flex items-center gap-3">
            <div className="relative w-14 h-14 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90">
                <circle cx="28" cy="28" r="24" fill="none" stroke="currentColor" strokeWidth="4" className="text-slate-200" />
                <circle
                  cx="28" cy="28" r="24" fill="none" stroke="currentColor" strokeWidth="4"
                  strokeDasharray="150"
                  strokeDashoffset={150 - (150 * cert.trust_score.score) / 100}
                  className={scoreColor}
                />
              </svg>
              <span className={`absolute font-bold text-sm ${scoreColor}`}>{cert.trust_score.score}</span>
            </div>
            <div>
              <h3 className="font-bold text-brand-dark leading-tight">{cert.trust_score.grade}</h3>
              <p className="text-xs text-slate-500">Trust Confidence Level</p>
            </div>
          </div>
          <MdVerified className={`text-2xl ${scoreColor}`} />
        </div>

        <div className="native-card p-6 space-y-4">
          <h3 className="font-bold text-brand-dark flex items-center gap-2">
            <MdInfoOutline className="text-slate-400" />
            Verification Breakdown
          </h3>
          <p className="text-sm text-slate-600 leading-relaxed italic">
            "{cert.trust_score.explanation}"
          </p>

          <div className="space-y-4 pt-4 border-t border-slate-50">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest">
              <MdPhoneIphone />
              Signal Corroboration
            </div>

            {/* Simulation of multi-SIM breakdown if provided by backend */}
            <div className="space-y-3">
              {cert.trust_score.signals.map((sig, i) => (
                <div key={i} className="flex flex-col gap-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">{sig.api_name}</span>
                    <span className={sig.passed ? 'text-emerald-600 font-medium' : 'text-amber-600 font-medium'}>
                      {sig.display_value}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 leading-tight">{sig.detail}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <footer className="grid grid-cols-2 gap-4 pb-8">
        <button
          onClick={handleShare}
          className="native-button bg-slate-100 text-slate-600 flex gap-2 items-center"
        >
          <MdOutlineShare /> Share
        </button>
        <button
          onClick={handleDownload}
          className="native-button bg-brand-dark text-white flex gap-2 items-center"
        >
          <MdDownload /> Download
        </button>
      </footer>
    </div>
  )
}

export default CertificateViewPage
