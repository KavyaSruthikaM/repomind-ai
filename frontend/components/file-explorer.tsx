"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, FileCode2, Folder, FolderOpen } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { FileTreeNode } from "@/lib/files";
import { cn } from "@/lib/utils";

type Props = {
  tree: FileTreeNode[];
  selectedPath?: string;
  onSelectFile: (path: string) => void;
};

function TreeBranch({
  node,
  depth,
  selectedPath,
  expanded,
  onToggle,
  onSelectFile
}: {
  node: FileTreeNode;
  depth: number;
  selectedPath?: string;
  expanded: Set<string>;
  onToggle: (path: string) => void;
  onSelectFile: (path: string) => void;
}) {
  const isFolder = node.type === "folder";
  const isOpen = expanded.has(node.path);
  const isSelected = selectedPath === node.path;

  if (isFolder) {
    return (
      <div>
        <button
          type="button"
          onClick={() => onToggle(node.path)}
          className="flex w-full items-center gap-1 rounded-md px-2 py-1 text-left text-xs hover:bg-white/5"
          style={{ paddingLeft: `${depth * 12 + 8}px` }}
        >
          {isOpen ? <ChevronDown className="h-3.5 w-3.5 text-muted" /> : <ChevronRight className="h-3.5 w-3.5 text-muted" />}
          {isOpen ? <FolderOpen className="h-3.5 w-3.5 text-accent" /> : <Folder className="h-3.5 w-3.5 text-accent" />}
          <span className="truncate text-foreground">{node.name}</span>
        </button>
        {isOpen ? (
          <div>
            {(node.children || []).map((child) => (
              <TreeBranch
                key={child.path}
                node={child}
                depth={depth + 1}
                selectedPath={selectedPath}
                expanded={expanded}
                onToggle={onToggle}
                onSelectFile={onSelectFile}
              />
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onSelectFile(node.path)}
      className={cn(
        "flex w-full items-center gap-1 rounded-md px-2 py-1 text-left text-xs hover:bg-white/5",
        isSelected && "bg-accent/20 text-foreground"
      )}
      style={{ paddingLeft: `${depth * 12 + 24}px` }}
    >
      <FileCode2 className="h-3.5 w-3.5 text-muted" />
      <span className="truncate">{node.name}</span>
    </button>
  );
}

export function FileExplorer({ tree, selectedPath, onSelectFile }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [query, setQuery] = useState("");

  const defaultExpanded = useMemo(() => {
    const paths = new Set<string>();
    for (const node of tree) {
      if (node.type === "folder") paths.add(node.path);
    }
    return paths;
  }, [tree]);

  const activeExpanded = expanded.size ? expanded : defaultExpanded;

  function onToggle(path: string) {
    setExpanded((prev) => {
      const base = prev.size ? new Set(prev) : new Set(defaultExpanded);
      if (base.has(path)) base.delete(path);
      else base.add(path);
      return base;
    });
  }

  const filteredTree = useMemo(() => {
    if (!query.trim()) return tree;
    const q = query.toLowerCase();

    function filterNodes(nodes: FileTreeNode[]): FileTreeNode[] {
      return nodes
        .map((node) => {
          if (node.type === "file") {
            return node.name.toLowerCase().includes(q) || node.path.toLowerCase().includes(q) ? node : null;
          }
          const children = filterNodes(node.children || []);
          if (node.name.toLowerCase().includes(q) || children.length > 0) {
            return { ...node, children };
          }
          return null;
        })
        .filter(Boolean) as FileTreeNode[];
    }

    return filterNodes(tree);
  }, [tree, query]);

  return (
    <Card className="flex h-[55vh] flex-col overflow-hidden">
      <div className="mb-2 space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">Explorer</h2>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search files..."
          className="w-full rounded-md border border-border bg-background px-2 py-1 text-xs"
        />
      </div>
      <div className="flex-1 overflow-auto pr-1">
        {filteredTree.length ? (
          filteredTree.map((node) => (
            <TreeBranch
              key={node.path}
              node={node}
              depth={0}
              selectedPath={selectedPath}
              expanded={activeExpanded}
              onToggle={onToggle}
              onSelectFile={onSelectFile}
            />
          ))
        ) : (
          <p className="text-xs text-muted">Upload a repository to browse its file tree.</p>
        )}
      </div>
    </Card>
  );
}
