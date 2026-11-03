export type HealthStatusType = 'healthy' | 'degraded' | 'unhealthy';

export type SchedulerMode = 'HOT' | 'CATCH_UP' | 'IDLE' | 'OFF_DAY';

export interface HealthStatus {
  status: HealthStatusType;
  scheduler_mode: SchedulerMode;
  last_successful_scrape: string | null;
  parser_healthy: boolean;
  quarantined_records_count: number;
  current_time_ist: string;
}
