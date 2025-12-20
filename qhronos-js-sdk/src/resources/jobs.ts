import { BaseResource } from './base';
import type { RequestOptions } from '../client';
import type { Job, JobListParams } from '../types/jobs';
import type { PaginatedResponse } from '../types/common';

/**
 * Jobs resource for querying execution records
 */
export class JobsResource extends BaseResource {
  /**
   * Get a job by ID
   */
  async get(id: string, options?: RequestOptions): Promise<Job> {
    return this.get<Job>(`/jobs/${id}`, options);
  }

  /**
   * List jobs with optional filtering
   * 
   * @example
   * ```typescript
   * const jobs = await client.jobs.list({
   *   status: 'completed',
   *   type: 'workflow',
   *   limit: 50
   * });
   * ```
   */
  async list(params?: JobListParams, options?: RequestOptions): Promise<PaginatedResponse<Job>> {
    const query = this.buildQueryString(params ?? {});
    return this.get<PaginatedResponse<Job>>(`/jobs${query}`, options);
  }

  /**
   * Cancel a pending or running job
   */
  async cancel(id: string, options?: RequestOptions): Promise<Job> {
    return this.post<Job>(`/jobs/${id}/cancel`, undefined, options);
  }

  /**
   * Retry a failed job
   */
  async retry(id: string, options?: RequestOptions): Promise<Job> {
    return this.post<Job>(`/jobs/${id}/retry`, undefined, options);
  }

  /**
   * Get child jobs (for workflow jobs)
   */
  async children(id: string, params?: Omit<JobListParams, 'parent_job_id'>, options?: RequestOptions): Promise<PaginatedResponse<Job>> {
    const query = this.buildQueryString(params ?? {});
    return this.get<PaginatedResponse<Job>>(`/jobs/${id}/children${query}`, options);
  }
}

