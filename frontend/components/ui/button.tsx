"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement>;
type ButtonVariant = "solid" | "ghost";

export function Button({ className, variant = "solid", ...props }: ButtonProps & { variant?: ButtonVariant }) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60",
        variant === "solid" && "bg-accent text-white",
        variant === "ghost" && "bg-transparent text-muted",
        className
      )}
      {...props}
    />
  );
}
