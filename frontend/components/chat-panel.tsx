"use client";

import { FormEvent, useState } from "react";

import { chat } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { SelectedFileContext } from "@/lib/files";

type Message = { role: "user" | "assistant"; content: string };

type Props = {
  repositoryId: string;
  selectedFile?: SelectedFileContext | null;
};

export function ChatPanel({ repositoryId, selectedFile }: Props) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!question.trim() || !repositoryId) return;
    const currentQuestion = question.trim();
    setQuestion("");
    setMessages((prev) => [...prev, { role: "user", content: currentQuestion }]);
    setLoading(true);
    try {
      const result = await chat(repositoryId, currentQuestion, selectedFile?.path);
      const chunks = result.answer.split(". ");
      let assembled = "";
      for (const chunk of chunks) {
        assembled += `${chunk}. `;
        setMessages((prev) => {
          const next = [...prev];
          if (next[next.length - 1]?.role === "assistant") {
            next[next.length - 1] = { role: "assistant", content: assembled.trim() };
          } else {
            next.push({ role: "assistant", content: assembled.trim() });
          }
          return next;
        });
        await new Promise((resolve) => setTimeout(resolve, 40));
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="flex h-[55vh] flex-col">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">AI Chat</h2>
        {selectedFile ? (
          <span className="truncate rounded-md bg-accent/15 px-2 py-1 text-xs text-accent">
            Context: {selectedFile.name}
          </span>
        ) : null}
      </div>
      <div className="mb-3 flex-1 space-y-3 overflow-auto pr-1">
        {messages.length ? (
          messages.map((m, idx) => (
            <div
              key={`${m.role}-${idx}`}
              className={`rounded-lg px-3 py-2 text-sm ${m.role === "user" ? "bg-accent/20" : "bg-white/5"}`}
            >
              {m.content}
            </div>
          ))
        ) : (
          <p className="text-xs text-muted">
            Ask about architecture, auth flow, APIs, and data handling. Select a file to include it as chat context.
          </p>
        )}
      </div>
      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          className="flex-1 rounded-lg border bg-background px-3 py-2 text-sm"
          placeholder={
            selectedFile
              ? `Ask about ${selectedFile.name}...`
              : "How does authentication flow through this project?"
          }
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <Button disabled={loading || !repositoryId}>{loading ? "..." : "Send"}</Button>
      </form>
    </Card>
  );
}
