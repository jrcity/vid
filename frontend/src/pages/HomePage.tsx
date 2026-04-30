import { Link } from 'react-router-dom'
import { MdOutlineSecurity, MdOutlineQrCodeScanner, MdOutlineNetworkCheck } from 'react-icons/md'
import SEO from '../components/SEO'

const Home = () => {
  return (
    <div className="flex flex-col gap-8 py-4">
      <SEO title="Home" />
      <section className="text-center space-y-4">
        <h1 className="text-4xl font-extrabold text-brand-dark leading-tight">
          Your Pan-African <br />
          <span className="text-brand-accent">Network Identity</span>
        </h1>
        <p className="text-slate-500 text-lg">
          Connect your SIM cards to generate a secure, private, and verifiable digital ID in minutes.
        </p>
      </section>

      <section className="grid gap-4">
        <div className="native-card p-6 flex gap-4 items-start">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0 text-2xl">
            <MdOutlineSecurity />
          </div>
          <div>
            <h3 className="font-bold text-brand-dark">Privacy by Design</h3>
            <p className="text-sm text-slate-500">Your personal data stays on the network. We only use boolean trust signals.</p>
          </div>
        </div>

        <div className="native-card p-6 flex gap-4 items-start">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0 text-2xl">
            <MdOutlineNetworkCheck />
          </div>
          <div>
            <h3 className="font-bold text-brand-dark">Multi-SIM Corroboration</h3>
            <p className="text-sm text-slate-500">Increase your trust score by linking up to 3 SIM cards from any African network.</p>
          </div>
        </div>

        <div className="native-card p-6 flex gap-4 items-start">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0 text-2xl">
            <MdOutlineQrCodeScanner />
          </div>
          <div>
            <h3 className="font-bold text-brand-dark">Universal Verification</h3>
            <p className="text-sm text-slate-500">Banks, clinics, and NGOs can verify your VID instantly via QR code.</p>
          </div>
        </div>
      </section>

      <section className="mt-4">
        <Link to="/enroll" className="native-button bg-brand-dark text-white w-full text-lg shadow-lg">
          Get Started
        </Link>
      </section>
    </div>
  )
}

export default Home
