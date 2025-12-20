/**
 * Script status
 */
export type ScriptStatus = 'active' | 'inactive';

/**
 * Script model
 */
export interface Script {
  id: string;
  name: string;
  description?: string;
  code: string;
  version: number;
  language: 'javascript';
  status: ScriptStatus;
  tags?: string[];
  created_at: string;
  updated_at?: string;
}

/**
 * Parameters for creating a script
 */
export interface ScriptCreateParams {
  name: string;
  description?: string;
  code: string;
  tags?: string[];
}

/**
 * Parameters for updating a script
 */
export interface ScriptUpdateParams {
  name?: string;
  description?: string;
  code?: string;
  status?: ScriptStatus;
  tags?: string[];
}

/**
 * Parameters for executing a script
 */
export interface ScriptExecuteParams {
  params?: Record<string, unknown>;
}

