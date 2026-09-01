"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  CalendarDays,
  ChartNoAxesCombined,
  LayoutDashboard,
  Menu,
  MessageSquareText,
  Scissors,
  Settings,
  Users,
  X,
} from "lucide-react";

const items = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/relatorios", label: "Relatório financeiro", icon: ChartNoAxesCombined },
  { href: "/clientes", label: "Clientes", icon: Users },
  { href: "/agendamentos", label: "Agendamentos", icon: CalendarDays },
  { href: "/calendario", label: "Calendário", icon: CalendarDays },
  { href: "/atendimento", label: "Atendimento", icon: MessageSquareText },
  { href: "/conversas", label: "Conversas WhatsApp", icon: MessageSquareText },
  { href: "/procedimentos", label: "Procedimentos", icon: Scissors },
  { href: "/configuracoes", label: "Configurações", icon: Settings },
  { href: "/operacoes", label: "Operações", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        aria-label={open ? "Recolher menu" : "Expandir menu"}
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        className="fixed left-4 top-4 z-50 inline-flex rounded-xl border border-zinc-700 bg-zinc-900 p-3 text-white shadow-lg transition hover:bg-zinc-800 lg:hidden"
      >
        {open ? <X size={20} /> : <Menu size={20} />}
      </button>

      {open && (
        <button
          type="button"
          aria-label="Fechar menu"
          onClick={() => setOpen(false)}
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
        />
      )}

    <aside className={`fixed inset-y-0 left-0 z-40 flex w-72 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950 p-6 shadow-2xl transition-transform duration-200 lg:static lg:z-auto lg:translate-x-0 lg:shadow-none ${open ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="mb-10 border-b border-white pb-6 text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-fuchsia-400">
          MAYA Admin
        </p>
        <h2 className="mt-2 text-2xl font-semibold capitalize text-white">dashboard</h2>
      </div>

      <nav className="space-y-2">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
                active
                  ? "bg-fuchsia-600/20 text-white"
                  : "text-white hover:bg-zinc-800 hover:text-white"
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
    </>
  );
}
