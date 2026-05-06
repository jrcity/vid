import React, { useState, useEffect, useRef, useCallback, memo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useResolvePhone, useEnroll } from '../hooks/useVidApi'
import { MdAdd, MdRemove, MdPhone, MdPerson, MdCheckCircleOutline } from 'react-icons/md'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { ResolvePhoneResponse, EnrollRequest } from '../types/vid'
import SEO from '../components/SEO'
import { getEmojiFlag } from '../utils/flags'
import { AxiosError } from 'axios'
import FaceCapture from '../components/face-capture'

/** Represents the current step in the enrollment flow */
type EnrollmentStep = 'form' | 'face';

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

const E164_REGEX = /^\+[1-9]\d{7,14}$/

/** Props for a single phone input row */
interface PhoneRowProps {
  index: number;
  value: string;
  detectedCountry: ResolvePhoneResponse | null;
  isPrimary: boolean;
  onRemove: (index: number) => void;
  onChange: (index: number, value: string) => void;
  onBlur: (index: number) => void;
  error: string;
}

/** Renders a single phone number input with country flag/indicator */
const PhoneRow: React.FC<PhoneRowProps> = memo(({
  index,
  value,
  detectedCountry,
  isPrimary,
  onRemove,
  onChange,
  onBlur,
  error,
}) => (
  <div className="relative flex flex-col gap-2">
    <div className="flex gap-2">
      <div className="relative flex-1">
        {detectedCountry ? (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 w-7 h-7 bg-white rounded-full flex items-center justify-center text-lg shadow-sm z-10 border border-slate-100">
            {getEmojiFlag(detectedCountry.iso_code)}
          </div>
        ) : (
          <MdPhone className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-xl" />
        )}
        <input
          type="tel"
          required
          className={clsx('native-input', detectedCountry ? 'pl-14' : 'pl-12')}
          placeholder={isPrimary ? 'Primary Number (+234...)' : 'Additional Number'}
          value={value}
          onChange={(e) => onChange(index, e.target.value)}
          onBlur={() => onBlur(index)}
        />
      </div>
      {!isPrimary && (
        <button
          type="button"
          onClick={() => onRemove(index)}
          className="w-14 h-14 rounded-2xl bg-red-50 text-red-500 flex items-center justify-center flex-shrink-0 active:scale-95 transition-all"
        >
          <MdRemove />
        </button>
      )}
    </div>
    {error && <p className="text-xs text-red-500 ml-1">{error}</p>}
  </div>
));
PhoneRow.displayName = 'PhoneRow';

