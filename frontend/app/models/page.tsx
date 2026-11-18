"use client";

import { useEffect, useState } from "react";
import { useT } from "@/lib/i18n";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/Table";
import { listModels, modelDownloadUrl } from "@/lib/api";
import type { MLModel } from "@/lib/types";

export default function ModelsPage() {
  const t = useT();
  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await listModels();
      setModels(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("models.failedLoad"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("models.title")}</h1>
        <Button variant="outline" size="sm" onClick={load}>
          {t("common.refresh")}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("models.trainedModels")}</CardTitle>
        </CardHeader>
        <CardContent>
          {error && <p className="mb-2 text-sm text-red-600">{error}</p>}
          {loading && models.length === 0 ? (
            <p className="text-slate-500">{t("common.loading")}</p>
          ) : models.length === 0 ? (
            <p className="text-slate-500">{t("models.noModels")}</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("common.id")}</TableHead>
                  <TableHead>{t("common.name")}</TableHead>
                  <TableHead>{t("common.algorithm")}</TableHead>
                  <TableHead>{t("common.metrics")}</TableHead>
                  <TableHead>{t("common.download")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {models.map((m) => (
                  <TableRow key={String(m.id)}>
                    <TableCell>{String(m.id)}</TableCell>
                    <TableCell>{String(m.name ?? m.id)}</TableCell>
                    <TableCell>{String(m.algorithm ?? "-")}</TableCell>
                    <TableCell>
                      {m.metrics ? (
                        <details>
                          <summary className="cursor-pointer text-blue-600">{t("common.view")}</summary>
                          <pre className="mt-2 max-w-xs overflow-auto rounded bg-slate-100 p-2 text-xs">
                            {JSON.stringify(m.metrics, null, 2)}
                          </pre>
                        </details>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell>
                      <a href={modelDownloadUrl(m)} download>
                        <Button size="sm" variant="outline">
                          {t("models.download")}
                        </Button>
                      </a>
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