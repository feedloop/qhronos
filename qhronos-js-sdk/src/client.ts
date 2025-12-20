import { EventsResource } from './resources/events';
import { JobsResource } from './resources/jobs';
import { WorkflowsResource } from './resources/workflows';
import { ScriptsResource } from './resources/scripts';
import { IntegrationsResource } from './resources/integrations';
import { QhronosApiError, QhronosNetworkError } from './errors';
import type { ApiResponse } from './types/common';

/**
 * Configuration options for the Qhronos client
 */
export interface QhronosConfig {
  /** Base URL of the Qhronos API (e.g., 'https://api.qhronos.io') */
  baseUrl: string;
  /** API token for authentication (master token or JWT) */
  token: string;
  /** Request timeout in milliseconds (default: 30000) */
  timeout?: number;
  /** Custom headers to include with every request */
  headers?: Record<string, string>;
  /** Enable debug logging */
  debug?: boolean;
}

/**
 * Options for individual API requests
 */
export interface RequestOptions {
  /** Request timeout in milliseconds (overrides client default) */
  timeout?: number;
  /** Additional headers for this request */
  headers?: Record<string, string>;
  /** Idempotency key for safe retries */
  idempotencyKey?: string;
  /** Abort signal for request cancellation */
  signal?: AbortSignal;
}

/**
 * Qhronos API Client
 * 
 * @example
 * ```typescript
 * const client = new QhronosClient({
 *   baseUrl: 'https://api.qhronos.io',
 *   token: 'your-api-token',
 * });
 * 
 * // Create an event
 * const event = await client.events.create({
 *   name: 'Daily Report',
 *   start_time: new Date().toISOString(),
 *   action: {
 *     type: 'webhook',
 *     params: { url: 'https://example.com/webhook' }
 *   }
 * });
 * 
 * // List jobs
 * const jobs = await client.jobs.list({ limit: 10 });
 * ```
 */
export class QhronosClient {
  private readonly config: Required<Omit<QhronosConfig, 'headers'>> & Pick<QhronosConfig, 'headers'>;

  /** Events resource for managing scheduled events */
  public readonly events: EventsResource;
  /** Jobs resource for querying execution records */
  public readonly jobs: JobsResource;
  /** Workflows resource for managing workflow definitions */
  public readonly workflows: WorkflowsResource;
  /** Scripts resource for managing JavaScript scripts */
  public readonly scripts: ScriptsResource;
  /** Integrations resource for managing external service integrations */
  public readonly integrations: IntegrationsResource;

  constructor(config: QhronosConfig) {
    this.config = {
      baseUrl: config.baseUrl.replace(/\/$/, ''), // Remove trailing slash
      token: config.token,
      timeout: config.timeout ?? 30000,
      headers: config.headers,
      debug: config.debug ?? false,
    };

    // Initialize resources
    this.events = new EventsResource(this);
    this.jobs = new JobsResource(this);
    this.workflows = new WorkflowsResource(this);
    this.scripts = new ScriptsResource(this);
    this.integrations = new IntegrationsResource(this);
  }

  /**
   * Make an HTTP request to the Qhronos API
   * @internal
   */
  async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    path: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const url = `${this.config.baseUrl}${path}`;
    const timeout = options?.timeout ?? this.config.timeout;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.config.token}`,
      ...this.config.headers,
      ...options?.headers,
    };

    if (options?.idempotencyKey) {
      headers['Idempotency-Key'] = options.idempotencyKey;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      if (this.config.debug) {
        console.log(`[Qhronos] ${method} ${url}`, body ? JSON.stringify(body) : '');
      }

      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: options?.signal ?? controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await response.json() as ApiResponse<T>;

      if (!response.ok) {
        throw new QhronosApiError(
          data.error?.message ?? 'Unknown API error',
          response.status,
          data.error?.code,
          data.error?.details
        );
      }

      if (this.config.debug) {
        console.log(`[Qhronos] Response:`, JSON.stringify(data));
      }

      return data as T;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof QhronosApiError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new QhronosNetworkError('Request timed out', 'TIMEOUT');
        }
        throw new QhronosNetworkError(error.message, 'NETWORK_ERROR');
      }

      throw new QhronosNetworkError('Unknown error occurred', 'UNKNOWN');
    }
  }

  /**
   * Check the health of the Qhronos API
   */
  async health(): Promise<{ status: string }> {
    return this.request('GET', '/health');
  }

  /**
   * Get the status of the Qhronos API
   */
  async status(): Promise<Record<string, unknown>> {
    return this.request('GET', '/status');
  }
}

