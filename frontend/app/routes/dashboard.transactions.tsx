import { columns } from "../components/transactions/columns";
import { DataTable } from "../components/transactions/data-table";
import { mockTransactions } from "../components/transactions/mock-data";

export default function Transactions() {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Transactions</h2>
      <div className="rounded-lg shadow p-4">
        <DataTable columns={columns} data={mockTransactions} />
      </div>
    </div>
  );
}
