"use client";

import { useEffect, useRef, useState } from "react";
import { useT, useLanguage } from "@/lib/i18n";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { listDatasets, sendChat } from "@/lib/api";
import type { Dataset } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const t = useT();
  const { lang } = useLanguage();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    listDatasets()
      .then((d) => {
        const arr = Array.isArray(d) ? d : [];
        setDatasets(arr);
        if (arr.length) setDatasetId(String(arr[0].id));
      })
      .catch((e) => setError(e instanceof Error ? e.message : t("chat.failedLoad")));
  }, []);

  // Switching datasets starts a fresh conversation: history from another
  // dataset must never be sent or displayed.
  useEffect(() => {
    requestIdRef.current += 1;
    setMessages([]);
    setInput("");
    setError(null);
    setSending(false);
  }, [datasetId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function onSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || !datasetId) return;
    setInput("");
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    setError(null);
    const reqId = ++requestIdRef.current;
    const activeDataset = datasetId;
    try {
      const res = await sendChat(activeDataset, text, history, lang);
      if (reqId !== requestIdRef.current) return;
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch (e) {
      if (reqId !== requestIdRef.current) return;
      const msg = e instanceof Error ? e.message : "";
      if (msg.includes("429") || msg.toLowerCase().includes("rate limit")) {
        setError(t("chat.rateLimit"));
      } else {
        setError(msg || t("chat.chatFailed"));
      }
    } finally {
      if (reqId === requestIdRef.current) setSending(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("chat.title")}</h1>

      <Card>
        <CardHeader>
          <CardTitle>{t("chat.dataset")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Select value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
            {datasets.map((d) => (
              <option key={String(d.id)} value={String(d.id)}>
                {String(d.name ?? d.filename ?? d.id)}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("chat.messages")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="max-h-96 space-y-3 overflow-y-auto rounded border border-slate-200 bg-slate-50 p-3">
            {messages.length === 0 ? (
              <p className="text-sm text-slate-500">{t("chat.noMessages")}</p>
            ) : (
              messages.map((m, i) => (
                <div
                  key={i}
                  className={
                    m.role === "user"
                      ? "ml-auto max-w-[80%] rounded bg-slate-900 px-3 py-2 text-sm text-white"
                      : "max-w-[80%] rounded bg-white px-3 py-2 text-sm text-slate-900 shadow"
                  }
                >
                  {m.content}
                </div>
              ))
            )}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={onSend} className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t("chat.placeholder")}
              disabled={sending}
            />
            <Button type="submit" disabled={sending || !input.trim() || !datasetId}>
              {sending ? t("chat.sending") : t("chat.send")}
            </Button>
          </form>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </CardContent>
      </Card>
    </div>
  );
}