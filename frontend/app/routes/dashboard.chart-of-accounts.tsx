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
  const BASE_API_URL = process.env.BASE_API_URL;
  if (!BASE_API_URL) {
    throw new Error("API_BASE_URL is not defined");
  }

  const response = await fetch(`${BASE_API_URL}/xero/chart_of_accounts`);
  if (!response.ok) {
    throw new Error("Failed to fetch chart of accounts");
  }

  const data = await response.json();
  return json({ accounts: data });
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