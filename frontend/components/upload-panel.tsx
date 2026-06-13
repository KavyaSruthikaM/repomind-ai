"use client";

import { useState } from "react";

import { uploadRepo, uploadZip, UploadResult } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

type Props = {
  onUploaded: (result: UploadResult) => void;
};

export function UploadPanel({ onUploaded }: Props) {
  const [repoUrl, setRepoUrl] = useState("");
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleUploadRepo() {
    if (!repoUrl) return;
    setLoading(true);
    setError("");
    try {
      const result = await uploadRepo(repoUrl);
      onUploaded(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload repository");
    } finally {
      setLoading(false);
    }
  }

  async function handleUploadZip() {
    if (!zipFile) return;
    setLoading(true);
    setError("");
    try {
      const result = await uploadZip(zipFile);
      onUploaded(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload ZIP");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">Repository Input</h2>
      <input
        className="w-full rounded-lg border bg-background px-3 py-2"
        placeholder="https://github.com/owner/repo"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
      />
      <Button onClick={handleUploadRepo} disabled={loading} className="w-full">
        {loading ? "Processing..." : "Upload from GitHub"}
      </Button>
      <input
        type="file"
        accept=".zip"
        onChange={(e) => setZipFile(e.target.files?.[0] || null)}
        className="w-full rounded-lg border bg-background px-3 py-2 text-sm"
      />
      <Button onClick={handleUploadZip} disabled={loading || !zipFile} className="w-full bg-transparent border border-border">
        Upload ZIP
      </Button>
      {error ? <p className="text-xs text-red-400">{error}</p> : null}
    </Card>
  );
}
