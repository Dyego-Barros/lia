"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Boxes,
  CalendarDays,
  ChartNoAxesCombined,
  ChevronDown,
  CreditCard,
  LayoutDashboard,
  ListTodo,
  Menu,
  MessageSquareText,
  Package,
  Scissors,
  Settings,
  Users,
  UsersRound,
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
];

const operationItems = [
  { href: "/operacoes?secao=equipe", label: "Equipe e agenda", icon: UsersRound },
  { href: "/operacoes?secao=pacotes", label: "Pacotes", icon: Package },
  { href: "/operacoes?secao=pagamentos", label: "Pagamentos", icon: CreditCard },
  { href: "/operacoes?secao=estoque", label: "Estoque", icon: Boxes },
  { href: "/operacoes?secao=espera", label: "Lista de espera", icon: ListTodo },
  { href: "/operacoes?secao=usuarios", label: "Usuários", icon: Users },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [operationsOpen, setOperationsOpen] = useState(pathname === "/operacoes");

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
          Mayssa Admin
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
        <div>
          <button
            type="button"
            aria-expanded={operationsOpen}
            aria-controls="operations-submenu"
            onClick={() => setOperationsOpen((current) => !current)}
            className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-white transition hover:bg-zinc-800 ${pathname === "/operacoes" ? "bg-fuchsia-600/20" : ""}`}
          >
            <Settings size={18} />
            <span className="flex-1 text-left">Operações</span>
            <ChevronDown size={16} className={`transition-transform ${operationsOpen ? "rotate-180" : ""}`} />
          </button>
          {operationsOpen && (
            <div id="operations-submenu" className="mt-1 space-y-1 border-l border-zinc-700 pl-3">
              {operationItems.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-zinc-300 transition hover:bg-zinc-800 hover:text-white"
                >
                  <Icon size={16} />
                  {label}
                </Link>
              ))}
            </div>
          )}
        </div>
      </nav>
    </aside>
    </>
  );
}
