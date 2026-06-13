"use client";

import { useEffect, useMemo, useState } from "react";
import mermaid from "mermaid";

import { Card } from "@/components/ui/card";
import type { ArchitectureAnalysis } from "@/lib/architecture";

type Props = {
  architecture?: ArchitectureAnalysis;
  repositoryName?: string;
};

function sanitizeNodeLabel(value: string) {
  return value.replace(/["<>]/g, "").replace(/\n/g, " ").slice(0, 56);
}

function safeId(value: string) {
  const cleaned = value.replace(/[^a-zA-Z0-9_]/g, "_");
  return cleaned.match(/^[0-9]/) ? `n_${cleaned}` : cleaned;
}

function buildMermaidFromEntities(architecture?: ArchitectureAnalysis) {
  const entities = architecture?.entities || [];
  const routes = architecture?.routes || [];
  const dependencies = architecture?.dependencies || [];
  const directories = architecture?.directories || [];

  if (!entities.length && !routes.length && !dependencies.length) {
    return "";
  }

  const lines: string[] = ["flowchart TB"];
  lines.push('classDef route fill:#2a1f4d,stroke:#6f5bd6,color:#efe8ff;');
  lines.push('classDef middleware fill:#1f2a44,stroke:#4f6ea8,color:#dce3ff;');
  lines.push('classDef controller fill:#1f3444,stroke:#4f8ea8,color:#dce3ff;');
  lines.push('classDef service fill:#1f4434,stroke:#4fa88e,color:#dce3ff;');
  lines.push('classDef model fill:#44341f,stroke:#a88e4f,color:#ffe9c7;');
  lines.push('classDef database fill:#0e2230,stroke:#2f5974,color:#d7f0ff;');
  lines.push('classDef module fill:#141a2d,stroke:#3b456d,color:#dce3ff;');

  const nodeIds = new Map<string, string>();

  const register = (key: string, label: string, layer: string) => {
    const id = safeId(key);
    if (!nodeIds.has(id)) {
      const className = ["route", "middleware", "controller", "service", "model", "database"].includes(layer)
        ? layer
        : "module";
      lines.push(`${id}["${sanitizeNodeLabel(label)}"]:::${className}`);
      nodeIds.set(id, className);
    }
    return id;
  };

  const grouped = new Map<string, typeof entities>();
  for (const entity of entities) {
    const top = entity.path.includes("/") ? entity.path.split("/")[0] : "root";
    const bucket = grouped.get(top) || [];
    bucket.push(entity);
    grouped.set(top, bucket);
  }

  for (const directory of directories.slice(0, 8)) {
    const top = directory.split("/")[0];
    const bucket = grouped.get(top);
    if (!bucket?.length) continue;
    lines.push(`subgraph ${safeId(directory)} ["${sanitizeNodeLabel(directory)}"]`);
    for (const entity of bucket.slice(0, 14)) {
      register(entity.id, entity.name, entity.layer);
    }
    lines.push("end");
  }

  for (const route of routes.slice(0, 24)) {
    const routeNode = register(`route:${route.file}:${route.method}:${route.path}`, `${route.method} ${route.path}`, "route");
    const fileNode = register(route.file, route.file.split("/").pop() || route.file, "route");
    lines.push(`${routeNode} --> ${fileNode}`);
  }

  for (const edge of dependencies.slice(0, 50)) {
    const fromNode = register(edge.from, edge.from.split("/").pop() || edge.from, "module");
    const toNode = register(edge.to, edge.to.split("/").pop() || edge.to, "module");
    lines.push(`${fromNode} --> ${toNode}`);
  }

  return lines.join("\n");
}

export function ArchitectureDiagram({ architecture, repositoryName }: Props) {
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");

  const definition = useMemo(() => {
    if (architecture?.mermaid?.trim()) {
      return architecture.mermaid;
    }
    return buildMermaidFromEntities(architecture);
  }, [architecture]);

  useEffect(() => {
    if (!definition) {
      setSvg("");
      setError("");
      return;
    }

    let mounted = true;
    mermaid.initialize({
      startOnLoad: false,
      theme: "dark",
      securityLevel: "loose",
      flowchart: {
        curve: "basis",
        useMaxWidth: true,
        htmlLabels: true
      }
    });

    mermaid
      .render(`architecture-graph-${Date.now()}`, definition)
      .then(({ svg: rendered }) => {
        if (!mounted) return;
        setSvg(rendered);
        setError("");
      })
      .catch((err: unknown) => {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "Failed to render architecture diagram.");
      });

    return () => {
      mounted = false;
    };
  }, [definition]);

  const entityCount = architecture?.entities?.length || 0;
  const routeCount = architecture?.routes?.length || architecture?.api_routes?.length || 0;
  const dependencyCount = architecture?.dependencies?.length || 0;

  return (
    <Card className="glass space-y-3 overflow-hidden">
      <div>
        <h2 className="text-lg font-semibold">Architecture Visualization</h2>
        <p className="text-xs text-muted">
          Repository-specific diagram for {repositoryName || "uploaded repo"} — {entityCount} modules, {routeCount}{" "}
          routes, {dependencyCount} import links.
        </p>
      </div>
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
      <div className="overflow-auto rounded-lg border border-border bg-[#0a0e1a] p-3">
        {svg ? (
          <div className="min-w-[760px]" dangerouslySetInnerHTML={{ __html: svg }} />
        ) : (
          <p className="text-sm text-muted">Upload a repository to generate a structure-aware architecture diagram.</p>
        )}
      </div>
    </Card>
  );
}
