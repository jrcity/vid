import React from 'react'
import { useNavigate } from 'react-router-dom'
import { MdHome, MdExploreOff } from 'react-icons/md'
import useTranslation from '../hooks/useTranslation'
import SEO from '../components/SEO'

const NotFoundPage: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-6 animate-in fade-in zoom-in-95 duration-700">
      <SEO title="404 - Not Found" description="The page you are looking for does not exist." />
      
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-brand-light blur-3xl opacity-20 rounded-full scale-150 animate-pulse" />
        <MdExploreOff className="text-9xl text-slate-200 relative z-10" />
        <div className="absolute -top-4 -right-4 bg-red-500 text-white text-xs font-black px-3 py-1 rounded-full shadow-lg z-20">
          ERROR 404
        </div>
      </div>

      <h1 className="text-4xl font-black text-brand-dark mb-4 tracking-tight">
        {t('errors.not_found_title') || 'Lost in the Digital Wilds?'}
      </h1>
      
      <p className="text-slate-500 max-w-md mx-auto mb-10 leading-relaxed">
        {t('errors.not_found_subtitle') || 'We couldn\'t find the identity record or page you were looking for. It might have been moved or doesn\'t exist in the VID registry.'}
      </p>

      <div className="flex flex-col sm:flex-row gap-4 w-full max-w-sm">
        <button
          onClick={() => navigate('/')}
          className="native-button bg-brand-dark text-white flex-1 flex items-center justify-center gap-2 group"
        >
          <MdHome className="text-xl group-hover:-translate-y-0.5 transition-transform" />
          {t('errors.back_home') || 'Back to Dashboard'}
        </button>
        
        <button
          onClick={() => navigate(-1)}
          className="native-button bg-slate-100 text-slate-600 flex-1 border border-slate-200"
        >
          {t('errors.go_back') || 'Go Back'}
        </button>
      </div>

      <div className="mt-16 pt-8 border-t border-slate-100 w-full max-w-md">
        <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mb-4">
          Sovereign Identity Verification Protocol
        </p>
        <div className="flex justify-center gap-4 opacity-30 grayscale">
          <div className="w-8 h-8 rounded bg-slate-200" />
          <div className="w-8 h-8 rounded bg-slate-200" />
          <div className="w-8 h-8 rounded bg-slate-200" />
        </div>
      </div>
    </div>
  )
}

export default NotFoundPage
