import { ColumnDef } from "@tanstack/react-table";

export interface Transaction {
  bookingDate: string;
  creditorName: string;
  remittanceInfo: string;
  currency: string;
  amount: number;
  coa_agent: string;
  coa_reason: string;
  coa_confidence: number;
}

export const columns: ColumnDef<Transaction>[] = [
  {
    accessorKey: "bookingDate",
    header: "Booking Date",
  },
  {
    accessorKey: "creditorName",
    header: "Creditor Name",
  },
  {
    accessorKey: "remittanceInfo",
    header: "Remittance Info",
  },
  {
    accessorKey: "currency",
    header: "Currency",
  },
  {
    accessorKey: "amount",
    header: () => {
      return <div className="text-right">Amount</div>;
    },
    cell: ({ row }) => {
      const amount = parseFloat(row.getValue("amount"));
      return <div className="text-right font-medium">{amount.toFixed(2)}</div>;
    },
  },
  {
    accessorKey: "coa_agent",
    header: "COA Agent",
  },
  {
    accessorKey: "coa_reason",
    header: "COA Reason",
  },
  {
    accessorKey: "coa_confidence",
    header: "Confidence",
    cell: ({ row }) => {
      const confidence = parseFloat(row.getValue("coa_confidence"));
      return <div className="text-right">{(confidence * 100).toFixed(1)}%</div>;
    },
  },
];
