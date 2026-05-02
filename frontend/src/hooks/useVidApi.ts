import { useQuery, useMutation } from '@tanstack/react-query'
import axios, { AxiosError } from 'axios'
import { 
  Country, 
  ResolvePhoneResponse, 
  Certificate, 
  EnrollRequest, 
  VerifyResponse 
} from '../types/vid'

const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE,
})

// Request Interceptor
// TODO: REMOVE BEFORE PRODUCTION - Logs payloads for debugging in development
api.interceptors.request.use((config) => {
  if (import.meta.env.DEV) {
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, config.data || '')
  }
  return config
})

// Response Interceptor
api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.status} ${response.config.url}`, response.data)
    }
    return response
  },
  (error) => {
    if (import.meta.env.DEV) {
      console.error(`[API Error] ${error.response?.status} ${error.config?.url}`, error.response?.data || error.message)
    }
    return Promise.reject(error)
  }
)

export const useCountries = () => {
  return useQuery<Country[]>({
    queryKey: ['countries'],
    queryFn: async () => {
      const { data } = await api.get('/countries')
      return data.countries
    },
  })
}

export const useResolvePhone = () => {
  return useMutation<ResolvePhoneResponse, AxiosError, string>({
    mutationFn: async (phone: string) => {
      const { data } = await api.post('/resolve-phone', { phone })
      return data
    },
  })
}

export const useEnroll = () => {
  return useMutation<Certificate, AxiosError, EnrollRequest>({
    mutationFn: async (enrollData: EnrollRequest) => {
      const { data } = await api.post('/enroll', enrollData)
      return data.certificate
    },
  })
}

export const useVerify = (vidId?: string) => {
  return useQuery<VerifyResponse>({
    queryKey: ['verify', vidId],
    queryFn: async () => {
      const { data } = await api.get(`/verify/${vidId}`)
      return data
    },
    enabled: !!vidId,
  })
}
