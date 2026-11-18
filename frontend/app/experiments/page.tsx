"use client";

import { useEffect, useRef, useState } from "react";
import { useT } from "@/lib/i18n";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/Table";
import { Progress } from "@/components/ui/Progress";
import { listJobs } from "@/lib/api";
import type { TrainingJob } from "@/lib/types";

export default function ExperimentsPage() {
  const t = useT();
  const tRef = useRef(t);
  tRef.current = t;
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await listJobs();
      setJobs(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : tRef.current("experiments.failedLoad"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  // Poll only while there is at least one job still running.
  const hasActiveJobs = jobs.some((j) => j.status === "pending" || j.status === "running");
  useEffect(() => {
    if (!hasActiveJobs) return;
    const timer = setInterval(() => {
      load();
    }, 5000);
    return () => clearInterval(timer);
  }, [hasActiveJobs]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("experiments.title")}</h1>
        <Button variant="outline" size="sm" onClick={load}>
          {t("common.refresh")}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("experiments.trainingJobs")}</CardTitle>
        </CardHeader>
        <CardContent>
          {error && <p className="mb-2 text-sm text-red-600">{error}</p>}
          {loading && jobs.length === 0 ? (
            <p className="text-slate-500">{t("common.loading")}</p>
          ) : jobs.length === 0 ? (
            <p className="text-slate-500">{t("experiments.noExperiments")}</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("common.id")}</TableHead>
                  <TableHead>{t("common.dataset")}</TableHead>
                  <TableHead>{t("common.algorithm")}</TableHead>
                  <TableHead>{t("common.status")}</TableHead>
                  <TableHead>{t("common.progress")}</TableHead>
                  <TableHead>{t("common.metrics")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((j) => (
                  <TableRow key={String(j.id)}>
                    <TableCell>{String(j.id)}</TableCell>
                    <TableCell>{String(j.dataset_name ?? j.dataset_id ?? "-")}</TableCell>
                    <TableCell>{String(j.algorithm ?? "-")}</TableCell>
                    <TableCell>{String(j.status ?? "-")}</TableCell>
                    <TableCell className="w-32">
                      {typeof j.progress === "number" ? <Progress value={j.progress} /> : "-"}
                    </TableCell>
                    <TableCell>
                      {(j.metrics_json || j.metrics) ? (
                        <details>
                          <summary className="cursor-pointer text-blue-600">{t("common.view")}</summary>
                          <pre className="mt-2 max-w-xs overflow-auto rounded bg-slate-100 p-2 text-xs">
                            {JSON.stringify(j.metrics_json || j.metrics, null, 2)}
                          </pre>
                        </details>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}