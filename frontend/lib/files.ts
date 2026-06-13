export type FileTreeNode = {
  name: string;
  path: string;
  type: "file" | "folder";
  language?: string | null;
  children?: FileTreeNode[];
};

export type FileContent = {
  path: string;
  name: string;
  language?: string | null;
  size_bytes: number;
  line_count: number;
  content: string;
  truncated: boolean;
};

export type SelectedFileContext = FileContent;

export type RelatedModule = {
  path: string;
  name: string;
  reason: string;
};

export type FileIntelligence = {
  file: FileContent;
  explanation: string;
  architectural_role: string;
  imports: string[];
  related_modules: RelatedModule[];
  references: Array<Record<string, string>>;
};
