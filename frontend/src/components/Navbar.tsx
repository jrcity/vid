import { Link } from 'react-router-dom'
import { MdVerifiedUser } from 'react-icons/md'
import LanguageSwitcher from './LanguageSwitcher'
import useTranslation from '../hooks/useTranslation'

const Navbar = () => {
  const { t } = useTranslation()

  return (
    <>
      <header className="h-16 bg-white border-b border-slate-100 px-4 flex items-center sticky top-0 z-50">
        <div className="max-w-lg mx-auto w-full flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-dark rounded-lg flex items-center justify-center text-white">
              <MdVerifiedUser className="text-xl" />
            </div>
            <span className="font-bold text-xl tracking-tight text-brand-dark">VID</span>
          </Link>
          <nav className="flex items-center gap-4">
            <Link to="/enroll" className="text-sm font-semibold text-brand-accent">{t('navbar.enroll')}</Link>
            <LanguageSwitcher />
          </nav>
        </div>
      </header>
    </>
  )
}

export default Navbar
