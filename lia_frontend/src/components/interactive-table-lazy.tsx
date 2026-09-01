"use client";

import dynamic from "next/dynamic";
import type { ReactElement } from "react";
import type { InteractiveTableProps } from "./interactive-table";

const DataTableClient = dynamic(() => import("./interactive-table").then((module) => module.InteractiveTable), { ssr: false }) as unknown as <T extends { id?: number }>(props: InteractiveTableProps<T>) => ReactElement;

export function InteractiveTable<T extends { id?: number }>(props: InteractiveTableProps<T>) {
  return <DataTableClient {...props} />;
}
