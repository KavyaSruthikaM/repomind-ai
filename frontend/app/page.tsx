"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { createClient } from "@/lib/supabase/browser";

export default function HomePage() {
  const supabase = createClient();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function signIn() {
    setLoading(true);
    setError("");
    const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (signInError) return setError(signInError.message);
    router.push("/dashboard");
  }

  async function signUp() {
    setLoading(true);
    setError("");
    const { error: signUpError } = await supabase.auth.signUp({ email, password });
    setLoading(false);
    if (signUpError) return setError(signUpError.message);
    router.push("/dashboard");
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <Card className="glass w-full max-w-md space-y-4">
        <h1 className="text-2xl font-semibold">RepoMind AI</h1>
        <p className="text-sm text-muted">Understand any codebase with AI-powered retrieval.</p>
        <input
          className="w-full rounded-lg border bg-background px-3 py-2"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          className="w-full rounded-lg border bg-background px-3 py-2"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
        <div className="flex gap-2">
          <Button onClick={signIn} disabled={loading} className="flex-1">
            {loading ? "Loading..." : "Login"}
          </Button>
          <Button onClick={signUp} disabled={loading} className="flex-1 bg-transparent border border-border">
            Sign Up
          </Button>
        </div>
      </Card>
    </main>
  );
}
