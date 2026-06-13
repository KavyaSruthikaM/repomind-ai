import type React from "react";

import { cn } from "@/lib/utils";

type Props = React.HTMLAttributes<HTMLDivElement>;

export function Card({ className, ...props }: Props) {
  return <div className={cn("rounded-lg border border-border bg-card p-4", className)} {...props} />;
}
