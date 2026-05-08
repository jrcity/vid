import React, { useState, useEffect, useRef, useCallback, memo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useResolvePhone, useEnroll } from '../hooks/useVidApi'
import { 
  MdAdd, 
  MdRemove, 
  MdPhone, 
  MdPerson, 
  MdCheckCircleOutline, 
  MdNavigateNext, 
  MdNavigateBefore,
  MdEmail,
  MdCalendarToday,
  MdWc,
  MdLocationOn,
  MdHome,
  MdFingerprint,
  MdExpandMore,
  MdCheck,
  MdMale,
  MdFemale,
  MdTransgender
} from 'react-icons/md'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { ResolvePhoneResponse, EnrollRequest } from '../types/vid'
import SEO from '../components/SEO'
import { getEmojiFlag } from '../utils/flags'
import { AxiosError } from 'axios'
import FaceCapture from '../components/face-capture'
import useTranslation from '../hooks/useTranslation'

type EnrollmentStep = 'personal' | 'identity' | 'phone' | 'consent' | 'face';

const E164_REGEX = /^\+[1-9]\d{7,14}$/

const Stepper: React.FC<{ currentStep: number; totalSteps: number }> = ({ currentStep, totalSteps }) => {
  const { t } = useTranslation();
  const stepKeys = ['step_personal', 'step_identity', 'step_phone', 'step_consent', 'step_face'];
  
  return (
    <div className="w-full mb-8">
      <div className="flex justify-between mb-2">
        {stepKeys.map((key, index) => (
          <div key={index} className="flex flex-col items-center flex-1">
            <div className={clsx(
              "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 z-10",
              currentStep > index ? "bg-emerald-500 text-white" : 
              currentStep === index ? "bg-brand-accent text-white scale-110 shadow-lg shadow-brand-accent/30" : 
              "bg-slate-200 text-slate-500"
            )}>
              {currentStep > index ? <MdCheckCircleOutline className="text-lg" /> : index + 1}
            </div>
            <span className={clsx(
              "text-[10px] mt-1 font-bold uppercase tracking-tighter hidden sm:block",
              currentStep === index ? "text-brand-dark" : "text-slate-400"
            )}>
              {t(`enroll.${key}`)}
            </span>
          </div>
        ))}
      </div>
      <div className="relative w-full h-1 bg-slate-100 rounded-full overflow-hidden">
        <div 
          className="absolute h-full bg-brand-accent transition-all duration-500 ease-out"
          style={{ width: `${(currentStep / (totalSteps - 1)) * 100}%` }}
        />
      </div>
    </div>
  )
}

