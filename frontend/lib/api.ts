import type { ArchitectureAnalysis } from "@/lib/architecture";
import type { FileContent, FileIntelligence, FileTreeNode } from "@/lib/files";

export type UploadResult = {
  repository_id: string;
  name: string;
  file_count: number;
};

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function uploadRepo(repoUrl: string): Promise<UploadResult> {
  const response = await fetch(`${BACKEND_URL}/upload-repo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl })
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function uploadZip(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${BACKEND_URL}/upload-zip`, { method: "POST", body: formData });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function getSummary(repositoryId: string) {
  const response = await fetch(`${BACKEND_URL}/summary?repository_id=${repositoryId}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<{
    summary: string;
    architecture: ArchitectureAnalysis;
  }>;
}

export async function getFiles(repositoryId: string) {
  const response = await fetch(`${BACKEND_URL}/files?repository_id=${repositoryId}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<{ files: Array<{ path: string; language?: string }> }>;
}

export async function getFileTree(repositoryId: string) {
  const response = await fetch(`${BACKEND_URL}/files/tree?repository_id=${repositoryId}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<{ tree: FileTreeNode[] }>;
}

export async function getFileContent(repositoryId: string, path: string) {
  const response = await fetch(
    `${BACKEND_URL}/files/content?repository_id=${repositoryId}&path=${encodeURIComponent(path)}`
  );
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<FileContent>;
}

export async function getFileIntelligence(repositoryId: string, path: string) {
  const response = await fetch(
    `${BACKEND_URL}/files/intelligence?repository_id=${repositoryId}&path=${encodeURIComponent(path)}`
  );
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<FileIntelligence>;
}

export async function chat(repositoryId: string, question: string, filePath?: string) {
  const response = await fetch(`${BACKEND_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repository_id: repositoryId,
      question,
      file_path: filePath || null
    })
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<{ answer: string; references: Array<Record<string, string>> }>;
}
