"use client";

import { useEffect, useState } from "react";
import { useT } from "@/lib/i18n";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { listDatasets, runEDA, API_BASE } from "@/lib/api";
import type { Dataset } from "@/lib/types";
import type { EDAResult } from "@/lib/api";

export default function EDAPage() {
  const t = useT();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EDAResult | null>(null);

  useEffect(() => {
    setLoading(true);
    listDatasets()
      .then((d) => {
        const arr = Array.isArray(d) ? d : [];
        setDatasets(arr);
        if (arr.length) setDatasetId(String(arr[0].id));
      })
      .catch((e) => setError(e instanceof Error ? e.message : t("eda.failedLoad")))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setResult(null);
    setError(null);
  }, [datasetId]);

  async function onGenerate() {
    if (!datasetId) return;
    setGenerating(true);
    setError(null);
    try {
      const r = await runEDA(datasetId);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("eda.edaFailed"));
    } finally {
      setGenerating(false);
    }
  }

  const summary = result?.summary;
  const missing = Object.fromEntries(
    Object.entries(summary?.missing ?? {}).filter(([, value]) => Number(value) > 0)
  );
  const correlation = summary?.correlation ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("eda.title")}</h1>

      <Card>
        <CardHeader>
          <CardTitle>{t("eda.exploratory")}</CardTitle>
          <CardDescription>{t("eda.selectDataset")}</CardDescription>
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
          <Button onClick={onGenerate} disabled={generating || !datasetId || loading}>
            {generating ? t("eda.generating") : t("eda.generate")}
          </Button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </CardContent>
      </Card>

      {result && summary && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>{t("eda.summary")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium">{t("eda.shape")}</h4>
                <p className="text-sm text-slate-600">
                  {Array.isArray(summary.shape) ? summary.shape.join(" x ") : "-"}
                </p>
              </div>
              <div>
                <h4 className="font-medium">{t("eda.missing")}</h4>
                {Object.keys(missing).length === 0 ? (
                  <p className="text-sm text-slate-500">{t("eda.noneMissing")}</p>
                ) : (
                  <ul className="text-sm text-slate-600">
                    {Object.entries(missing).map(([k, v]) => (
                      <li key={k}>
                        {k}: {String(v)}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <h4 className="font-medium">{t("eda.correlation")}</h4>
                {correlation.length === 0 ? (
                  <p className="text-sm text-slate-500">{t("eda.noCorrelation")}</p>
                ) : (
                  <ul className="text-sm text-slate-600">
                    {correlation.map((c, i) => (
                      <li key={i}>
                        {c.a} vs {c.b}: {c.value.toFixed(4)}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </CardContent>
          </Card>

          {result.plots && result.plots.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>{t("eda.plots")}</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                {result.plots.map((p, i) => (
                  <img
                    key={i}
                    src={`${API_BASE}${p}`}
                    alt={`plot-${i}`}
                    className="w-full rounded border border-slate-200"
                  />
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}