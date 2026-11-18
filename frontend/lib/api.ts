import type { Dataset, MLModel, TrainingJob, TrainRequest } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `${status} request failed`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function parseDetail(body: unknown, status: number, statusText: string): string {
  if (body && typeof body === "object") {
    const obj = body as Record<string, unknown>;
    const detail = obj.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (item && typeof item === "object") {
            const e = item as Record<string, unknown>;
            const loc = Array.isArray(e.loc) ? e.loc.join(".") : "";
            return `${loc ? loc + ": " : ""}${String(e.msg ?? "invalid value")}`;
          }
          return String(item);
        })
        .join("; ");
    }
    if (typeof obj.message === "string") return obj.message;
  }
  return `${status} ${statusText}`;
}

export async function apiFetch<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // ignore
    }
    throw new ApiError(res.status, parseDetail(body, res.status, res.statusText));
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return (await res.json()) as T;
  }
  return (await res.text()) as unknown as T;
}

export async function listDatasets() {
  return apiFetch<Dataset[]>("/api/datasets");
}

export async function uploadDataset(file: File) {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<Dataset>("/api/datasets/upload", { method: "POST", body: form });
}

export async function getDataset(id: string | number) {
  return apiFetch<Dataset>(`/api/datasets/${id}`);
}

export async function createTrainingJob(payload: TrainRequest) {
  return apiFetch<TrainingJob>("/api/training/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function listJobs() {
  return apiFetch<TrainingJob[]>("/api/training");
}

export async function getJob(id: string | number) {
  return apiFetch<TrainingJob>(`/api/training/${id}`);
}

export async function listModels() {
  return apiFetch<MLModel[]>("/api/models");
}

export function modelDownloadUrl(m: MLModel) {
  if (m.download_url) {
    const url = m.download_url;
    if (url.startsWith("/")) return `${API_BASE}${url}`;
    if (url.startsWith(`${API_BASE}/`)) return url;
  }
  return `${API_BASE}/api/models/${m.id}/download`;
}

export interface EDAResult {
  dataset_id: string | number;
  summary: {
    shape?: number[];
    columns?: string[];
    dtypes?: Record<string, string>;
    missing?: Record<string, number>;
    numeric_summary?: Record<string, unknown>;
    categorical_summary?: Record<string, unknown>;
    correlation?: Array<{ a: string; b: string; value: number }>;
    [key: string]: unknown;
  };
  plots: string[];
}

export async function runEDA(id: string | number) {
  return apiFetch<EDAResult>(`/api/eda/${id}`, { method: "POST" });
}

export async function sendChat(
  datasetId: string | number,
  message: string,
  history: Array<{ role: string; content: string }> = [],
  lang: string = "en"
) {
  return apiFetch<{ reply: string }>("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId, message, history, lang }),
  });
}

export async function downloadReport(id: string | number, lang: string = "es"): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/reports/${id}?lang=${encodeURIComponent(lang)}`, {
    method: "POST",
  });
  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // ignore
    }
    throw new ApiError(res.status, parseDetail(body, res.status, res.statusText));
  }
  return await res.blob();
}

export function reportDownloadUrl(id: string | number) {
  return `${API_BASE}/api/reports/${id}/download`;
}
