import React, { useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { MdVerified, MdInfoOutline, MdOutlineShare, MdDownload, MdPhoneIphone } from 'react-icons/md'
import toast from 'react-hot-toast'
import { Certificate } from '../types/vid'
import SEO from '../components/SEO'
import useTranslation from '../hooks/useTranslation'

const getEmojiFlag = (isoCode: string) => {
  if (!isoCode || isoCode === 'UNKNOWN') return '🌍'
  const codePoints = isoCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0))
  return String.fromCodePoint(...codePoints)
}

const CertificateViewPage: React.FC = () => {
  const { t } = useTranslation()
  const { state } = useLocation()
  const navigate = useNavigate()
  const cardRef = useRef<HTMLDivElement>(null)

  const cert = state?.certificate as Certificate
  const biometricPassed = (state?.biometric_passed as boolean | undefined) ?? false

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
    const publicUrl = (import.meta.env.VITE_APP_URL as string) || window.location.origin
    const normalizedOrigin = publicUrl.replace(/\/$/, '')
    const verifyUrl = `${normalizedOrigin}/verify/${cert.vid_id}`
    try {
      if (navigator.share) {
        await navigator.share({
          title: t('pdf.title'),
          text: `Verify my identity at ${verifyUrl}`,
          url: verifyUrl
        })
      } else if (navigator.clipboard) {
        await navigator.clipboard.writeText(verifyUrl)
        toast.success(t('toasts.link_copied'))
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      if (navigator.clipboard) {
        try {
          await navigator.clipboard.writeText(verifyUrl)
          toast.success(t('toasts.link_copied'))
        } catch {
          toast.error(t('toasts.copy_error'))
        }
      } else {
        toast.error(t('toasts.share_error') + verifyUrl)
      }
    }
  }

  const handleDownload = async () => {
    const loadingToast = toast.loading(t('pdf.generating'))
    try {
      const { jsPDF } = await import('jspdf')
      
      const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
      
      doc.setFillColor(191, 149, 63)
      doc.rect(0, 0, 210, 45, 'F')
      doc.setFillColor(170, 119, 28)
      doc.rect(0, 40, 210, 5, 'F')
      
      doc.setTextColor(5, 5, 5)
      doc.setFontSize(22)
      doc.setFont('helvetica', 'bold')
      doc.text(t('pdf.title'), 105, 22, { align: 'center' })
      
      doc.setFontSize(11)
      doc.setTextColor(80, 80, 80)
      doc.text(cert.country.vid_label, 105, 32, { align: 'center' })
      
      doc.setFontSize(16)
      doc.setTextColor(5, 5, 5)
      doc.setFont('helvetica', 'bold')
      doc.text(cert.holder_name.toUpperCase(), 105, 55, { align: 'center' })
      
      doc.setFillColor(cert.trust_score.score >= 80 ? 209 : cert.trust_score.score >= 55 ? 245 : 239,
                     cert.trust_score.score >= 80 ? 252 : cert.trust_score.score >= 55 ? 243 : 194,
                     cert.trust_score.score >= 80 ? 230 : cert.trust_score.score >= 55 ? 133 : 128)
      doc.roundedRect(70, 65, 70, 30, 3, 3, 'F')
      doc.setFontSize(24)
      doc.setTextColor(cert.trust_score.score >= 80 ? 16 : cert.trust_score.score >= 55 ? 180 : 204,
                        cert.trust_score.score >= 80 ? 185 : cert.trust_score.score >= 55 ? 126 : 68,
                        cert.trust_score.score >= 80 ? 99 : cert.trust_score.score >= 55 ? 3 : 76)
      doc.setFont('helvetica', 'bold')
      doc.text(`${cert.trust_score.score}/100`, 105, 78, { align: 'center' })
      doc.setFontSize(9)
      doc.text(cert.trust_score.grade, 105, 88, { align: 'center' })
      
      let y = 110
      doc.setFontSize(12)
      doc.setTextColor(5, 5, 5)
      doc.setFont('helvetica', 'bold')
      doc.text(t('pdf.identity_details'), 20, y)
      y += 10
      
      doc.setFontSize(10)
      doc.setTextColor(80, 80, 80)
      doc.setFont('helvetica', 'normal')
      
      const details = [
        [t('pdf.id_number'), cert.vid_id],
        [t('pdf.country'), `${cert.country.name} (${cert.country.iso})`],
        [t('pdf.region'), cert.country.region],
        [t('pdf.phone_numbers'), cert.masked_phones.join(', ')],
        [t('pdf.issued'), new Date(cert.issued_at).toLocaleDateString()],
        [t('pdf.expires'), new Date(cert.expires_at).toLocaleDateString()],
        [t('pdf.cert_hash'), cert.certificate_hash],
      ]
      
      for (const [label, value] of details) {
        doc.setFont('helvetica', 'bold')
        doc.text(label, 20, y)
        doc.setFont('helvetica', 'normal')
        const maxWidth = 120
        const lines = doc.splitTextToSize(String(value), maxWidth)
        doc.text(lines, 75, y)
        y += lines.length * 6 + 2
      }
      
      y += 5
      doc.setFontSize(12)
      doc.setTextColor(5, 5, 5)
      doc.setFont('helvetica', 'bold')
      doc.text(t('pdf.verification_signals'), 20, y)
      y += 10
      
      for (const sig of cert.trust_score.signals) {
        doc.setFontSize(9)
        doc.setTextColor(80, 80, 80)
        doc.setFont('helvetica', 'bold')
        doc.text(sig.api_name, 25, y)
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(sig.passed ? 16 : 204, sig.passed ? 185 : 68, sig.passed ? 99 : 76)
        doc.text(sig.display_value, 100, y)
        y += 5
        doc.setTextColor(140, 140, 140)
        const detailLines = doc.splitTextToSize(sig.detail, 140)
        doc.setFontSize(7)
        doc.text(detailLines, 30, y)
        y += detailLines.length * 4 + 3
      }
      
      if (cert.qr_data_url) {
        try {
          const qrY = Math.min(y + 5, 240)
          doc.addImage(cert.qr_data_url, 'PNG', 75, qrY, 60, 60)
        } catch {
          // Skip QR if image fails
        }
      }
      
      doc.setFontSize(7)
      doc.setTextColor(150, 150, 150)
      doc.text(t('pdf.watermark'), 105, 290, { align: 'center' })
      
      doc.save(`VID-${cert.vid_id}.pdf`)
      
      toast.dismiss(loadingToast)
      toast.success(t('pdf.download_success'))
    } catch {
      toast.dismiss(loadingToast)
      toast.error(t('pdf.download_error'))
    }
  }

  return (
    <div className="flex flex-col gap-6 animate-in zoom-in-95 duration-500">
      <SEO title={t('certificate.title')} description={`Verified VID for ${cert.holder_name} in ${cert.country.name}.`} />

      <header className="text-center">
        <h1 className="text-2xl font-bold text-brand-dark">{t('certificate.title')}</h1>
        <p className="text-slate-500 text-sm">{t('certificate.subtitle')}</p>
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
                {t('pdf.watermark')}
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
              <p className="text-[9px] uppercase tracking-[0.2em] text-brand-dark/50 font-bold">{t('certificate.signal_corroboration')}</p>
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {cert.masked_phones?.map((p, i) => (
                  <p key={i} className="text-[11px] font-mono text-brand-dark bg-black/5 px-3 py-1 rounded-lg border border-black/5 backdrop-blur-sm">{p}</p>
                ))}
              </div>
            </div>
            <div className="flex gap-8">
              <div>
                <p className="text-[9px] uppercase tracking-[0.2em] text-brand-dark/50 font-bold">{t('certificate.certificate_id')}</p>
                <p className="font-mono text-sm tracking-widest text-brand-dark font-black">{cert.vid_id}</p>
              </div>
              <div>
                <p className="text-[9px] uppercase tracking-[0.2em] text-brand-dark/50 font-bold">{t('verification.region')}</p>
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
              <p className="text-xs text-slate-500">{t('certificate.trust_confidence')}</p>
            </div>
          </div>
          <MdVerified className={`text-2xl ${scoreColor}`} />
        </div>

        <div className="native-card p-6 space-y-4">
          <h3 className="font-bold text-brand-dark flex items-center gap-2">
            <MdInfoOutline className="text-slate-400" />
            {t('certificate.verification_breakdown')}
          </h3>
          <p className="text-sm text-slate-600 leading-relaxed italic">
            “{cert.trust_score.explanation}”
          </p>

          <div className="space-y-4 pt-4 border-t border-slate-50">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest">
              <MdPhoneIphone />
              {t('certificate.signal_corroboration')}
            </div>

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
              {biometricPassed && (
                <div className="flex flex-col gap-1 pt-2 border-t border-slate-50">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">{t('certificate.biometric_liveness')}</span>
                    <span className="text-emerald-600 font-medium">{t('certificate.biometric_confirmed')}</span>
                  </div>
                  <p className="text-[10px] text-slate-400 leading-tight">{t('certificate.biometric_detail')}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <footer className="grid grid-cols-2 gap-4 pb-8">
        <button
          onClick={handleShare}
          className="native-button bg-slate-100 text-slate-600 flex gap-2 items-center"
        >
          <MdOutlineShare /> {t('certificate.share_certificate')}
        </button>
        <button
          onClick={handleDownload}
          className="native-button bg-brand-dark text-white flex gap-2 items-center"
        >
          <MdDownload /> {t('certificate.download_pdf')}
        </button>
      </footer>
    </div>
  )
}

export default CertificateViewPage
