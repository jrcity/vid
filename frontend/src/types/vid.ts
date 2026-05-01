export interface SignalResult {
  api_name: string;
  signal_key: string;
  passed: boolean;
  weight: number;
  display_value: string;
  detail: string;
}

export interface TrustScore {
  score: number;
  grade: string;
  signals: SignalResult[];
  explanation: string;
  multi_sim_bonus: number;
}

export interface Country {
  iso: string;
  name: string;
  vid_label: string;
  region: string;
  prefix: string;
}

export interface Certificate {
  vid_id: string;
  certificate_hash: string;
  holder_name: string;
  country: Country; // Nested country object to match backend
  masked_phones: string[];
  trust_score: TrustScore;
  issued_at: string;
  expires_at: string;
  qr_data_url: string;
}

export interface ResolvePhoneResponse {
  phone: string;
  iso_code: string;
  country_name: string;
  vid_label: string;
  region: string;
  prefix: string;
  valid: boolean;
  error?: string;
}

export interface EnrollRequest {
  full_name: string;
  phone_numbers: { number: string; is_primary?: boolean }[];
  consent: boolean;
  location?: {
    latitude: number;
    longitude: number;
    radius?: number;
  };
}

export interface VerifyResponse {
  valid: boolean;
  vid_id: string;
  nationality: string;
  vid_label: string;
  region: string;
  trust_grade: string;
  score: number;
  issued_at: string;
  expires_at: string;
}
