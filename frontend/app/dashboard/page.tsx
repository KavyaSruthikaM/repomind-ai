"use client";

import { useState } from "react";

import { ArchitectureDiagram } from "@/components/architecture-diagram";
import { ChatPanel } from "@/components/chat-panel";
import { FileExplorer } from "@/components/file-explorer";
import { FileIntelligencePanel } from "@/components/file-intelligence-panel";
import { SummaryCard } from "@/components/summary-card";
import { UploadPanel } from "@/components/upload-panel";
import { Button } from "@/components/ui/button";
import { getFileContent, getFileIntelligence, getFileTree, getSummary } from "@/lib/api";
import type { ArchitectureAnalysis } from "@/lib/architecture";
import type { FileIntelligence, FileTreeNode, SelectedFileContext } from "@/lib/files";

type RepoState = {
  id: string;
  name: string;
  fileCount: number;
};

export default function DashboardPage() {
  const [repo, setRepo] = useState<RepoState | null>(null);
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<SelectedFileContext | null>(null);
  const [fileIntelligence, setFileIntelligence] = useState<FileIntelligence | null>(null);
  const [selectedPath, setSelectedPath] = useState("");
  const [panelOpen, setPanelOpen] = useState(false);
  const [fileLoading, setFileLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [architecture, setArchitecture] = useState<ArchitectureAnalysis>({});
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "architecture" | "chat">("overview");

  async function onUploaded(result: { repository_id: string; name: string; file_count: number }) {
    setRepo({ id: result.repository_id, name: result.name, fileCount: result.file_count });
    setSelectedFile(null);
    setFileIntelligence(null);
    setSelectedPath("");
    setPanelOpen(false);
    setLoading(true);
    try {
      const [summaryRes, treeRes] = await Promise.all([
        getSummary(result.repository_id),
        getFileTree(result.repository_id)
      ]);
      setSummary(summaryRes.summary);
      setArchitecture(summaryRes.architecture || {});
      setFileTree(treeRes.tree || []);
    } finally {
      setLoading(false);
    }
  }

  async function onSelectFile(path: string) {
    if (!repo?.id) return;
    setSelectedPath(path);
    setPanelOpen(true);
    setFileLoading(true);
    setAiLoading(true);
    setSelectedFile(null);
    setFileIntelligence(null);
    try {
      const content = await getFileContent(repo.id, path);
      setSelectedFile(content);
      setFileLoading(false);

      const intelligence = await getFileIntelligence(repo.id, path);
      setFileIntelligence(intelligence);
      setSelectedFile(intelligence.file);
    } finally {
      setFileLoading(false);
      setAiLoading(false);
    }
  }

  return (
    <main className="min-h-screen p-4 md:p-6">
      <div className="mx-auto max-w-7xl space-y-4">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-3">
            <UploadPanel onUploaded={onUploaded} />
            <FileExplorer tree={fileTree} selectedPath={selectedPath} onSelectFile={onSelectFile} />
          </div>
          <div className="space-y-4 lg:col-span-9">
            <div className="glass inline-flex rounded-lg border border-border p-1">
              <Button onClick={() => setActiveTab("overview")} variant={activeTab === "overview" ? "solid" : "ghost"}>
                Overview
              </Button>
              <Button
                onClick={() => setActiveTab("architecture")}
                variant={activeTab === "architecture" ? "solid" : "ghost"}
              >
                Architecture
              </Button>
              <Button onClick={() => setActiveTab("chat")} variant={activeTab === "chat" ? "solid" : "ghost"}>
                Chat
              </Button>
            </div>

            {activeTab === "overview" ? (
              <SummaryCard
                summary={loading ? "Analyzing repository..." : summary}
                repositoryName={repo?.name || ""}
                architecture={architecture}
              />
            ) : null}

            {activeTab === "architecture" ? (
              <ArchitectureDiagram architecture={architecture} repositoryName={repo?.name} />
            ) : null}

            {activeTab === "chat" ? (
              <ChatPanel repositoryId={repo?.id || ""} selectedFile={selectedFile} />
            ) : null}
          </div>
        </div>
      </div>

      <FileIntelligencePanel
        open={panelOpen}
        loading={fileLoading}
        aiLoading={aiLoading}
        file={selectedFile}
        intelligence={fileIntelligence}
        onClose={() => setPanelOpen(false)}
      />
    </main>
  );
}
