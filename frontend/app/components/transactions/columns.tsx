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
const coaOptions = coaData.Accounts.map((account) => ({
  value: account.AccountID,
  label: `${account.Code || ""} - ${account.Name}`,
  type: account.Type,
}));

// Get unique account types from CoA data for category options
const classOptions = Array.from(
  new Set(coaData.Accounts.map((account) => account.Type))
)
  .filter(Boolean) // Remove any null/undefined values
  .map((type) => ({
    value: type.toLowerCase(),
    label: type,
  }));

interface ColumnProps {
  onTransactionChange?: (
    transactionId: string,
    field: string,
    value: string
  ) => void;
  pendingChanges: Record<string, Record<string, string>>;
}

export const getColumns = ({
  onTransactionChange,
  pendingChanges,
}: ColumnProps): ColumnDef<Transaction>[] => [
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
    accessorKey: "chart_of_accounts",
    header: "CoA",
    cell: ({ row }) => {
      const transactionId = row.original.id;
      const originalValue = row.getValue("chart_of_accounts") as string;
      const currentValue =
        pendingChanges[transactionId]?.chart_of_accounts || originalValue;
      // Only show AI emoji if the value hasn't been manually changed
      const showAiEmoji =
        !pendingChanges[transactionId]?.chart_of_accounts &&
        row.original.coa_set_by === "AI";

      // Find the matching CoA option to display the code
      const selectedAccount = coaOptions.find(
        (option) => option.value === currentValue
      );

      return (
        <Select
          value={currentValue}
          onValueChange={(value) => {
            onTransactionChange?.(transactionId, "chart_of_accounts", value);
          }}
        >
          <SelectTrigger className="w-fit min-w-[200px] whitespace-nowrap">
            <SelectValue>
              {selectedAccount && (
                <span className="flex items-center flex-start gap-1 w-full pr-2">
                  {showAiEmoji && <span>✨</span>}
                  {selectedAccount.label}
                </span>
              )}
            </SelectValue>
          </SelectTrigger>
          <SelectContent className="min-w-[200px] w-fit">
            {coaOptions.map((option) => (
              <SelectItem
                key={option.value}
                value={option.value}
                className="whitespace-nowrap"
              >
                <span className="flex items-center gap-1 w-full">
                  {currentValue === option.value && showAiEmoji && (
                    <span>✨</span>
                  )}
                  {option.label}
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    },
  },
  {
    accessorKey: "category",
    header: "Class",
    cell: ({ row }) => {
      const transactionId = row.original.id;
      const selectedCoaId = row.getValue("chart_of_accounts") as string;
      
      // Find the corresponding CoA option to get its type
      const selectedCoaOption = coaOptions.find(opt => opt.value === selectedCoaId);
      
      // Use the CoA type as the default category if available
      const defaultClass = selectedCoaOption?.type?.toLowerCase() || '';
      
      const originalValue = row.getValue("category") as string;
      const currentValue = 
        pendingChanges[transactionId]?.category || 
        originalValue || 
        defaultClass;

      const showAiEmoji =
        !pendingChanges[transactionId]?.category &&
        row.original.category_set_by === "AI";

      return (
        <Select
          value={currentValue}
          onValueChange={(value) => {
            onTransactionChange?.(transactionId, "category", value);
          }}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue>
              {currentValue && (
                <span className="flex items-center gap-1">
                  {showAiEmoji && <span>✨</span>}
                  {classOptions.find(opt => opt.value === currentValue)?.label}
                </span>
              )}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {classOptions.map((option) => (
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
    accessorKey: "booking_date",
    header: "Date",
    cell: ({ row }) => {
      const date = row.getValue("booking_date") || row.getValue("created_at"); // Fallback to created_at if booking_date is not available
      return new Date(date as string).toLocaleDateString("en-GB", {
        year: "numeric",
        month: "short",
        day: "numeric",
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
