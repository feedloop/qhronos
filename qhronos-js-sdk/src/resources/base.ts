import type { QhronosClient, RequestOptions } from '../client';

/**
 * Base class for API resources
 */
export abstract class BaseResource {
  protected readonly client: QhronosClient;

  constructor(client: QhronosClient) {
    this.client = client;
  }

  protected get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.client.request('GET', path, undefined, options);
  }

  protected post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.client.request('POST', path, body, options);
  }

  protected put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.client.request('PUT', path, body, options);
  }

  protected delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.client.request('DELETE', path, undefined, options);
  }

  /**
   * Build query string from parameters
   */
  protected buildQueryString(params: Record<string, unknown>): string {
    const searchParams = new URLSearchParams();

    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, String(v)));
        } else {
          searchParams.append(key, String(value));
        }
      }
    }

    const query = searchParams.toString();
    return query ? `?${query}` : '';
  }
}

