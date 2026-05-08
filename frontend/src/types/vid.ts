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
  // FE-01: frontend-only field for biometric signal display
  biometric_passed?: boolean;
}

/** Face recognition status types — no biometric data leaves the device */
export type FaceStatus =
  | 'loading'
  | 'starting'
  | 'searching'
  | 'face_detected'
  | 'blink_prompt'
  | 'blink_detected'
  | 'failed'
  | 'error';

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
  given_name: string;
  family_name: string;
  phone_numbers: { number: string; is_primary?: boolean }[];
  consent: boolean;
  location?: {
    latitude: number;
    longitude: number;
    radius?: number;
  };
  // Optional KYC fields — aligned with NaC sandbox
  birthdate?: string;
  email?: string;
  gender?: 'MALE' | 'FEMALE' | 'OTHER';
  id_document?: string;
  address: string;
  // FE-01: sent to backend — no biometric data leaves this device
  biometric_passed?: boolean;
  locale: string;
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
  explanation?: string;
}
