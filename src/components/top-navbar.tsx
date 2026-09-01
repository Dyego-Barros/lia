"use client";

import { useEffect, useState } from "react";
import { Bell, CircleUserRound, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";

type User = { nome: string; email: string; role: string };

export function TopNavbar() {
  const router = useRouter(); const [user, setUser] = useState<User | null>(null);
  useEffect(() => { apiGet<User>("/auth/me").then(setUser).catch(() => undefined); }, []);
  async function logout() { await apiPost("/auth/logout").catch(() => undefined); router.replace("/login"); }
  return <header className="mb-6 flex items-center justify-between border-b border-slate-200 pb-5"><div className="pl-14 lg:pl-0"><p className="text-sm text-slate-500">Painel administrativo</p></div><div className="flex items-center gap-4"><button title="Notificações" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><Bell size={18} /></button><div className="hidden h-8 w-px bg-slate-200 sm:block" /><button onClick={logout} title="Sair" aria-label="Sair" className="flex items-center gap-3 text-left"><CircleUserRound className="text-fuchsia-700" size={34} /><span className="hidden sm:block"><span className="block text-sm font-semibold text-slate-900">{user?.nome ?? "Usuário"}</span><span className="block text-xs text-slate-500">{user ? `${user.role} · ${user.email}` : "Carregando sessão..."}</span></span><LogOut size={18} className="text-slate-500" /></button></div></header>;
}
