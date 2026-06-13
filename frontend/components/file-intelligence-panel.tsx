"use client";

import { X, Network, FileCode2, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { FileIntelligence, SelectedFileContext } from "@/lib/files";
import { cn } from "@/lib/utils";

type Props = {
  open: boolean;
  loading: boolean;
  aiLoading?: boolean;
  file: SelectedFileContext | null;
  intelligence: FileIntelligence | null;
  onClose: () => void;
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton rounded-md", className)} />;
}

export function FileIntelligencePanel({ open, loading, aiLoading = false, file, intelligence, onClose }: Props) {
  if (!open) return null;

  const role = intelligence?.architectural_role || "analyzing";

  return (
    <div className="fixed inset-0 z-50">
      <button
        type="button"
        aria-label="Close file intelligence panel"
        className="panel-backdrop absolute inset-0 bg-black/60"
        onClick={onClose}
      />
      <aside className="panel-slide absolute right-0 top-0 flex h-full w-full max-w-xl flex-col border-l border-border bg-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-wide text-muted">File Intelligence</p>
            <h3 className="truncate text-sm font-semibold">{file?.name || "Selected file"}</h3>
          </div>
          <Button variant="ghost" onClick={onClose} aria-label="Close panel">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 space-y-4 overflow-auto p-4">
          <Card className="panel-section space-y-3">
            <div className="flex items-center gap-2">
              <FileCode2 className="h-4 w-4 text-accent" />
              <h4 className="text-sm font-semibold">Metadata</h4>
            </div>
            {loading && !file ? (
              <div className="space-y-2">
                <Skeleton className="h-3 w-2/3" />
                <Skeleton className="h-3 w-1/2" />
                <Skeleton className="h-3 w-1/3" />
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <p className="text-muted">Path</p>
                  <p className="truncate text-foreground">{file?.path}</p>
                </div>
                <div>
                  <p className="text-muted">Language</p>
                  <p className="text-foreground">{file?.language || "unknown"}</p>
                </div>
                <div>
                  <p className="text-muted">Size</p>
                  <p className="text-foreground">{file ? formatBytes(file.size_bytes) : "-"}</p>
                </div>
                <div>
                  <p className="text-muted">Lines</p>
                  <p className="text-foreground">{file?.line_count ?? "-"}</p>
                </div>
              </div>
            )}
            <div className="inline-flex rounded-md bg-accent/15 px-2 py-1 text-xs text-accent">
              Architectural role: {role}
            </div>
          </Card>

          <Card className="panel-section space-y-2">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-accent" />
              <h4 className="text-sm font-semibold">AI Explanation</h4>
            </div>
            {aiLoading && !intelligence ? (
              <div className="space-y-2">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-11/12" />
              </div>
            ) : (
              <p className="whitespace-pre-wrap text-sm text-muted">{intelligence?.explanation}</p>
            )}
          </Card>

          <Card className="panel-section space-y-2">
            <h4 className="text-sm font-semibold">Imports / Dependencies</h4>
            {aiLoading && !intelligence ? (
              <Skeleton className="h-16 w-full" />
            ) : (
              <div className="flex flex-wrap gap-1">
                {(intelligence?.imports || []).length ? (
                  intelligence?.imports.map((item) => (
                    <span key={item} className="rounded-md border border-border px-2 py-1 text-xs text-muted">
                      {item}
                    </span>
                  ))
                ) : (
                  <p className="text-xs text-muted">No imports detected.</p>
                )}
              </div>
            )}
          </Card>

          <Card className="panel-section space-y-2">
            <div className="flex items-center gap-2">
              <Network className="h-4 w-4 text-accent" />
              <h4 className="text-sm font-semibold">Related Modules</h4>
            </div>
            {aiLoading && !intelligence ? (
              <Skeleton className="h-20 w-full" />
            ) : (
              <ul className="space-y-2">
                {(intelligence?.related_modules || []).map((module) => (
                  <li key={module.path} className="rounded-md border border-border px-2 py-2 text-xs">
                    <p className="font-medium text-foreground">{module.name}</p>
                    <p className="truncate text-muted">{module.path}</p>
                    <p className="text-muted">{module.reason}</p>
                  </li>
                ))}
                {!intelligence?.related_modules?.length ? (
                  <li className="text-xs text-muted">No related modules found from retrieval.</li>
                ) : null}
              </ul>
            )}
          </Card>

          <Card className="panel-section space-y-2">
            <h4 className="text-sm font-semibold">Content Preview</h4>
            {loading && !file ? (
              <Skeleton className="h-40 w-full" />
            ) : (
              <pre className="max-h-56 overflow-auto rounded-lg border border-border bg-[#0a0e1a] p-3 text-xs leading-5 text-foreground">
                {file?.content || "// Empty file"}
              </pre>
            )}
            {file?.truncated ? <p className="text-xs text-amber-300">Preview truncated for large file.</p> : null}
          </Card>
        </div>
      </aside>
    </div>
  );
}
