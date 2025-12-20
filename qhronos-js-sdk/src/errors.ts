/**
 * Base error class for Qhronos SDK errors
 */
export class QhronosError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'QhronosError';
    Object.setPrototypeOf(this, QhronosError.prototype);
  }
}

/**
 * Error thrown when the API returns an error response
 */
export class QhronosApiError extends QhronosError {
  /** HTTP status code */
  public readonly status: number;
  /** Error code from the API */
  public readonly code?: string;
  /** Additional error details */
  public readonly details?: Record<string, unknown>;

  constructor(
    message: string,
    status: number,
    code?: string,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'QhronosApiError';
    this.status = status;
    this.code = code;
    this.details = details;
    Object.setPrototypeOf(this, QhronosApiError.prototype);
  }
}

/**
 * Error thrown when a network error occurs
 */
export class QhronosNetworkError extends QhronosError {
  /** Error type (e.g., 'TIMEOUT', 'NETWORK_ERROR') */
  public readonly type: string;

  constructor(message: string, type: string) {
    super(message);
    this.name = 'QhronosNetworkError';
    this.type = type;
    Object.setPrototypeOf(this, QhronosNetworkError.prototype);
  }
}

