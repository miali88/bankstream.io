/* eslint-disable import/no-unresolved */
import { columns } from "../components/transactions/columns";
import { DataTable } from "../components/transactions/data-table";
import { Input } from "~/components/ui/input";
import { AddAccountDialog } from "~/components/transactions/add-account-dialog";
import type { LoaderFunction, ActionFunction } from "@remix-run/node";
import { getBankList, getBuildLink } from "~/api/transactions";
import { useSearchParams, useLoaderData } from "@remix-run/react";
import { useEffect, useState } from "react";
import { useToast } from "~/components/ui/use-toast";
import { CheckCircle } from "lucide-react";
import { redirect, json } from "@remix-run/node";
import { getAuth } from "@clerk/remix/ssr.server";

interface CountryData {
  cca2: string;
  name: { common: string };
  flag: string;
}

const ALLOWED_COUNTRIES: Record<string, string> = {
  AT: "Austria",
  BE: "Belgium",
  BG: "Bulgaria",
  HR: "Croatia",
  CY: "Cyprus",
  CZ: "Czech Republic",
  DK: "Denmark",
  FI: "Finland",
  FR: "France",
  DE: "Germany",
  HU: "Hungary",
  IT: "Italy",
  LU: "Luxembourg",
  MT: "Malta",
  NL: "Netherlands",
  NO: "Norway",
  PL: "Poland",
  PT: "Portugal",
  IE: "Republic of Ireland",
  RO: "Romania",
  SK: "Slovakia",
  SI: "Slovenia",
  ES: "Spain",
  SE: "Sweden",
  GB: "United Kingdom",
};

export interface Transaction {
  id: string;
  user_id: string;
  creditor_name: string | null;
  debtor_name: string | null;
  amount: number;
  currency: string;
  remittance_info: string;
  code: string;
  created_at: string;
}

export const loader: LoaderFunction = async (args) => {
  const { userId, getToken } = await getAuth(args);

  if (!userId) {
    return redirect("/sign-in");
  }

  const token = await getToken();

  try {
    const transactionsResponse = await fetch(
      `${process.env.VITE_API_BASE_URL}/transactions`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!transactionsResponse.ok) {
      throw new Error("Failed to fetch transactions");
    }

    const transactions: Transaction[] = await transactionsResponse.json();

    // Fetch countries data from API (existing code)
    const response = await fetch("https://restcountries.com/v3.1/all");
    const data = await response.json();

    const countries = data
      .filter((country: CountryData) => ALLOWED_COUNTRIES[country.cca2])
      .map((country: CountryData) => ({
        code: country.cca2,
        name: ALLOWED_COUNTRIES[country.cca2],
        flag: country.flag,
      }))
      .sort((a: { name: string }, b: { name: string }) =>
        a.name.localeCompare(b.name)
      );

    return json({
      countries,
      token,
      transactions: transactions || [],
    });
  } catch (error) {
    console.error("Error fetching transactions:", error);
    return json({
      countries: [],
      token,
      transactions: [],
      error: "Failed to fetch transactions",
    });
  }
};

export const action: ActionFunction = async (args) => {
  const { userId, getToken } = await getAuth(args);

  if (!userId) {
    throw new Error("Not authenticated");
  }

  const token = await getToken();
  const { request } = args;
  const formData = await request.formData();
  const countryValue = formData.get("country");
  const bankIdValue = formData.get("bankId");

  try {
    if (countryValue) {
      const bankList = await getBankList(String(countryValue), token);
      return { bankList };
    }

    if (bankIdValue) {
      const { link } = await getBuildLink(String(bankIdValue), token);
      return { link };
    }

    throw new Error("Invalid form data provided");
  } catch (error) {
    console.error("Error:", error);
    throw new Error("Failed to process request");
  }
};

export default function Transactions() {
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const { transactions } = useLoaderData<typeof loader>();
  const [globalFilter, setGlobalFilter] = useState("");

  useEffect(() => {
    if (searchParams.get("trx") === "succeed") {
      toast({
        variant: "default",
        className: "bg-white border-green-500",
        description: (
          <div className="flex items-center gap-2 text-green-900">
            <CheckCircle className="h-4 w-4" />
            <span className="text-black">
              Transaction successfully completed
            </span>
          </div>
        ),
        duration: 3000, // 3 seconds
      });
    }
  }, [searchParams, toast]);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Transactions</h2>
      <div className="rounded-lg shadow p-4">
        <div className="flex items-center justify-between py-4">
          <Input
            placeholder="Search all columns..."
            className="max-w-sm"
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
          />
          <AddAccountDialog />
        </div>
        <DataTable
          columns={columns}
          data={transactions}
          globalFilter={globalFilter}
          onGlobalFilterChange={setGlobalFilter}
        />
      </div>
    </div>
  );
}
