"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { TopNavbar } from "@/components/top-navbar";
import { apiGet } from "@/lib/api";

type User = { id: number; nome: string; email: string; role: string };

export function AuthShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname(); const router = useRouter(); const [ready, setReady] = useState(false);
  useEffect(() => { if (pathname === "/login") { Promise.resolve().then(() => setReady(true)); return; } apiGet<User>("/auth/me").then(() => setReady(true)).catch(() => { router.replace("/login"); }); }, [pathname, router]);
  useEffect(() => {
    if (pathname === "/login") return;
    const idleTimeout = 30 * 60 * 1000;
    let timer: number;
    const expireSession = () => {
      void fetch("/api/auth/logout", { method: "POST", credentials: "include" }).finally(() => router.replace("/login"));
    };
    const resetTimer = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(expireSession, idleTimeout);
    };
    const activityEvents = ["pointerdown", "keydown", "scroll", "touchstart"];
    activityEvents.forEach((event) => window.addEventListener(event, resetTimer, { passive: true }));
    resetTimer();
    return () => {
      window.clearTimeout(timer);
      activityEvents.forEach((event) => window.removeEventListener(event, resetTimer));
    };
  }, [pathname, router]);
  if (pathname === "/login") return <>{children}</>;
  if (!ready) return <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-500">Validando sessão...</div>;
  return <div className="flex min-h-screen"><Sidebar /><main className="min-w-0 flex-1 bg-slate-50 p-4 text-slate-900 md:p-8"><TopNavbar />{children}<footer className="mt-10 border-t border-slate-200 py-6 text-center text-xs text-slate-400">© 2026 MAYA Admin. Todos os direitos reservados. Texto provisório para edição futura.</footer></main></div>;
}
