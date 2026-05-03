import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider, Route, createRoutesFromElements } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { HelmetProvider } from 'react-helmet-async'
import App from './App'
import HomePage from './pages/HomePage'
import EnrollPage from './pages/EnrollPage'
import CertificateViewPage from './pages/CertificateViewPage'
import VerifyPage from './pages/VerifyPage'
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
    <Route path="/" element={<App />}>
      <Route index element={<HomePage />} />
      <Route path="enroll" element={<EnrollPage />} />
      <Route path="certificate" element={<CertificateViewPage />} />
      <Route path="verify/:vidId" element={<VerifyPage />} />
    </Route>,
  ),
)

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <HelmetProvider>
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
      </HelmetProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