const CustomDropdown = ({ 
  value, 
  onChange, 
  options, 
  placeholder, 
  icon, 
  className 
}: { 
  value: string; 
  onChange: (v: string) => void; 
  options: { value: string; label: string }[]; 
  placeholder: string;
  icon?: React.ReactNode;
  className?: string;
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false);
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const selected = options.find(o => o.value === value);

  return (
    <div className={clsx("relative flex-1", className)} ref={ref}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full h-14 px-4 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-between transition-all hover:border-slate-300"
      >
        <div className="flex items-center gap-2 truncate">
          {icon && <span className="text-slate-400 text-xl">{icon}</span>}
          <span className={clsx("text-sm truncate", !selected && "text-slate-400")}>
            {selected ? selected.label : placeholder}
          </span>
        </div>
        <MdExpandMore className={clsx("text-slate-400 transition-transform flex-shrink-0", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 z-50 bg-white rounded-2xl shadow-2xl border border-slate-100 py-2 max-h-60 overflow-y-auto animate-in fade-in slide-in-from-top-2 duration-200 no-scrollbar">
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => { onChange(opt.value); setIsOpen(false) }}
              className={clsx(
                "w-full px-4 py-2.5 text-left text-sm transition-colors",
                value === opt.value ? "bg-brand-accent/10 text-brand-accent font-bold" : "text-slate-600 hover:bg-slate-50"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

const EnrollPage = () => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [stepIndex, setStepIndex] = useState(0)
  
  // Form State
  const [givenName, setGivenName] = useState('')
  const [familyName, setFamilyName] = useState('')
  
  // Split Birthdate State
  const [birthDay, setBirthDay] = useState('')
  const [birthMonth, setBirthMonth] = useState('')
  const [birthYear, setBirthYear] = useState('')
  
  const [email, setEmail] = useState('')
  const [gender, setGender] = useState<'MALE' | 'FEMALE' | 'OTHER' | ''>('')
  const [address, setAddress] = useState('')
  
  const [hasId, setHasId] = useState<boolean | null>(null)
  const [idDocument, setIdDocument] = useState('')
  
  const [phones, setPhones] = useState<string[]>([''])
  const [detectedCountries, setDetectedCountries] = useState<(ResolvePhoneResponse | null)[]>([null])
  
  const [consent, setConsent] = useState(false)
  const [consentError, setConsentError] = useState(false)
  const [location, setLocation] = useState<{ latitude: number, longitude: number, radius: number } | null>(null)
  const [isLocating, setIsLocating] = useState(false)
  
  const [biometricPassed, setBiometricPassed] = useState<boolean | undefined>(undefined)

  const resolvePhone = useResolvePhone()
  const enroll = useEnroll()
  const steps: EnrollmentStep[] = ['personal', 'identity', 'phone', 'consent', 'face']

  // Auto-detect country
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
            }
          })
        }, 500)
      }
      return null
    })
    return () => timers.forEach(t => t && clearTimeout(t))
  }, [phones, resolvePhone.mutate])

  const validateCurrentStep = () => {
    switch (steps[stepIndex]) {
      case 'personal':
        if (!givenName || !familyName || !address) {
          toast.error(t('errors.fill_required'))
          return false
        }
        return true
      case 'identity':
        if (hasId === null) {
          toast.error('Please select an option')
          return false
        }
        if (hasId && !idDocument) {
          toast.error(t('errors.fill_required'))
          return false
        }
        return true
      case 'phone':
        if (phones.some(p => !E164_REGEX.test(p))) {
          toast.error(t('errors.fix_phone_errors'))
          return false
        }
        return true
      case 'consent':
        if (!consent) {
          setConsentError(true)
          toast.error(t('enroll.consent_required'))
          return false
        }
        setConsentError(false)
        return true
      default:
        return true
    }
  }

  const nextStep = () => {
    if (validateCurrentStep()) {
      if (stepIndex < steps.length - 1) setStepIndex(stepIndex + 1)
    }
  }

  const prevStep = () => {
    if (stepIndex > 0) setStepIndex(stepIndex - 1)
  }

  const handleBiometricResult = (passed: boolean | null) => {
    setBiometricPassed(passed === true)
    if (passed === true) {
      proceedEnroll(true)
    } else {
      toast.error('Biometric verification failed')
      setStepIndex(0) // Reset to start on failure
    }
  }

  const proceedEnroll = (bioPassed: boolean) => {
    // Format birthdate for backend
    let formattedBirthdate = undefined;
    if (birthDay && birthMonth && birthYear) {
      formattedBirthdate = `${birthYear}-${birthMonth.padStart(2, '0')}-${birthDay.padStart(2, '0')}`;
    }

    const payload: EnrollRequest = {
      given_name: givenName,
      family_name: familyName,
      birthdate: formattedBirthdate,
      email: email || undefined,
      gender: gender as any || undefined,
      address: address,
      id_document: hasId ? idDocument : undefined,
      phone_numbers: phones.map((p, i) => ({ number: p, is_primary: i === 0 })),
      consent,
      location: location || undefined,
      biometric_passed: bioPassed,
      locale: localStorage.getItem('app-language') || 'en'
    }

    enroll.mutate(payload, {
      onSuccess: (certificate) => {
        toast.success(t('enroll.success_message'))
        navigate('/certificate', { state: { certificate, biometric_passed: bioPassed } })
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || t('errors.generic'))
        setStepIndex(0)
      }
    })
  }

  const renderStep = () => {
    const animationClass = "animate-in slide-in-from-right-8 duration-500 fade-in"
    
    switch (steps[stepIndex]) {
      case 'personal':
        const genderOptions = [
          { value: 'MALE', label: t('enroll.gender_male'), icon: <MdMale /> },
          { value: 'FEMALE', label: t('enroll.gender_female'), icon: <MdFemale /> },
          { value: 'OTHER', label: t('enroll.gender_other'), icon: <MdTransgender /> },
        ]

        // Date options
        const days = Array.from({ length: 31 }, (_, i) => ({ value: String(i + 1), label: String(i + 1) }))
        const months = [
          "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ].map((m, i) => ({ value: String(i + 1), label: m }))
        const years = Array.from({ length: 100 }, (_, i) => {
          const y = new Date().getFullYear() - i;
          return { value: String(y), label: String(y) }
        })

        return (
          <div className={clsx("flex flex-col gap-5", animationClass)}>
            <div className="space-y-2">
              <label className="text-sm font-bold text-slate-600">{t('enroll.given_name_label')}</label>
              <div className="relative">
                <MdPerson className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  className="native-input pl-12" 
                  value={givenName} 
                  onChange={e => setGivenName(e.target.value)} 
                  placeholder={t('enroll.given_name_placeholder')}
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-bold text-slate-600">{t('enroll.family_name_label')}</label>
              <div className="relative">
                <MdPerson className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  className="native-input pl-12" 
                  value={familyName} 
                  onChange={e => setFamilyName(e.target.value)} 
                  placeholder={t('enroll.family_name_placeholder')}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-bold text-slate-600">{t('enroll.birthdate_label')} ({t('common.optional')})</label>
              <div className="flex gap-2">
                <CustomDropdown 
                  value={birthDay} 
                  onChange={setBirthDay} 
                  options={days} 
                  placeholder="Day" 
                  icon={<MdCalendarToday className="text-sm" />} 
                />
                <CustomDropdown 
                  value={birthMonth} 
                  onChange={setBirthMonth} 
                  options={months} 
                  placeholder="Month" 
                />
                <CustomDropdown 
                  value={birthYear} 
                  onChange={setBirthYear} 
                  options={years} 
                  placeholder="Year" 
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-bold text-slate-600">{t('enroll.gender_label')} ({t('common.optional')})</label>
              <CustomDropdown 
                value={gender} 
                onChange={(v) => setGender(v as any)} 
                options={genderOptions} 
                placeholder="Select Gender" 
                icon={<MdWc />}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-bold text-slate-600">{t('enroll.address_label')}</label>
              <div className="relative">
                <MdHome className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  className="native-input pl-12" 
                  value={address} 
                  onChange={e => setAddress(e.target.value)} 
                  placeholder={t('enroll.address_placeholder')}
                />
              </div>
            </div>
          </div>
        )
      case 'identity':
        return (
          <div className={clsx("flex flex-col gap-6", animationClass)}>
            <div className="text-center space-y-2">
              <h2 className="text-lg font-bold text-brand-dark">{t('enroll.has_id_question')}</h2>
              <p className="text-sm text-slate-500 leading-relaxed">{t('enroll.has_id_description')}</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <button 
                type="button"
                onClick={() => setHasId(true)}
                className={clsx(
                  "p-6 rounded-3xl border-2 transition-all flex flex-col items-center gap-2",
                  hasId === true ? "border-brand-accent bg-brand-accent/5" : "border-slate-100 bg-white hover:border-slate-200"
                )}
              >
                <div className={clsx("w-10 h-10 rounded-full flex items-center justify-center text-xl", hasId === true ? "bg-brand-accent text-white" : "bg-slate-100 text-slate-400")}>
                  <MdCheckCircleOutline />
                </div>
                <span className="font-bold">{t('common.yes')}</span>
              </button>
              <button 
                type="button"
                onClick={() => { setHasId(false); setIdDocument('') }}
                className={clsx(
                  "p-6 rounded-3xl border-2 transition-all flex flex-col items-center gap-2",
                  hasId === false ? "border-slate-400 bg-slate-50" : "border-slate-100 bg-white hover:border-slate-200"
                )}
              >
                <div className={clsx("w-10 h-10 rounded-full flex items-center justify-center text-xl", hasId === false ? "bg-slate-400 text-white" : "bg-slate-100 text-slate-400")}>
                  <MdRemove />
                </div>
                <span className="font-bold">{t('common.no')}</span>
              </button>
            </div>
            {hasId && (
              <div className="space-y-2 animate-in zoom-in-95 duration-300">
                <label className="text-sm font-bold text-slate-600">{t('enroll.id_document_label')}</label>
                <div className="relative">
                  <MdFingerprint className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input className="native-input pl-12" value={idDocument} onChange={e => setIdDocument(e.target.value)} placeholder={t('enroll.id_document_placeholder')} />
                </div>
              </div>
            )}
          </div>
        )
      case 'phone':
        return (
          <div className={clsx("flex flex-col gap-5", animationClass)}>
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-slate-600">{t('enroll.phone_label')}</label>
              <button type="button" onClick={() => setPhones([...phones, ''])} disabled={phones.length >= 3} className="text-brand-accent text-sm font-bold flex items-center gap-1">
                <MdAdd className="text-lg" /> Add SIM
              </button>
            </div>
            {phones.map((phone, i) => (
              <div key={i} className="relative">
                {detectedCountries[i] ? (
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-xl z-10">{getEmojiFlag(detectedCountries[i]!.iso_code)}</div>
                ) : (
                  <MdPhone className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                )}
                <input 
                  className={clsx("native-input", detectedCountries[i] ? "pl-14" : "pl-12")} 
                  value={phone} 
                  onChange={e => {
                    const next = [...phones]
                    next[i] = e.target.value
                    setPhones(next)
                  }}
                  placeholder={i === 0 ? t('enroll.phone_primary_placeholder') : t('enroll.phone_secondary_placeholder')}
                />
                {i > 0 && (
                  <button type="button" onClick={() => setPhones(phones.filter((_, idx) => idx !== i))} className="absolute right-4 top-1/2 -translate-y-1/2 text-red-400"><MdRemove /></button>
                )}
              </div>
            ))}
          </div>
        )
      case 'consent':
        return (
          <div className={clsx("flex flex-col gap-6", animationClass)}>
            <div className="native-card p-6 bg-blue-50 border-blue-100 space-y-4">
              <h3 className="font-bold text-blue-900 flex items-center gap-2"><MdCheckCircleOutline /> {t('enroll.consent_title')}</h3>
              <p className="text-xs text-blue-800 leading-relaxed">{t('enroll.consent_text')}</p>
              <div className="flex items-center gap-3">
                <input type="checkbox" id="consent" className="w-6 h-6 rounded" checked={consent} onChange={e => { setConsent(e.target.checked); if (e.target.checked) setConsentError(false) }} />
                <label htmlFor="consent" className="text-sm font-bold text-blue-900">{t('enroll.consent_agree')}</label>
              </div>
            </div>
            <div className="native-card p-6 bg-slate-50 border-dashed border-2 border-slate-200">
              <h3 className="font-bold text-slate-700 flex items-center gap-2"><MdLocationOn /> {t('enroll.location_title')}</h3>
              <p className="text-xs text-slate-500 mb-3">{t('enroll.location_description')}</p>
              <button 
                type="button" 
                onClick={() => {
                  setIsLocating(true)
                  navigator.geolocation.getCurrentPosition(
                    p => { setLocation({ latitude: p.coords.latitude, longitude: p.coords.longitude, radius: p.coords.accuracy }); setIsLocating(false); toast.success(t('enroll.location_verified')) },
                    () => { setIsLocating(false); toast.error('Location denied') }
                  )
                }}
                className="text-xs font-bold text-brand-accent"
              >
                {isLocating ? t('enroll.location_accessing') : location ? `📍 ${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}` : t('enroll.location_share')}
              </button>
            </div>
            {consentError && <p className="text-xs text-red-500 font-medium mt-1">You must consent to continue</p>}
          </div>
        )
      case 'face':
        return (
          <div className={animationClass}>
            <FaceCapture onBiometricResult={handleBiometricResult} />
          </div>
        )
    }
  }

  return (
    <div className="max-w-lg mx-auto pb-12">
      <SEO title={t('navbar.enroll')} />
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-black text-brand-dark tracking-tight">{t('enroll.title')}</h1>
        <p className="text-slate-500">{t('enroll.subtitle')}</p>
      </header>

      <Stepper currentStep={stepIndex} totalSteps={steps.length} />

      <div className="bg-white rounded-[32px] p-6 shadow-xl shadow-slate-200/50 border border-slate-100 min-h-[400px] flex flex-col">
        <div className="flex-1">
          {renderStep()}
        </div>

        {steps[stepIndex] !== 'face' && (
          <div className="mt-8 flex gap-3">
            {stepIndex > 0 && (
              <button 
                onClick={prevStep}
                className="h-14 px-6 rounded-2xl bg-slate-100 text-slate-600 font-bold flex items-center gap-2 active:scale-95 transition-all"
              >
                <MdNavigateBefore className="text-xl" />
              </button>
            )}
            <button 
              onClick={nextStep}
              className="flex-1 h-14 rounded-2xl bg-brand-dark text-white font-bold flex items-center justify-center gap-2 active:scale-95 transition-all shadow-lg shadow-brand-dark/20"
            >
              {stepIndex === steps.length - 2 ? t('enroll.submit_button') : t('common.next')}
              <MdNavigateNext className="text-xl" />
            </button>
          </div>
        )}
      </div>

      {enroll.isPending && (
        <div className="fixed inset-0 z-50 bg-brand-dark/95 backdrop-blur-md flex flex-col items-center justify-center p-8 animate-in fade-in duration-500">
           <div className="relative w-48 h-48 flex items-center justify-center">
            <div className="absolute inset-0 border-2 border-brand-accent/20 rounded-full animate-[ping_3s_linear_infinite]" />
            <div className="absolute inset-0 border-[3px] border-transparent border-t-brand-accent rounded-full animate-spin" />
            <div className="text-brand-accent font-black text-2xl">VID</div>
          </div>
          <div className="mt-12 text-center space-y-4">
            <h2 className="text-white font-bold text-xl">{t('enroll.loader_title')}</h2>
            <p className="text-brand-accent/70 text-[10px] uppercase font-black tracking-widest">{t('enroll.loader_subtitle')}</p>
            <p className="text-slate-400 text-xs max-w-xs">{t('enroll.loader_description')}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default EnrollPage
