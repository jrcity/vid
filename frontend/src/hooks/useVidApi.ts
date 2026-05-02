import { useQuery, useMutation } from '@tanstack/react-query'
import axios from 'axios'
import { 
  Country, 
  ResolvePhoneResponse, 
  Certificate, 
  EnrollRequest, 
  VerifyResponse 
} from '../types/vid'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
})

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
  return useMutation<ResolvePhoneResponse, Error, string>({
    mutationFn: async (phone: string) => {
      const { data } = await api.post('/resolve-phone', { phone })
      return data
    },
  })
}

export const useEnroll = () => {
  return useMutation<Certificate, Error, EnrollRequest>({
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
