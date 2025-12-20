import { BaseResource } from './base';
import type { RequestOptions } from '../client';
import type { Workflow, WorkflowCreateParams, WorkflowUpdateParams, WorkflowExecuteParams } from '../types/workflows';
import type { Job, JobListParams } from '../types/jobs';
import type { PaginatedResponse, ListParams } from '../types/common';

/**
 * Workflows resource for managing workflow definitions
 */
export class WorkflowsResource extends BaseResource {
  /**
   * Create a new workflow
   * 
   * @example
   * ```typescript
   * const workflow = await client.workflows.create({
   *   name: 'Data Pipeline',
   *   definition: {
   *     steps: [
   *       {
   *         id: 'fetch',
   *         type: 'action',
   *         action: { type: 'apicall', params: { url: '...' } },
   *         next: 'process'
   *       },
   *       {
   *         id: 'process',
   *         type: 'action',
   *         action: { type: 'script', params: { script_id: '...' } }
   *       }
   *     ]
   *   }
   * });
   * ```
   */
  async create(params: WorkflowCreateParams, options?: RequestOptions): Promise<Workflow> {
    return this.post<Workflow>('/workflows', params, options);
  }

  /**
   * Get a workflow by ID
   */
  async get(id: string, options?: RequestOptions): Promise<Workflow> {
    return this.get<Workflow>(`/workflows/${id}`, options);
  }

  /**
   * Update a workflow
   */
  async update(id: string, params: WorkflowUpdateParams, options?: RequestOptions): Promise<Workflow> {
    return this.put<Workflow>(`/workflows/${id}`, params, options);
  }

  /**
   * Delete a workflow
   */
  async delete(id: string, options?: RequestOptions): Promise<void> {
    return this.delete<void>(`/workflows/${id}`, options);
  }

  /**
   * List workflows with optional pagination
   */
  async list(params?: ListParams, options?: RequestOptions): Promise<PaginatedResponse<Workflow>> {
    const query = this.buildQueryString(params ?? {});
    return this.get<PaginatedResponse<Workflow>>(`/workflows${query}`, options);
  }

  /**
   * Execute a workflow immediately
   * 
   * @example
   * ```typescript
   * const job = await client.workflows.execute('workflow-id', {
   *   params: { userId: '123', action: 'process' }
   * });
   * ```
   */
  async execute(id: string, params?: WorkflowExecuteParams, options?: RequestOptions): Promise<Job> {
    return this.post<Job>(`/workflows/${id}/execute`, params ?? {}, options);
  }

  /**
   * List jobs for a workflow
   */
  async jobs(id: string, params?: JobListParams, options?: RequestOptions): Promise<PaginatedResponse<Job>> {
    const query = this.buildQueryString(params ?? {});
    return this.get<PaginatedResponse<Job>>(`/workflows/${id}/jobs${query}`, options);
  }

  /**
   * Get a specific job for a workflow
   */
  async job(workflowId: string, jobId: string, options?: RequestOptions): Promise<Job> {
    return this.get<Job>(`/workflows/${workflowId}/jobs/${jobId}`, options);
  }
}

