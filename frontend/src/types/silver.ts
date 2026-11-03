export type SessionType = 'AM' | 'PM';
export type MetalType = 'silver';
export type PurityType = '999';
export type RateStatus = 'valid' | 'quarantined' | 'superseded';
export type RateUnit = 'per_kg' | 'per_10g' | 'per_gram';

export type StaleReason =
  | 'source_unavailable'
  | 'parser_unhealthy'
  | 'not_yet_published'
  | null;

export interface SilverRate {
  metal: MetalType;
  purity: PurityType;
  rate_date: string; // 'YYYY-MM-DD' in Asia/Kolkata
  session: SessionType;
  price_inr_per_kg: number;
  price_inr_per_10g: number;
  price_inr_per_gram: number;
  excludes_gst: boolean;
  derived: boolean;
  detected_at: string; // ISO-8601 UTC
  revision: number;
  stale: boolean;
  stale_reason: StaleReason;
  next_expected_publication?: string | null;
  source: string;
  attribution: string;
  status?: RateStatus;
}

export interface HistoricalRateRecord {
  id?: number;
  rate_date: string;
  session: SessionType;
  metal: MetalType;
  purity: PurityType;
  price_inr: number;
  price_inr_per_kg?: number;
  price_inr_per_10g?: number;
  price_inr_per_gram?: number;
  unit: string;
  status: RateStatus;
  revision: number;
  first_seen_at?: string;
  detected_at?: string;
  source_url?: string;
}

export interface HistoryQueryParams {
  from?: string;
  to?: string;
  session?: SessionType;
  format?: 'json' | 'csv';
  limit?: number;
  offset?: number;
}

export interface HistoryResponse {
  items: HistoricalRateRecord[];
  total: number;
  limit: number;
  offset: number;
}

export type SSERateEventName = 'rate.published' | 'rate.revised' | 'ping';

export interface SSERateEvent {
  event: SSERateEventName;
  data: SilverRate;
}

export type SSEConnectionState = 'connecting' | 'connected' | 'disconnected';
