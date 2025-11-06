export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  workflow_progress: number;
  next_questions?: string[];
  workflow_preview?: WorkflowPreview;
}

export interface WorkflowPreview {
  steps: WorkflowStep[];
  connections?: WorkflowConnection[];
}

export interface WorkflowStep {
  id: string;
  type: string;
  name: string;
  description: string;
}

export interface WorkflowConnection {
  from: string;
  to: string;
  condition?: string;
}

export interface WorkflowExecution {
  execution_id: string;
  workflow_id: string;
  workflow_name?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';
  trigger_type: 'manual' | 'scheduled' | 'webhook' | 'api';
  started_at: string;
  completed_at?: string;
  progress: number;
  current_step?: string;
  error_message?: string;
}

export interface ExecutionLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  step_id?: string;
}

export interface ScheduledJob {
  id: string;
  workflow_id: string;
  workflow_name?: string;
  schedule_type: 'cron' | 'interval' | 'one_time';
  schedule: string;
  is_enabled: boolean;
  next_run?: string;
  last_run?: string;
  execution_count: number;
  success_count: number;
  failure_count: number;
}

export interface AnalyticsMetrics {
  total_executions: number;
  success_rate: number;
  average_duration: number;
  active_executions: number;
  failed_executions: number;
}
