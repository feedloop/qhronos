import { BaseResource } from './base';
import type { RequestOptions } from '../client';
import type { Integration, IntegrationCreateParams, IntegrationUpdateParams } from '../types/integrations';
import type { PaginatedResponse, ListParams } from '../types/common';

/**
 * Integrations resource for managing external service integrations
 */
export class IntegrationsResource extends BaseResource {
  /**
   * Create a new integration
   * 
   * @example
   * ```typescript
   * // Create an OpenAI LLM integration
   * const integration = await client.integrations.create({
   *   name: 'OpenAI GPT-4',
   *   type: 'llm',
   *   provider: 'openai',
   *   config: {
   *     api_key: process.env.OPENAI_API_KEY,
   *     model: 'gpt-4'
   *   }
   * });
   * 
   * // Create a Slack notification integration
   * const slack = await client.integrations.create({
   *   name: 'Slack Alerts',
   *   type: 'notification',
   *   provider: 'slack',
   *   config: {
   *     webhook_url: 'https://hooks.slack.com/...',
   *     channel: '#alerts'
   *   }
   * });
   * ```
   */
  async create(params: IntegrationCreateParams, options?: RequestOptions): Promise<Integration> {
    return this.post<Integration>('/integrations', params, options);
  }

  /**
   * Get an integration by ID
   */
  async get(id: string, options?: RequestOptions): Promise<Integration> {
    return this.get<Integration>(`/integrations/${id}`, options);
  }

  /**
   * Update an integration
   */
  async update(id: string, params: IntegrationUpdateParams, options?: RequestOptions): Promise<Integration> {
    return this.put<Integration>(`/integrations/${id}`, params, options);
  }

  /**
   * Delete an integration
   */
  async delete(id: string, options?: RequestOptions): Promise<void> {
    return this.delete<void>(`/integrations/${id}`, options);
  }

  /**
   * List integrations with optional pagination
   */
  async list(params?: ListParams, options?: RequestOptions): Promise<PaginatedResponse<Integration>> {
    const query = this.buildQueryString(params ?? {});
    return this.get<PaginatedResponse<Integration>>(`/integrations${query}`, options);
  }

  /**
   * Test an integration connection
   */
  async test(id: string, options?: RequestOptions): Promise<{ success: boolean; message?: string }> {
    return this.post<{ success: boolean; message?: string }>(`/integrations/${id}/test`, undefined, options);
  }
}

