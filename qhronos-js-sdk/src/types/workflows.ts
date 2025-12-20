import type { Action } from './events';

/**
 * Workflow step type
 */
export type StepType = 'action' | 'condition' | 'delay' | 'loop' | 'sub_workflow' | 'set_variable';

/**
 * Workflow step configuration
 */
export interface WorkflowStep {
  id: string;
  type: StepType;
  name?: string;
  action?: Action;
  condition?: string;
  true_branch?: string;
  false_branch?: string;
  delay_seconds?: number;
  items?: string;
  max_iterations?: number;
  variable?: string;
  value?: unknown;
  workflow_id?: string;
  steps?: WorkflowStep[];
  next?: string;
  on_error?: string;
  timeout_ms?: number;
  retry?: {
    max_attempts: number;
    delay_ms: number;
    backoff_multiplier?: number;
  };
}

/**
 * Workflow status
 */
export type WorkflowStatus = 'active' | 'inactive';

/**
 * Workflow model
 */
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  definition: {
    steps: WorkflowStep[];
    entry_point?: string;
  };
  version: number;
  status: WorkflowStatus;
  tags?: string[];
  created_at: string;
  updated_at?: string;
}

/**
 * Parameters for creating a workflow
 */
export interface WorkflowCreateParams {
  name: string;
  description?: string;
  definition: {
    steps: WorkflowStep[];
    entry_point?: string;
  };
  tags?: string[];
}

/**
 * Parameters for updating a workflow
 */
export interface WorkflowUpdateParams {
  name?: string;
  description?: string;
  definition?: {
    steps: WorkflowStep[];
    entry_point?: string;
  };
  status?: WorkflowStatus;
  tags?: string[];
}

/**
 * Parameters for executing a workflow
 */
export interface WorkflowExecuteParams {
  params?: Record<string, unknown>;
}

