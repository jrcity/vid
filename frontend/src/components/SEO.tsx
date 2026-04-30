import { Helmet } from 'react-helmet-async'

interface SEOProps {
  title: string
  description?: string
}

const SEO = ({ title, description }: SEOProps) => {
  const fullTitle = `${title} | VID — Virtual ID`
  const defaultDesc = "Secure, private, and verifiable digital identity for everyone in Africa using mobile network signals."

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={description || defaultDesc} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description || defaultDesc} />
      <meta property="og:type" content="website" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description || defaultDesc} />
    </Helmet>
  )
}

export default SEO
