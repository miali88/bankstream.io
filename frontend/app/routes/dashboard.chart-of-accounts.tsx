import { json, type LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { DataTable } from "~/components/transactions/data-table";
import { type ColumnDef } from "@tanstack/react-table";

interface ChartOfAccount {
  accountID: string;
  code: string;
  name: string;
  type: string;
  status: string;
  description?: string;
}

const columns: ColumnDef<ChartOfAccount>[] = [
  {
    accessorKey: "code",
    header: "Code",
  },
  {
    accessorKey: "name",
    header: "Name",
  },
  {
    accessorKey: "type",
    header: "Type",
  },
  {
    accessorKey: "status",
    header: "Status",
  },
  {
    accessorKey: "description",
    header: "Description",
  },
];

export async function loader({ request }: LoaderFunctionArgs) {
  const accounts = await import('../../public/CoA.json');
  return json({ accounts: accounts.default });
}

export default function ChartOfAccounts() {
  const { accounts } = useLoaderData<typeof loader>();

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight">Chart of Accounts</h2>
        <p className="text-muted-foreground">
          View and manage your Xero chart of accounts
        </p>
      </div>
      <DataTable columns={columns} data={accounts} />
    </div>
  );
} 