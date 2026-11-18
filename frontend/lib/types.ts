export interface Dataset {
  id: string | number;
  name?: string;
  filename?: string;
  rows?: number;
  cols?: number;
  columns?: string[];
  created_at?: string;
  [key: string]: unknown;
}

export interface TrainingJob {
  id: string | number;
  dataset_id?: string | number;
  dataset_name?: string;
  task_type?: string;
  problem?: string;
  algorithm?: string;
  target_column?: string;
  test_size?: number;
  status?: "queued" | "running" | "completed" | "failed" | string;
  progress?: number;
  metrics?: Record<string, unknown>;
  metrics_json?: Record<string, unknown>;
  error?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface MLModel {
  id: string | number;
  name?: string;
  algorithm?: string;
  dataset_id?: string | number;
  metrics?: Record<string, unknown>;
  download_url?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface TrainRequest {
  dataset_id: string | number;
  task_type: string;
  problem: string;
  algorithm: string;
  target_column?: string;
  test_size?: number;
}
