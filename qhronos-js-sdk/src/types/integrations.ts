/**
 * Integration type
 */
export type IntegrationType = 'llm' | 'notification' | 'database' | 'spreadsheet';

/**
 * Integration provider
 */
export type IntegrationProvider =
  // LLM providers
  | 'openai'
  | 'anthropic'
  | 'gemini'
  | 'openrouter'
  // Notification providers
  | 'ses'
  | 'twilio'
  | 'slack'
  | 'discord'
  | 'telegram'
  // Database providers
  | 'mysql'
  | 'postgres'
  // Spreadsheet providers
  | 'google_sheets';

/**
 * Integration status
 */
export type IntegrationStatus = 'active' | 'inactive';

/**
 * Integration model
 */
export interface Integration {
  id: string;
  name: string;
  type: IntegrationType;
  provider: IntegrationProvider;
  config: Record<string, unknown>;
  status: IntegrationStatus;
  tags?: string[];
  created_at: string;
  updated_at?: string;
}

/**
 * Parameters for creating an integration
 */
export interface IntegrationCreateParams {
  name: string;
  type: IntegrationType;
  provider: IntegrationProvider;
  config: Record<string, unknown>;
  tags?: string[];
}

/**
 * Parameters for updating an integration
 */
export interface IntegrationUpdateParams {
  name?: string;
  config?: Record<string, unknown>;
  status?: IntegrationStatus;
  tags?: string[];
}

