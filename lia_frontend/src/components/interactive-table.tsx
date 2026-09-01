"use client";

import { useEffect, useRef } from "react";
import DataTable from "datatables.net-react";
import DT from "datatables.net-dt";

// DataTables React requires this one-time plugin registration at module scope.
// eslint-disable-next-line react-hooks/rules-of-hooks
DataTable.use(DT);

export type TableColumn<T> = {
  title: string;
  data: string;
  render?: (row: T) => string;
};

export type InteractiveTableProps<T extends { id?: number }> = {
  data: T[];
  columns: TableColumn<T>[];
  onAction?: (action: string, id: number) => void;
};

export function InteractiveTable<T extends { id?: number }>({ data, columns, onAction }: InteractiveTableProps<T>) {
  const wrapper = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = wrapper.current;
    if (!element || !onAction) return;
    const handleClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const button = target.closest<HTMLButtonElement>("button[data-table-action]");
      if (!button) return;
      const id = Number(button.dataset.id);
      if (id) onAction(button.dataset.tableAction ?? "", id);
    };
    element.addEventListener("click", handleClick);
    return () => element.removeEventListener("click", handleClick);
  }, [onAction]);

  const dataTableColumns = columns.map((column) => ({
    title: column.title,
    data: column.data,
    render: column.render
      ? (_value: unknown, _type: unknown, row: T) => column.render?.(row)
      : undefined,
  }));

  return (
    <div ref={wrapper} className="data-table-wrapper overflow-x-auto">
      <DataTable
        data={data}
        columns={dataTableColumns as never}
        className="display compact w-full"
        options={{
          pageLength: 10,
          lengthMenu: [5, 10, 25, 50],
          language: {
            search: "Buscar:",
            lengthMenu: "Mostrar _MENU_ registros",
            info: "Mostrando _START_ a _END_ de _TOTAL_",
            infoEmpty: "Nenhum registro",
            zeroRecords: "Nenhum registro encontrado",
            paginate: { first: "Primeiro", last: "Último", next: "Próximo", previous: "Anterior" },
          },
        }}
      />
    </div>
  );
}
