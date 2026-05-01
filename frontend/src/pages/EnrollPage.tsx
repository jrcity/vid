import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useResolvePhone, useEnroll } from '../hooks/useVidApi'
import { MdAdd, MdRemove, MdPhone, MdPerson, MdCheckCircleOutline } from 'react-icons/md'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { ResolvePhoneResponse, EnrollRequest } from '../types/vid'
import SEO from '../components/SEO'

const getEmojiFlag = (isoCode: string) => {
  if (!isoCode || isoCode === 'UNKNOWN') return '🌍'
  const codePoints = isoCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0))
  return String.fromCodePoint(...codePoints)
}

const EnrollPage: React.FC = () => {
  const navigate = useNavigate()
  const [fullName, setFullName] = useState<string>('')
  const [phones, setPhones] = useState<string[]>([''])
  const [consent, setConsent] = useState<boolean>(false)
  
  // Track detected countries for all numbers
  const [detectedCountries, setDetectedCountries] = useState<(ResolvePhoneResponse | null)[]>([null])

  const resolvePhone = useResolvePhone()
  const enroll = useEnroll()

  // Efficient country detection for any number change
  const handlePhoneChange = (index: number, value: string) => {
    const newPhones = [...phones]
    newPhones[index] = value
    setPhones(newPhones)

    // Debounced resolve for each number
    if (value.length >= 7) {
      const timeoutId = setTimeout(() => {
        resolvePhone.mutate(value, {
          onSuccess: (data) => {
            setDetectedCountries(prev => {
              const next = [...prev]
              next[index] = data.valid ? data : null
              return next
            })
          }
        })
      }, 500)
      return () => clearTimeout(timeoutId)
    } else {
      setDetectedCountries(prev => {
        const next = [...prev]
        next[index] = null
        return next
      })
    }
  }

  const addPhone = () => {
    if (phones.length < 3) {
      setPhones([...phones, ''])
      setDetectedCountries([...detectedCountries, null])
    }
  }

  const removePhone = (index: number) => {
    if (phones.length > 1) {
      const newPhones = [...phones]
      newPhones.splice(index, 1)
      setPhones(newPhones)
      
      const newDetected = [...detectedCountries]
      newDetected.splice(index, 1)
      setDetectedCountries(newDetected)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!consent) {
      toast.error('Explicit consent is required to proceed')
      return
    }

    const enrollData: EnrollRequest = {
      full_name: fullName,
      phone_numbers: phones.map(n => ({ number: n })),
      consent: consent
    }

    enroll.mutate(enrollData, {
      onSuccess: (certificate) => {
        toast.success('Enrollment successful!')
        navigate('/certificate', { state: { certificate } })
      },
      onError: (error: any) => {
        const msg = error.response?.data?.detail || 'Enrollment failed'
        toast.error(msg)
      }
    })
  }

  // Primary country info for the verified badge
  const primaryCountry = detectedCountries[0]

  return (
    <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <SEO title="Enroll" description="Start your journey to a secure digital identity with VID." />
      
      <header>
        <h1 className="text-2xl font-bold text-brand-dark">Enroll in VID</h1>
        <p className="text-slate-500 text-sm">Join the secure digital identity network.</p>
      </header>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-slate-600 px-1">Full Name</label>
          <div className="relative">
            <MdPerson className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-xl" />
            <input
              type="text"
              required
              className="native-input pl-12"
              placeholder="e.g. John Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <label className="text-sm font-semibold text-slate-600">Mobile Numbers (Up to 3)</label>
            <button
              type="button"
              onClick={addPhone}
              disabled={phones.length >= 3}
              className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 disabled:opacity-30 transition-all active:scale-90"
            >
              <MdAdd />
            </button>
          </div>
          
          <div className="space-y-3">
            {phones.map((phone, index) => (
              <div key={index} className="relative flex gap-2">
                <div className="relative flex-1">
                  {detectedCountries[index] ? (
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 w-7 h-7 bg-white rounded-full flex items-center justify-center text-lg shadow-sm z-10 border border-slate-100">
                      {getEmojiFlag(detectedCountries[index]!.iso_code)}
                    </div>
                  ) : (
                    <MdPhone className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-xl" />
                  )}
                  <input
                    type="tel"
                    required
                    className={clsx(
                      "native-input",
                      detectedCountries[index] ? "pl-14" : "pl-12"
                    )}
                    placeholder={index === 0 ? "Primary Number (+234...)" : "Additional Number"}
                    value={phone}
                    onChange={(e) => handlePhoneChange(index, e.target.value)}
                  />
                </div>
                {index > 0 && (
                  <button
                    type="button"
                    onClick={() => removePhone(index)}
                    className="w-14 h-14 rounded-2xl bg-red-50 text-red-500 flex items-center justify-center flex-shrink-0 active:scale-95 transition-all"
                  >
                    <MdRemove />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {primaryCountry && (
          <div className="px-1 animate-in slide-in-from-top-2 duration-300">
            <div className="flex items-center gap-2 text-emerald-600 text-xs font-bold uppercase tracking-wider">
              <MdCheckCircleOutline className="text-sm" />
              Verified for {primaryCountry.country_name} • {primaryCountry.vid_label}
            </div>
          </div>
        )}

        {/* Explicit Consent Section */}
        <div className="native-card p-5 bg-blue-50 border-blue-100 space-y-4">
          <div className="flex items-center gap-2 text-blue-800 font-bold text-sm">
            <MdCheckCircleOutline />
            Privacy Consent
          </div>
          <p className="text-xs text-blue-700 leading-relaxed">
            By checking the box below, I explicitly authorize VID to request network signals (SIM stability, KYC match, and location) from mobile network operators to verify my identity. 
            <br /><br />
            <strong>I understand that no raw personal data will be stored on VID servers.</strong>
          </p>
          <div className="flex items-center gap-3 pt-2">
            <input
              type="checkbox"
              id="consent"
              required
              className="w-6 h-6 rounded-lg border-blue-300 text-brand-accent focus:ring-brand-accent cursor-pointer"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            <label htmlFor="consent" className="text-sm font-semibold text-blue-900 cursor-pointer">
              I agree and provide my consent
            </label>
          </div>
        </div>

        <button
          type="submit"
          disabled={enroll.isPending}
          className={clsx(
            "native-button mt-2 text-white shadow-lg shadow-brand-accent/20 relative overflow-hidden",
            enroll.isPending ? "bg-brand-dark/80" : "bg-brand-accent"
          )}
        >
          {enroll.isPending ? "Processing..." : "Generate My VID"}
        </button>
      </form>

      {/* Premium Security Loader Overlay */}
      {enroll.isPending && (
        <div className="fixed inset-0 z-50 bg-brand-dark/95 backdrop-blur-md flex flex-col items-center justify-center p-8 animate-in fade-in duration-500">
          <div className="relative w-48 h-48 flex items-center justify-center">
            {/* Pulsing Outer Rings */}
            <div className="absolute inset-0 border-2 border-brand-accent/20 rounded-full animate-[ping_3s_linear_infinite]" />
            <div className="absolute inset-4 border-2 border-brand-accent/40 rounded-full animate-[ping_2s_linear_infinite]" />
            
            {/* Main Scanner Ring */}
            <div className="absolute inset-0 border-[3px] border-transparent border-t-brand-accent rounded-full animate-spin" />
            
            {/* Central Icon */}
            <div className="relative z-10 flex flex-col items-center gap-2">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-brand-accent animate-pulse">
                <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor" />
              </svg>
              <div className="text-brand-accent font-black tracking-tighter text-xl">VID</div>
            </div>

            {/* Scanning Line */}
            <div className="absolute left-0 right-0 h-[1px] bg-brand-accent/50 shadow-[0_0_15px_#BF953F] animate-[scan_2s_ease-in-out_infinite]" />
          </div>

          <div className="mt-12 text-center space-y-4 max-w-xs">
            <h2 className="text-white font-bold text-xl tracking-tight">Security Verification</h2>
            <div className="flex flex-col gap-2">
              <p className="text-brand-accent/70 text-[10px] uppercase font-black tracking-[0.2em] animate-pulse">
                Accessing CAMARA Network Signals
              </p>
              <div className="flex justify-center gap-1">
                <div className="w-1 h-1 bg-brand-accent rounded-full animate-bounce [animation-delay:-0.3s]" />
                <div className="w-1 h-1 bg-brand-accent rounded-full animate-bounce [animation-delay:-0.15s]" />
                <div className="w-1 h-1 bg-brand-accent rounded-full animate-bounce" />
              </div>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              We are verifying your SIM stability, KYC consistency, and location with regional operators. 
              <br /><br />
              <span className="text-[10px] text-slate-500 italic">This process usually takes 15-20 seconds for secure network handshakes.</span>
            </p>
          </div>

          {/* Background Text Stream Simulation */}
          <div className="absolute bottom-8 left-8 right-8 overflow-hidden h-24 opacity-20 pointer-events-none">
            <div className="text-[8px] font-mono text-brand-accent space-y-1 animate-[slide-up_10s_linear_infinite]">
              <p>QUERYING nokia-nac-v1.api.service...</p>
              <p>ENCRYPTING certificate_hash(sha256)...</p>
              <p>VERIFYING location_radius(200km)...</p>
              <p>MATCHING kyc_profile(encrypted_data)...</p>
              <p>CHECKING sim_swap_status(current_session)...</p>
              <p>ESTABLISHING sovereign_identity_link...</p>
              <p>RANDOM_FOREST_INFERENCE: processing_signals...</p>
              <p>TRUST_SCORE_CALCULATED: finalized...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default EnrollPage
