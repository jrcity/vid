import React, { useState, useEffect, useRef } from 'react'
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

const formatApiError = (error: unknown): string => {
  if (!error) return 'Unknown error occurred'
  if (typeof error === 'string') return error
  if (Array.isArray(error)) {
    return error
      .map((item) => {
        if (!item) return ''
        if (typeof item === 'string') return item
        if (typeof item === 'object' && item !== null && 'msg' in item) {
          return (item as { msg?: string }).msg || JSON.stringify(item)
        }
        return JSON.stringify(item)
      })
      .filter(Boolean)
      .join('; ')
  }
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return (error as { message?: string }).message || JSON.stringify(error)
  }
  if (typeof error === 'object' && error !== null) {
    return JSON.stringify(error)
  }
  return String(error)
}

const EnrollPage: React.FC = () => {
  const navigate = useNavigate()
  const [fullName, setFullName] = useState<string>('')
  const [phones, setPhones] = useState<string[]>([''])
  const [consent, setConsent] = useState<boolean>(false)
  
  // Track detected countries for all numbers
  const [detectedCountries, setDetectedCountries] = useState<(ResolvePhoneResponse | null)[]>([null])
  const phoneResolveTimers = useRef<Record<number, ReturnType<typeof setTimeout> | null>>({})

  const resolvePhone = useResolvePhone()
  const enroll = useEnroll()

  // Efficient country detection for any number change
  const handlePhoneChange = (index: number, value: string) => {
    const newPhones = [...phones]
    newPhones[index] = value
    setPhones(newPhones)

    if (phoneResolveTimers.current[index]) {
      clearTimeout(phoneResolveTimers.current[index] as ReturnType<typeof setTimeout>)
    }

    if (value.length >= 7) {
      phoneResolveTimers.current[index] = setTimeout(() => {
        resolvePhone.mutate(value, {
          onSuccess: (data) => {
            setDetectedCountries(prev => {
              const next = [...prev]
              next[index] = data.valid ? data : null
              return next
            })
          },
          onError: () => {
            setDetectedCountries(prev => {
              const next = [...prev]
              next[index] = null
              return next
            })
          },
        })
      }, 500)
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

  useEffect(() => {
    return () => {
      Object.values(phoneResolveTimers.current).forEach(timer => {
        if (timer) clearTimeout(timer)
      })
    }
  }, [])

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
      onError: (error: unknown) => {
        const errObj = error as { response?: { data?: any } }
        const msg = formatApiError(errObj.response?.data?.detail ?? errObj.response?.data ?? error)
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
          {enroll.isPending ? (
            <div className="flex items-center gap-3 z-10">
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span className="animate-pulse">Analyzing SIM Signals...</span>
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full animate-[shimmer_1.5s_infinite]" />
            </div>
          ) : (
            "Generate My VID"
          )}
        </button>
      </form>
    </div>
  )
}

export default EnrollPage
