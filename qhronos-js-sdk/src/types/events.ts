/**
 * Action type for events
 */
export type ActionType = 'webhook' | 'websocket' | 'apicall' | 'script' | 'integration' | 'workflow';

/**
 * Action configuration
 */
export interface Action {
  type: ActionType;
  params: Record<string, unknown>;
}

/**
 * Schedule configuration for recurring events
 */
export interface ScheduleConfig {
  frequency: 'daily' | 'weekly' | 'monthly' | 'yearly';
  interval?: number;
  by_day?: string[];
  by_month?: number[];
  by_month_day?: number[];
  count?: number;
  until?: string;
}

/**
 * Event status
 */
export type EventStatus = 'active' | 'inactive' | 'paused';

/**
 * Event model
 */
export interface Event {
  id: string;
  name: string;
  description?: string;
  start_time: string;
  webhook?: string;
  action?: Action;
  metadata?: Record<string, unknown>;
  schedule?: ScheduleConfig;
  tags?: string[];
  status: EventStatus;
  hmac_secret?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Parameters for creating an event
 */
export interface EventCreateParams {
  name: string;
  description?: string;
  start_time: string | Date;
  webhook?: string;
  action?: Action;
  metadata?: Record<string, unknown>;
  schedule?: ScheduleConfig;
  tags?: string[];
  hmac_secret?: string;
}

/**
 * Parameters for updating an event
 */
export interface EventUpdateParams {
  name?: string;
  description?: string;
  start_time?: string | Date;
  webhook?: string;
  action?: Action;
  metadata?: Record<string, unknown>;
  schedule?: ScheduleConfig;
  tags?: string[];
  status?: EventStatus;
  hmac_secret?: string;
}

/**
 * Parameters for listing events
 */
export interface EventListParams {
  page?: number;
  limit?: number;
  tags?: string[];
  status?: EventStatus;
}

