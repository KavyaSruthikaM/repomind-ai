import { Card } from "@/components/ui/card";
import type { SelectedFileContext } from "@/lib/files";

type Props = {
  file: SelectedFileContext | null;
  loading?: boolean;
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FilePreview({ file, loading }: Props) {
  if (loading) {
    return (
      <Card className="space-y-2">
        <p className="text-xs text-muted">Loading file preview...</p>
      </Card>
    );
  }

  if (!file) {
    return (
      <Card className="space-y-2">
        <h3 className="text-sm font-semibold">File Preview</h3>
        <p className="text-xs text-muted">Select a file in the explorer to view metadata and content.</p>
      </Card>
    );
  }

  return (
    <Card className="space-y-3">
      <div>
        <h3 className="text-sm font-semibold">{file.name}</h3>
        <p className="truncate text-xs text-muted">{file.path}</p>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs text-muted md:grid-cols-4">
        <div>
          <p className="uppercase tracking-wide">Language</p>
          <p className="text-foreground">{file.language || "unknown"}</p>
        </div>
        <div>
          <p className="uppercase tracking-wide">Size</p>
          <p className="text-foreground">{formatBytes(file.size_bytes)}</p>
        </div>
        <div>
          <p className="uppercase tracking-wide">Lines</p>
          <p className="text-foreground">{file.line_count}</p>
        </div>
        <div>
          <p className="uppercase tracking-wide">Context</p>
          <p className="text-foreground">Attached to chat</p>
        </div>
      </div>
      {file.truncated ? <p className="text-xs text-amber-300">Preview truncated for large file.</p> : null}
      <pre className="max-h-56 overflow-auto rounded-lg border border-border bg-[#0a0e1a] p-3 text-xs leading-5 text-foreground">
        {file.content || "// Empty file"}
      </pre>
    </Card>
  );
}