const EnrollPage: React.FC = () => {
  const navigate = useNavigate()
  const [fullName, setFullName] = useState<string>('')
  const [phones, setPhones] = useState<string[]>([''])
  const [phoneErrors, setPhoneErrors] = useState<string[]>([''])
  const [nameError, setNameError] = useState('')
  const [consent, setConsent] = useState<boolean>(false)
  const [consentError, setConsentError] = useState(false)
  
  const validatePhone = (phone: string): string => {
    if (!phone) return ''
    if (!E164_REGEX.test(phone)) return 'Enter number with country code e.g. +2348031234567'
    return ''
  }

  const validateName = (name: string): string => {
    if (!name) return ''
    if (name.length < 2 || /\d/.test(name)) return 'Enter your full name (letters only)'
    return ''
  }

  const handlePhoneBlur = (index: number) => {
    const error = validatePhone(phones[index])
    setPhoneErrors(prev => {
      const next = [...prev]
      next[index] = error
      return next
    })
  }
  
  // Track detected countries for all numbers
  const [detectedCountries, setDetectedCountries] = useState<(ResolvePhoneResponse | null)[]>([null])
  const [location, setLocation] = useState<{ latitude: number, longitude: number, radius: number } | null>(null)
  const [isLocating, setIsLocating] = useState(false)

  // FE-01: Face verification step state
  const [step, setStep] = useState<EnrollmentStep>('form');
  const faceCaptureRef = useRef<HTMLDivElement>(null);
  const consentRef = useRef<HTMLDivElement>(null);

  const enrollTimeoutRef = useRef<number | null>(null);

  const clearEnrollTimeout = useCallback(() => {
    if (enrollTimeoutRef.current) {
      clearTimeout(enrollTimeoutRef.current);
      enrollTimeoutRef.current = null;
    }
  }, []);

  const resolvePhone = useResolvePhone()
  const enroll = useEnroll()

  // Debounced phone resolution via useEffect
  useEffect(() => {
    const timers = phones.map((phone, index) => {
      if (phone.length >= 7) {
        return setTimeout(() => {
          resolvePhone.mutate(phone, {
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
          if (prev[index] === null) return prev
          const next = [...prev]
          next[index] = null
          return next
        })
        return null
      }
    })

    return () => {
      timers.forEach(timer => {
        if (timer) clearTimeout(timer)
      })
    }
  }, [phones, resolvePhone.mutate])

  const handlePhoneChange = (index: number, value: string) => {
    const newPhones = [...phones]
    newPhones[index] = value
    setPhones(newPhones)
    setPhoneErrors(prev => {
      const next = [...prev]
      next[index] = ''
      return next
    })
  }

  const addPhone = () => {
    if (phones.length < 3) {
      setPhones([...phones, ''])
      setDetectedCountries([...detectedCountries, null])
      setPhoneErrors([...phoneErrors, ''])
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

      const newErrors = [...phoneErrors]
      newErrors.splice(index, 1)
      setPhoneErrors(newErrors)
    }
  }


  const handleLocationShare = () => {
    setIsLocating(true)
    if (!navigator.geolocation) {
      toast.error('Geolocation is not supported by your browser')
      setIsLocating(false)
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          radius: position.coords.accuracy || 10000
        })
        setIsLocating(false)
        toast.success('Location verified for trust boost!')
      },
      (_error) => {
        toast.error('Could not access location. Using country default.')
        setIsLocating(false)
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }


  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!consent) {
      setConsentError(true)
      consentRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      return
    }
    setConsentError(false)
    
    if (!fullName || phones.some(p => !p)) {
      toast.error('Please fill all required fields')
      return
    }
    
    const hasInvalidPhone = phones.some(p => !E164_REGEX.test(p))
    if (hasInvalidPhone) {
      toast.error('Please fix phone number errors')
      return
    }
    
    const nameErr = validateName(fullName)
    if (nameErr) {
      setNameError(nameErr)
      return
    }
    
    setStep('face')
  }

  // Auto-scroll to face capture when step changes
  useEffect(() => {
    if (step === 'face') {
      setTimeout(() => {
        faceCaptureRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }, 100)
    }
  }, [step])

  const handleBiometricResult = (passed: boolean | null) => {
    proceedEnroll(passed)
  }

  // Cleanup timeout on unmount
  useEffect(() => {
    return clearEnrollTimeout;
  }, [clearEnrollTimeout]);

  const proceedEnroll = (bioPassed: boolean | null) => {
    clearEnrollTimeout();

    const payload: EnrollRequest = {
      full_name: fullName,
      phone_numbers: phones.map((p, i) => ({
        number: p,
        is_primary: i === 0,
        country_iso: detectedCountries[i]?.iso_code,
      })),
      consent,
      location: location || undefined,
      // FE-01: Only send boolean — no biometric data leaves this device
      biometric_passed: bioPassed === true ? true : undefined,
    };

    // 30s timeout for enrollment API (CAMARA calls can take 15-20s)
    enrollTimeoutRef.current = setTimeout(() => {
      enroll.reset();
      toast.error('Enrollment timed out. Please try again.');
      setStep('form');
      enrollTimeoutRef.current = null;
    }, 30000);

    enroll.mutate(payload, {
      onSuccess: (certificate) => {
        clearEnrollTimeout();
        toast.success('Enrollment successful!');
        navigate('/certificate', {
          state: { certificate, biometric_passed: bioPassed === true },
        });
      },
      onError: (error: AxiosError) => {
        clearEnrollTimeout();
        const data = error.response?.data as { detail?: string } | undefined;
        const msg = formatApiError(data?.detail ?? error.response?.data ?? error.message);
        toast.error(msg);
        // Allow retry: go back to form step
        setStep('form');
      },
    });
  };

  // Primary country info for the verified badge
  const primaryCountry = detectedCountries[0]

  return (
    <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <SEO title="Enroll" description="Start your journey to a secure digital identity with VID." />
      
      <header>
        <h1 className="text-2xl font-bold text-brand-dark">Enroll in VID</h1>
        <p className="text-slate-500 text-sm">Join the secure digital identity network.</p>
      </header>

      <form onSubmit={handleFormSubmit} className="flex flex-col gap-6">
        <div className={clsx('flex flex-col gap-6', step === 'face' && 'opacity-40 pointer-events-none select-none')}>
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
                onBlur={() => setNameError(validateName(fullName))}
              />
            </div>
            {nameError && <p className="text-xs text-red-500 mt-1 px-1">{nameError}</p>}
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
                <PhoneRow
                  key={index}
                  index={index}
                  value={phone}
                  detectedCountry={detectedCountries[index]}
                  isPrimary={index === 0}
                  onRemove={removePhone}
                  onChange={handlePhoneChange}
                  onBlur={handlePhoneBlur}
                  error={phoneErrors[index] || ''}
                />
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

            <div ref={consentRef} className="flex items-center gap-3 py-2">
              <input
                type="checkbox"
                id="consent"
                required
                className="w-6 h-6 rounded-lg border-blue-300 text-brand-accent focus:ring-brand-accent cursor-pointer"
                checked={consent}
                onChange={(e) => { setConsent(e.target.checked); setConsentError(false) }}
              />
              <label htmlFor="consent" className="text-sm font-semibold text-blue-900 cursor-pointer">
                I agree and provide my consent
              </label>
            </div>
            {consentError && <p className="text-xs text-red-500 font-medium mt-1">You must consent to continue</p>}
          </div>

          {/* Location Boost */}
          <div className="native-card p-6 bg-slate-50/50 border-dashed border-2 border-slate-200">
            <div className="flex items-start gap-4">
              <div className={clsx(
                "w-12 h-12 rounded-2xl flex items-center justify-center text-2xl transition-all duration-500",
                location ? "bg-emerald-100 text-emerald-600 scale-110" : "bg-slate-200 text-slate-500"
              )}>
                {isLocating ? <div className="w-6 h-6 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" /> : <MdCheckCircleOutline />}
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-brand-dark">Location Boost (Optional)</h3>
                <p className="text-sm text-slate-500 mb-3">
                  Verify your precise location to increase your VID trust grade.
                </p>
                {location ? (
                  <div className="text-xs font-mono text-emerald-600 bg-emerald-50 p-2 rounded-lg inline-block animate-in slide-in-from-left duration-300">
                    📍 {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)} (±{Math.round(location.radius)}m)
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={handleLocationShare}
                    disabled={isLocating}
                    className="text-xs font-bold text-brand-accent hover:underline flex items-center gap-1"
                  >
                    {isLocating ? 'Accessing GPS...' : 'Share location for +4 pts bonus'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* FE-01: Face Verification Step */}
        {step === 'face' && (
          <div ref={faceCaptureRef} className="animate-in fade-in slide-in-from-bottom-6">
            <FaceCapture onBiometricResult={handleBiometricResult} />
          </div>
        )}

        <button
          type="submit"
          disabled={enroll.isPending || step === 'face' || !fullName || phones.some(p => !E164_REGEX.test(p)) || !consent}
          className={clsx(
            "native-button mt-2 text-white shadow-lg shadow-brand-accent/20 relative overflow-hidden",
            step === 'face' ? "bg-brand-dark/80" : enroll.isPending ? "bg-brand-dark/80" : "bg-brand-accent"
          )}
        >
          {step === 'face'
            ? "Verifying face..."
            : enroll.isPending
              ? "Processing..."
              : "Continue to Face Verification"}
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
