import { ColumnDef } from "@tanstack/react-table";

import type { Transaction } from "~/routes/dashboard.transactions";

export const columns: ColumnDef<Transaction>[] = [
  {
    accessorKey: "creditor_name",
    header: "Creditor",
    cell: ({ row }) => row.getValue("creditor_name") || "N/A",
  },
  {
    accessorKey: "debtor_name",
    header: "Debtor",
    cell: ({ row }) => row.getValue("debtor_name") || "N/A",
  },
  {
    accessorKey: "amount",
    header: "Amount",
    cell: ({ row }) => {
      const amountInPence = row.getValue("amount") as number;
      const amountInMainUnit = amountInPence / 100; // Convert from pence to pounds/euros/etc
      const currency = row.original.currency;
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: currency,
      }).format(amountInMainUnit);
    },
  },
  {
    accessorKey: "remittance_info",
    header: "Description",
  },
  {
    accessorKey: "code",
    header: "Code",
  },
  {
    accessorKey: "created_at",
    header: "Date",
    cell: ({ row }) => {
      return new Date(row.getValue("created_at")).toLocaleDateString();
    },
  },
];
