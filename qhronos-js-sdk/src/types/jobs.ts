/**
 * Job status
 */
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

/**
 * Job type
 */
export type JobType = 'job' | 'workflow' | 'step' | 'api_call' | 'script' | 'webhook' | 'websocket' | 'integration';

/**
 * Job model
 */
export interface Job {
  id: string;
  schedule_id?: string;
  type: JobType;
  status: JobStatus;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  error_message?: string;
  parent_job_id?: string;
  data: Record<string, unknown>;
  created_at: string;
}

/**
 * Parameters for listing jobs
 */
export interface JobListParams {
  page?: number;
  limit?: number;
  type?: JobType;
  status?: JobStatus;
  event_id?: string;
  workflow_id?: string;
  parent_job_id?: string;
}

