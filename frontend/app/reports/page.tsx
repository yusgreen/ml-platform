"use client";

import { useEffect, useState } from "react";
import { useT, useLanguage } from "@/lib/i18n";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { listDatasets, downloadReport } from "@/lib/api";
import type { Dataset } from "@/lib/types";

export default function ReportsPage() {
  const t = useT();
  const { lang } = useLanguage();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState<string>("");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportUrl, setReportUrl] = useState<string | null>(null);

  useEffect(() => {
    listDatasets()
      .then((d) => {
        const arr = Array.isArray(d) ? d : [];
        setDatasets(arr);
        if (arr.length) setDatasetId(String(arr[0].id));
      })
      .catch((e) => setError(e instanceof Error ? e.message : t("reports.failedLoad")));
  }, []);

  useEffect(() => {
    setReportUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setError(null);
  }, [datasetId]);

  useEffect(() => {
    return () => {
      if (reportUrl) URL.revokeObjectURL(reportUrl);
    };
  }, [reportUrl]);

  async function onGenerate() {
    if (!datasetId) return;
    setGenerating(true);
    setError(null);
    setReportUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    try {
      const blob = await downloadReport(datasetId, lang);
      const url = URL.createObjectURL(blob);
      setReportUrl(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("reports.reportFailed"));
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("reports.title")}</h1>

      <Card>
        <CardHeader>
          <CardTitle>{t("reports.generateReport")}</CardTitle>
          <CardDescription>{t("reports.selectDataset")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
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
          <Button onClick={onGenerate} disabled={generating || !datasetId}>
            {generating ? t("reports.generating") : t("reports.generate")}
          </Button>
          {error && <p className="text-sm text-red-600">{error}</p>}
          {reportUrl && (
            <div>
              <a href={reportUrl} download="report.pdf" target="_blank" rel="noreferrer">
                <Button variant="outline" size="sm">
                  {t("reports.downloadPdf")}
                </Button>
              </a>
            </div>
          )}

        </CardContent>
      </Card>
    </div>
  );
}