import { ColumnDef } from "@tanstack/react-table";
import type { Transaction } from "~/types/TransactionDataResponse";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";
import coaData from "../../../public/CoA.json";

// Get COA options from the JSON file
const coaOptions = coaData.Accounts.map(account => ({
  value: account.AccountID,
  label: `${account.Code || ''} - ${account.Name}`,
  type: account.Type
}));

// Category options
const categoryOptions = [
  { value: "income", label: "Income" },
  { value: "expense", label: "Expense" },
  { value: "transfer", label: "Transfer" },
  { value: "investment", label: "Investment" },
  { value: "other", label: "Other" }
];

interface ColumnProps {
  onTransactionChange?: (transactionId: string, field: string, value: string) => void;
  pendingChanges: Record<string, Record<string, string>>;
}

export const getColumns = ({ onTransactionChange, pendingChanges }: ColumnProps): ColumnDef<Transaction>[] => [
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
    accessorKey: "chart_of_account",
    header: "CoA",
    cell: ({ row }) => {
      const transactionId = row.original.id;
      const originalValue = row.getValue("chart_of_account") as string;
      const currentValue = pendingChanges[transactionId]?.chart_of_account || originalValue;
      
      // Find the matching CoA option to display the code
      const selectedAccount = coaOptions.find(option => option.value === currentValue);
      
      return (
        <Select 
          value={currentValue}
          onValueChange={(value) => {
            onTransactionChange?.(transactionId, "chart_of_account", value);
          }}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue>
              {selectedAccount ? selectedAccount.label : "Select CoA"}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {coaOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    },
  },
  {
    accessorKey: "category",
    header: "Category",
    cell: ({ row }) => {
      const transactionId = row.original.id;
      const originalValue = row.getValue("category") as string;
      const currentValue = pendingChanges[transactionId]?.category || originalValue;
      
      return (
        <Select 
          value={currentValue}
          onValueChange={(value) => {
            onTransactionChange?.(transactionId, "category", value);
          }}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Select Category" />
          </SelectTrigger>
          <SelectContent>
            {categoryOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    },
  },
  {
    accessorKey: "created_at",
    header: "Date",
    cell: ({ row }) => {
      return new Date(row.getValue("created_at")).toLocaleDateString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    },
  },
  {
    accessorKey: "bban",
    header: "BBAN",
    cell: ({ row }) => row.getValue("bban") || "N/A",
  },
];

// Export a default columns instance for backward compatibility
export const columns = getColumns({ pendingChanges: {} });
