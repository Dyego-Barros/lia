import type { Metadata } from "next";
import "./globals.css";
import "datatables.net-dt/css/dataTables.dataTables.css";
import { AuthShell } from "@/components/auth-shell";

export const metadata: Metadata = {
  title: "MAYA Admin",
  description: "Painel administrativo MAYA com IA, WhatsApp e agendamentos",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className="h-full antialiased">
      <body className="min-h-full bg-slate-50 text-slate-900">
        <AuthShell>{children}</AuthShell>
      </body>
    </html>
  );
}
