import { columns } from "../components/transactions/columns";
import { DataTable } from "../components/transactions/data-table";
import { mockTransactions } from "../components/transactions/mock-data";
import { BankSelectorDialog } from "../components/bank-selector/bank-selector-dialog";

export default function Transactions() {
  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Transactions</h2>
        <BankSelectorDialog />
      </div>
      <div className="rounded-lg shadow p-4">
        <DataTable columns={columns} data={mockTransactions} />
      </div>
    </div>
  );
}
