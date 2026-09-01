"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter(); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState<string | null>(null); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); try { await apiPost("/auth/login", { email, password }); router.replace("/"); } catch (e) { setError(e instanceof Error ? e.message : "Não foi possível entrar."); } finally { setBusy(false); } }
  return <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6"><form onSubmit={submit} className="w-full max-w-md space-y-5 rounded-2xl border border-slate-200 bg-white p-8 shadow-lg"><div className="text-center"><p className="text-lg font-semibold uppercase tracking-[0.35em] text-fuchsia-700">MAYA Admin</p></div>{error && <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}<input className="field" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="E-mail" /><input className="field" type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Senha" /><button disabled={busy} className="w-full rounded-xl bg-fuchsia-700 px-4 py-3 font-medium text-white disabled:opacity-60">{busy ? "Entrando..." : "Entrar"}</button></form></main>;
}
