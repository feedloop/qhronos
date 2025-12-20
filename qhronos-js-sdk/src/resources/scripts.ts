import { BaseResource } from './base';
import type { RequestOptions } from '../client';
import type { Script, ScriptCreateParams, ScriptUpdateParams, ScriptExecuteParams } from '../types/scripts';
import type { Job } from '../types/jobs';
import type { PaginatedResponse, ListParams } from '../types/common';

/**
 * Scripts resource for managing JavaScript scripts
 */
export class ScriptsResource extends BaseResource {
  /**
   * Create a new script
   * 
   * @example
   * ```typescript
   * const script = await client.scripts.create({
   *   name: 'Data Transformer',
   *   code: `
   *     const data = input.data;
   *     const transformed = data.map(item => ({
   *       ...item,
   *       processed: true
   *     }));
   *     return { transformed };
   *   `
   * });
   * ```
   */
  async create(params: ScriptCreateParams, options?: RequestOptions): Promise<Script> {
    return this.post<Script>('/scripts', params, options);
  }

  /**
   * Get a script by ID
   */
  async get(id: string, options?: RequestOptions): Promise<Script> {
    return this.get<Script>(`/scripts/${id}`, options);
  }

  /**
   * Update a script
   */
  async update(id: string, params: ScriptUpdateParams, options?: RequestOptions): Promise<Script> {
    return this.put<Script>(`/scripts/${id}`, params, options);
  }

  /**
   * Delete a script
   */
  async delete(id: string, options?: RequestOptions): Promise<void> {
    return this.delete<void>(`/scripts/${id}`, options);
  }

  /**
   * List scripts with optional pagination
   */
  async list(params?: ListParams, options?: RequestOptions): Promise<PaginatedResponse<Script>> {
    const query = this.buildQueryString(params ?? {});
    return this.get<PaginatedResponse<Script>>(`/scripts${query}`, options);
  }

  /**
   * Execute a script immediately
   * 
   * @example
   * ```typescript
   * const job = await client.scripts.execute('script-id', {
   *   params: { data: [1, 2, 3] }
   * });
   * ```
   */
  async execute(id: string, params?: ScriptExecuteParams, options?: RequestOptions): Promise<Job> {
    return this.post<Job>(`/scripts/${id}/execute`, params ?? {}, options);
  }
}

