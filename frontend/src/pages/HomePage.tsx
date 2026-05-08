import { Link } from 'react-router-dom'
import { MdOutlineSecurity, MdOutlineQrCodeScanner, MdOutlineNetworkCheck } from 'react-icons/md'
import SEO from '../components/SEO'
import useTranslation from '../hooks/useTranslation'

const Home = () => {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-8 py-4">
      <SEO title={t('navbar.home')} />
      <section className="text-center space-y-4">
        <h1 className="text-4xl font-extrabold text-brand-dark leading-tight">
          {t('home.hero_title_1')} <br />
          <span className="text-brand-accent">{t('home.hero_title_2')}</span>
        </h1>
        <p className="text-slate-500 text-lg">
          {t('home.hero_subtitle')}
        </p>
      </section>

      <section className="grid gap-4">
        <div className="native-card p-6 flex gap-4 items-start">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0 text-2xl">
            <MdOutlineSecurity />
          </div>
          <div>
            <h3 className="font-bold text-brand-dark">{t('home.feature_1_title')}</h3>
            <p className="text-sm text-slate-500">{t('home.feature_1_desc')}</p>
          </div>
        </div>

        <div className="native-card p-6 flex gap-4 items-start">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0 text-2xl">
            <MdOutlineNetworkCheck />
          </div>
          <div>
            <h3 className="font-bold text-brand-dark">{t('home.feature_2_title')}</h3>
            <p className="text-sm text-slate-500">{t('home.feature_2_desc')}</p>
          </div>
        </div>

        <div className="native-card p-6 flex gap-4 items-start">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0 text-2xl">
            <MdOutlineQrCodeScanner />
          </div>
          <div>
            <h3 className="font-bold text-brand-dark">{t('home.feature_3_title')}</h3>
            <p className="text-sm text-slate-500">{t('home.feature_3_desc')}</p>
          </div>
        </div>
      </section>

      <section className="mt-4">
        <Link to="/enroll" className="native-button bg-brand-dark text-white w-full text-lg shadow-lg">
          {t('common.get_started')}
        </Link>
      </section>
    </div>
  )
}

export default Home
