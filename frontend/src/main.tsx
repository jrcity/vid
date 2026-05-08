import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider, Route, createRoutesFromElements } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { HelmetProvider } from 'react-helmet-async'
import { LanguageProvider } from './context/LanguageContext'
import TranslationErrorBoundary from './components/TranslationErrorBoundary'
import App from './App'
import HomePage from './pages/HomePage'
import EnrollPage from './pages/EnrollPage'
import CertificateViewPage from './pages/CertificateViewPage'
import VerifyPage from './pages/VerifyPage'
import NotFoundPage from './pages/NotFoundPage'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route path="/" element={<App />} errorElement={<NotFoundPage />}>
      <Route index element={<HomePage />} />
      <Route path="enroll" element={<EnrollPage />} />
      <Route path="certificate" element={<CertificateViewPage />} />
      <Route path="verify/:vidId" element={<VerifyPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Route>,
  ),
)

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <HelmetProvider>
        <LanguageProvider>
          <TranslationErrorBoundary>
            <RouterProvider
              router={router}
              future={{
                v7_startTransition: true,
              }}
            />
            <Toaster
              position="bottom-center"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#0F172A',
                  color: '#fff',
                  borderRadius: '16px',
                  fontSize: '14px',
                },
              }}
            />
          </TranslationErrorBoundary>
        </LanguageProvider>
      </HelmetProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
