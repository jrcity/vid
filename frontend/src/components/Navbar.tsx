import { Link } from 'react-router-dom'
import { MdVerifiedUser } from 'react-icons/md'

const Navbar = () => {
  return (
    <header className="h-16 bg-white border-b border-slate-100 px-4 flex items-center sticky top-0 z-50">
      <div className="max-w-lg mx-auto w-full flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-dark rounded-lg flex items-center justify-center text-white">
            <MdVerifiedUser className="text-xl" />
          </div>
          <span className="font-bold text-xl tracking-tight text-brand-dark">VID</span>
        </Link>
        <nav>
          <Link to="/enroll" className="text-sm font-semibold text-brand-accent">Enroll</Link>
        </nav>
      </div>
    </header>
  )
}

export default Navbar
