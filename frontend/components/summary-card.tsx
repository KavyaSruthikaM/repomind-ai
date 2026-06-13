import type React from "react";

import { Card } from "@/components/ui/card";
import type { ArchitectureAnalysis } from "@/lib/architecture";

type Props = {
  summary: string;
  repositoryName: string;
  architecture?: ArchitectureAnalysis;
};

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">{children}</h3>;
}

export function SummaryCard({ summary, repositoryName, architecture }: Props) {
  return (
    <Card className="glass space-y-4">
      <h2 className="text-lg font-semibold">{repositoryName || "Repository Summary"}</h2>
      <p className="mt-2 whitespace-pre-wrap text-sm text-muted">
        {summary || "No summary yet. Upload a repository and request analysis."}
      </p>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="space-y-2 rounded-lg border border-border p-3">
          <SectionTitle>Detected Directories</SectionTitle>
          <p className="text-xs text-muted">
            {(architecture?.directories || []).slice(0, 12).join(", ") || "No major directories detected yet."}
          </p>
        </div>
        <div className="space-y-2 rounded-lg border border-border p-3">
          <SectionTitle>Major Technologies</SectionTitle>
          <p className="text-xs text-muted">{architecture?.technologies?.join(", ") || "Detecting technologies..."}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="space-y-2 rounded-lg border border-border p-3">
          <SectionTitle>Request/Data Flow</SectionTitle>
          <ul className="space-y-1 text-xs text-muted">
            {(architecture?.request_data_flow || []).slice(0, 6).map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
        <div className="space-y-2 rounded-lg border border-border p-3">
          <SectionTitle>Dependency Relationships</SectionTitle>
          <ul className="space-y-1 text-xs text-muted">
            {(architecture?.dependency_relationships || []).slice(0, 6).map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-2 rounded-lg border border-border p-3">
          <SectionTitle>API Routes</SectionTitle>
          <ul className="space-y-1 text-xs text-muted">
            {(architecture?.api_routes || []).slice(0, 10).map((route) => (
              <li key={route} className="truncate">
                {route}
              </li>
            ))}
          </ul>
        </div>
        <div className="space-y-2 rounded-lg border border-border p-3">
          <SectionTitle>Services</SectionTitle>
          <ul className="space-y-1 text-xs text-muted">
            {(architecture?.services || []).slice(0, 10).map((service) => (
              <li key={service} className="truncate">
                {service}
              </li>
            ))}
          </ul>
        </div>
        <div className="space-y-2 rounded-lg border border-border p-3">
          <SectionTitle>Database Interactions</SectionTitle>
          <ul className="space-y-1 text-xs text-muted">
            {(architecture?.database_interactions || []).slice(0, 6).map((line) => (
              <li key={line}>- {line}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="space-y-2 rounded-lg border border-border p-3">
        <SectionTitle>Key Modules and Responsibilities</SectionTitle>
        <ul className="space-y-1 text-xs text-muted">
          {(architecture?.major_modules || []).map((module) => (
            <li key={module.module}>
              <span className="text-foreground">{module.module}</span>: {module.responsibility}
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}
