import { useState, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'

interface SEOProps {
  title: string
  description?: string
}

const SEO = ({ title, description }: SEOProps) => {
  const fullTitle = `${title} | VID — Virtual ID`
  const defaultDesc = "Secure, private, and verifiable digital identity for everyone in Africa using mobile network signals."
  
  const [canonicalUrl, setCanonicalUrl] = useState('https://vid.network')

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setCanonicalUrl(window.location.href)
    }
  }, [])

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={description || defaultDesc} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description || defaultDesc} />
      <meta property="og:type" content="website" />
      <meta property="og:site_name" content="VID Network" />
      <meta property="og:locale" content="en_US" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description || defaultDesc} />
      <meta name="twitter:image" content="https://vid.network/og-image.png" />
      <meta property="og:image" content="https://vid.network/og-image.png" />
      <link rel="canonical" href={canonicalUrl} />
    </Helmet>
  )
}

export default SEO
