"use client";

import { useEffect, useState } from "react";
import { useT } from "@/lib/i18n";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Progress } from "@/components/ui/Progress";
import { listDatasets, getDataset, createTrainingJob, getJob } from "@/lib/api";
import type { Dataset, TrainingJob } from "@/lib/types";

export default function TrainPage() {
  const t = useT();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState<string>("");
  const [columns, setColumns] = useState<string[]>([]);
  const [taskType, setTaskType] = useState("supervised");
  const [problem, setProblem] = useState("classification");
  const [algorithm, setAlgorithm] = useState("logistic_regression");
  const [targetColumn, setTargetColumn] = useState("");
  const [testSize, setTestSize] = useState("0.2");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<TrainingJob | null>(null);

  const problemsByTask: Record<string, { label: string; value: string }[]> = {
    supervised: [
      { label: t("train.classification"), value: "classification" },
      { label: t("train.regression"), value: "regression" },
    ],
    unsupervised: [
      { label: t("train.clustering"), value: "clustering" },
      { label: t("train.dimensionality"), value: "dimensionality" },
    ],
  };

  const algorithmsByProblem: Record<string, { label: string; value: string }[]> = {
    classification: [
      { label: "Logistic Regression", value: "logistic" },
      { label: "Random Forest", value: "random_forest" },
      { label: "XGBoost", value: "xgboost" },
    ],
    regression: [
      { label: "Linear Regression", value: "linear" },
      { label: "Random Forest Regressor", value: "random_forest" },
      { label: "XGBoost", value: "xgboost" },
    ],
    clustering: [
      { label: "K-Means", value: "kmeans" },
      { label: "DBSCAN", value: "dbscan" },
    ],
    dimensionality: [{ label: "PCA", value: "pca" }],
  };

  useEffect(() => {
    listDatasets()
      .then((d) => {
        const arr = Array.isArray(d) ? d : [];
        setDatasets(arr);
        if (arr.length) setDatasetId(String(arr[0].id));
      })
      .catch((e) => setError(e instanceof Error ? e.message : t("train.failedLoad")));
  }, []);

  useEffect(() => {
    const probs = problemsByTask[taskType];
    if (probs && !probs.find((p) => p.value === problem)) {
      setProblem(probs[0].value);
    }
  }, [taskType, problem]);

  useEffect(() => {
    const algs = algorithmsByProblem[problem];
    if (algs && !algs.find((a) => a.value === algorithm)) {
      setAlgorithm(algs[0]?.value ?? "");
    }
  }, [problem, algorithm]);

  useEffect(() => {
    if (!datasetId) {
      setColumns([]);
      setTargetColumn("");
      return;
    }
    let cancelled = false;
    setColumns([]);
    setTargetColumn("");
    setJob(null);
    setError(null);
    getDataset(datasetId)
      .then((d) => {
        if (cancelled) return;
        const cols = Array.isArray(d.columns) ? d.columns : [];
        setColumns(cols);
        setTargetColumn((prev) => (prev && cols.includes(prev) ? prev : ""));
      })
      .catch(() => {
        if (!cancelled) setColumns([]);
      });
    return () => {
      cancelled = true;
    };
  }, [datasetId]);

  useEffect(() => {
    if (!job?.id) return;
    if (job.status === "completed" || job.status === "failed") return;
    let cancelled = false;
    const id = job.id;
    const timer = setInterval(async () => {
      try {
        const j = await getJob(id);
        if (!cancelled) setJob(j);
      } catch {
        // ignore transient polling errors
      }
    }, 2000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [job?.id, job?.status]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!datasetId) return;
    const size = Number.parseFloat(testSize);
    if (!Number.isFinite(size) || size <= 0.05 || size >= 0.5) {
      setError(t("train.invalidTestSize"));
      return;
    }
    if (taskType === "supervised" && !targetColumn) {
      setError(t("train.targetRequired"));
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const j = await createTrainingJob({
        dataset_id: datasetId,
        task_type: taskType,
        problem,
        algorithm,
        target_column: targetColumn || undefined,
        test_size: size,
      });
      setJob(j);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("train.trainingFailed"));
    } finally {
      setSubmitting(false);
    }
  }

  const problems = problemsByTask[taskType] ?? [];
  const algorithms = algorithmsByProblem[problem] ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("train.title")}</h1>

      <Card>
        <CardHeader>
          <CardTitle>{t("train.config")}</CardTitle>
          <CardDescription>{t("train.configDesc")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <label className="text-sm font-medium">{t("common.dataset")}</label>
              <Select value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
                {datasets.map((d) => (
                  <option key={String(d.id)} value={String(d.id)}>
                    {String(d.name ?? d.filename ?? d.id)}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">{t("train.taskType")}</label>
              <Select value={taskType} onChange={(e) => setTaskType(e.target.value)}>
                <option value="supervised">{t("train.supervised")}</option>
                <option value="unsupervised">{t("train.unsupervised")}</option>
              </Select>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">{t("train.problem")}</label>
              <Select value={problem} onChange={(e) => setProblem(e.target.value)}>
                {problems.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">{t("common.algorithm")}</label>
              <Select value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
                {algorithms.map((a) => (
                  <option key={a.value} value={a.value}>
                    {a.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">{t("train.targetColumn")}</label>
              {columns.length > 0 ? (
                <Select value={targetColumn} onChange={(e) => setTargetColumn(e.target.value)}>
                  <option value="">{t("common.none")}</option>
                  {columns.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </Select>
              ) : (
                <Input value={targetColumn} onChange={(e) => setTargetColumn(e.target.value)} placeholder="target" />
              )}
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">{t("train.testSize")}</label>
              <Input
                type="number"
                step="0.05"
                min="0.1"
                max="0.4"
                value={testSize}
                onChange={(e) => setTestSize(e.target.value)}
              />
            </div>

            <div className="sm:col-span-2">
              <Button type="submit" disabled={submitting || !datasetId}>
                {submitting ? t("train.submitting") : t("train.start")}
              </Button>
            </div>
          </form>
          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        </CardContent>
      </Card>

      {job && (
        <Card>
          <CardHeader>
            <CardTitle>{t("train.job")} {String(job.id)}</CardTitle>
            <CardDescription>{t("train.status")}: {job.status ?? "unknown"}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {typeof job.progress === "number" && <Progress value={job.progress} />}
            {(job.metrics_json || job.metrics) && (
              <pre className="overflow-auto rounded bg-slate-100 p-3 text-xs">
                {JSON.stringify(job.metrics_json || job.metrics, null, 2)}
              </pre>
            )}
            {job.error && <p className="text-sm text-red-600">{String(job.error)}</p>}
          </CardContent>
        </Card>
      )}
    </div>
  );
}