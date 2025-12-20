import { BaseResource } from './base';
import type { RequestOptions } from '../client';
import type { Event, EventCreateParams, EventUpdateParams, EventListParams } from '../types/events';
import type { PaginatedResponse } from '../types/common';

/**
 * Events resource for managing scheduled events
 */
export class EventsResource extends BaseResource {
  /**
   * Create a new event
   * 
   * @example
   * ```typescript
   * const event = await client.events.create({
   *   name: 'Daily Reminder',
   *   start_time: new Date(Date.now() + 3600000).toISOString(),
   *   action: {
   *     type: 'webhook',
   *     params: { url: 'https://example.com/webhook' }
   *   },
   *   schedule: { frequency: 'daily' }
   * });
   * ```
   */
  async create(params: EventCreateParams, options?: RequestOptions): Promise<Event> {
    const body = {
      ...params,
      start_time: params.start_time instanceof Date 
        ? params.start_time.toISOString() 
        : params.start_time,
    };
    return this.post<Event>('/events', body, options);
  }

  /**
   * Get an event by ID
   */
  async get(id: string, options?: RequestOptions): Promise<Event> {
    return this.get<Event>(`/events/${id}`, options);
  }

  /**
   * Update an event
   */
  async update(id: string, params: EventUpdateParams, options?: RequestOptions): Promise<Event> {
    const body = {
      ...params,
      start_time: params.start_time instanceof Date 
        ? params.start_time.toISOString() 
        : params.start_time,
    };
    return this.put<Event>(`/events/${id}`, body, options);
  }

  /**
   * Delete an event
   */
  async delete(id: string, options?: RequestOptions): Promise<void> {
    return this.delete<void>(`/events/${id}`, options);
  }

  /**
   * List events with optional filtering
   * 
   * @example
   * ```typescript
   * const events = await client.events.list({
   *   tags: ['notifications'],
   *   status: 'active',
   *   limit: 20
   * });
   * ```
   */
  async list(params?: EventListParams, options?: RequestOptions): Promise<PaginatedResponse<Event>> {
    const query = this.buildQueryString(params ?? {});
    return this.get<PaginatedResponse<Event>>(`/events${query}`, options);
  }

  /**
   * Pause an event
   */
  async pause(id: string, options?: RequestOptions): Promise<Event> {
    return this.post<Event>(`/events/${id}/pause`, undefined, options);
  }

  /**
   * Resume a paused event
   */
  async resume(id: string, options?: RequestOptions): Promise<Event> {
    return this.post<Event>(`/events/${id}/resume`, undefined, options);
  }

  /**
   * Trigger an event immediately (for testing)
   */
  async trigger(id: string, options?: RequestOptions): Promise<{ job_id: string }> {
    return this.post<{ job_id: string }>(`/events/${id}/trigger`, undefined, options);
  }
}

