"use client";

import Link from "next/link";
import { useT } from "@/lib/i18n";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Database, Brain, FlaskConical, Package } from "lucide-react";

export default function Home() {
  const t = useT();
  const items = [
    { href: "/datasets", title: t("home.cards.datasets.title"), desc: t("home.cards.datasets.desc"), icon: Database },
    { href: "/train", title: t("home.cards.train.title"), desc: t("home.cards.train.desc"), icon: Brain },
    { href: "/experiments", title: t("home.cards.experiments.title"), desc: t("home.cards.experiments.desc"), icon: FlaskConical },
    { href: "/models", title: t("home.cards.models.title"), desc: t("home.cards.models.desc"), icon: Package },
  ];
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{t("home.title")}</h1>
        <p className="mt-2 text-slate-600">{t("home.subtitle")}</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((it) => {
          const Icon = it.icon;
          return (
            <Card key={it.href}>
              <CardHeader>
                <Icon className="h-6 w-6 text-slate-700" />
                <CardTitle className="mt-2">{it.title}</CardTitle>
                <CardDescription>{it.desc}</CardDescription>
              </CardHeader>
              <CardContent>
                <Link href={it.href}>
                  <Button variant="outline" size="sm">
                    {t("common.open")}
                  </Button>
                </Link>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}