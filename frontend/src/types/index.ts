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
