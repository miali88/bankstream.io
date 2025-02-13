/* eslint-disable import/no-unresolved */
import { json, type LoaderFunctionArgs } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { ChartTable } from "~/components/accounts/chart-table";

export async function loader({ request }: LoaderFunctionArgs) {
  const accounts = await import("../../public/CoA.json");
  return json({ accounts: accounts.default.Accounts });
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
      <ChartTable data={accounts} />
    </div>
  );
}
