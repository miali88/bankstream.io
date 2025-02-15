/* eslint-disable import/no-unresolved */
import { getColumns } from "../components/transactions/columns";
import { DataTable } from "../components/transactions/data-table";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";
import { AddAccountDialog } from "~/components/transactions/add-account-dialog";
import type { LoaderFunction, ActionFunction } from "@remix-run/node";
import { getBankList, getBuildLink } from "~/api/gocardless";
import { useSearchParams, useLoaderData, useFetcher } from "@remix-run/react";
import { useEffect, useState } from "react";
import { useToast } from "~/components/ui/use-toast";
import { CheckCircle, Save } from "lucide-react";
import { redirect, json } from "@remix-run/node";
import { getAuth } from "@clerk/remix/ssr.server";
import type { Transaction, TransactionDataResponse } from "~/types/TransactionDataResponse";
import { config } from "~/config.server";

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

// Ensure we have an API URL
const API_BASE_URL = config.apiBaseUrl || process.env.VITE_API_BASE_URL || 'http://localhost:8001/api/v1';

export const loader: LoaderFunction = async (args) => {
  const { userId, getToken } = await getAuth(args);

  if (!userId) {
    return redirect("/sign-in");
  }

  const token = await getToken();
  const url = new URL(args.request.url);
  const page = url.searchParams.get("page") || "1";
  const pageSize = url.searchParams.get("pageSize") || "10";

  try {
    const apiUrl = `${API_BASE_URL}/transactions?page=${page}&page_size=${pageSize}`;
    console.log('Fetching transactions from:', apiUrl);
    
    const transactionsResponse = await fetch(
      apiUrl,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!transactionsResponse.ok) {
      const errorText = await transactionsResponse.text();
      console.error("Failed to fetch transactions:", {
        status: transactionsResponse.status,
        statusText: transactionsResponse.statusText,
        error: errorText,
        url: transactionsResponse.url
      });
      throw new Error(`Failed to fetch transactions: ${transactionsResponse.status} ${transactionsResponse.statusText}`);
    }

    const transactionData: TransactionDataResponse = await transactionsResponse.json();
    console.log('Received transaction data:', transactionData);

    // Fetch countries data from API
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
      ...transactionData,
    });
  } catch (error) {
    console.error("Error fetching transactions:", error);
    return json({
      countries: [],
      token,
      transactions: [],
      total_count: 0,
      page: parseInt(page),
      page_size: parseInt(pageSize),
      total_pages: 0,
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

  // Handle transaction updates
  if (formData.get("_action") === "updateTransactions") {
    const updatesJson = formData.get("updates");
    if (!updatesJson || typeof updatesJson !== 'string') {
      throw new Error("No updates provided");
    }

    const updates = JSON.parse(updatesJson);
    
    try {
      // Use the API_BASE_URL constant instead of config.apiBaseUrl
      const updateUrl = `${API_BASE_URL}/transactions/batch`;
      console.log('Attempting to update transactions at:', updateUrl);
      
      const response = await fetch(updateUrl, {
        method: "PATCH",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Failed to update transactions:", {
          status: response.status,
          url: response.url,
          error: errorData
        });
        throw new Error(errorData.detail || "Failed to update transactions");
      }

      const result = await response.json();
      console.log('Update successful:', result);
      return json({ success: true, data: result });
    } catch (error: unknown) {
      console.error("Error updating transactions:", error);
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("Failed to update transactions");
    }
  }

  const countryValue = formData.get("country");
  const bankIdValue = formData.get("bankId");

  try {
    if (countryValue && typeof countryValue === 'string') {
      const bankList = await getBankList(countryValue, token);
      return { bankList };
    }

    if (bankIdValue && typeof bankIdValue === 'string') {
      const transactionTotalDaysValue = formData.get("transactionTotalDays");
      
      if (!transactionTotalDaysValue || typeof transactionTotalDaysValue !== 'string') {
        throw new Error("Missing transaction total days");
      }
      
      const { link, ref } = await getBuildLink(bankIdValue, transactionTotalDaysValue, token);
      return { link, ref };
    }

    throw new Error("Invalid form data provided");
  } catch (error) {
    console.error("Error:", error);
    throw new Error("Failed to process request");
  }
};

export default function Transactions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();
  const { transactions, page, page_size, total_pages, total_count } = useLoaderData<typeof loader>();
  const [globalFilter, setGlobalFilter] = useState("");
  const [pendingChanges, setPendingChanges] = useState<Record<string, Record<string, string>>>({});
  const fetcher = useFetcher();

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
        duration: 3000,
      });
    }
  }, [searchParams, toast]);

  const handleTransactionChange = (transactionId: string, field: string, value: string) => {
    console.log('Transaction Change:', { transactionId, field, value });
    setPendingChanges(prev => {
      const newChanges = {
        ...prev,
        [transactionId]: {
          ...(prev[transactionId] || {}),
          [field]: value,
        },
      };
      console.log('New Pending Changes:', newChanges);
      return newChanges;
    });
  };

  const handleSaveChanges = () => {
    if (Object.keys(pendingChanges).length === 0) {
      toast({
        description: "No changes to save",
        duration: 3000,
      });
      return;
    }

    const updates = Object.entries(pendingChanges).map(([transactionId, changes]) => ({
      id: transactionId,
      ...changes
    }));

    console.log('Sending updates:', {
      transactions: updates,
      page: page || 1,
      pageSize: page_size || 10
    });

    const formData = new FormData();
    formData.append("_action", "updateTransactions");
    formData.append("updates", JSON.stringify({
      transactions: updates,
      page: page || 1,
      pageSize: page_size || 10
    }));

    fetcher.submit(
      formData,
      { method: "patch" }
    );

    // Add response logging
    console.log('Fetcher state:', fetcher.state);
    console.log('Fetcher data:', fetcher.data);

    // Clear pending changes after submission
    setPendingChanges({});

    toast({
      variant: "default",
      className: "bg-white border-green-500",
      description: (
        <div className="flex items-center gap-2 text-green-900">
          <CheckCircle className="h-4 w-4" />
          <span className="text-black">Changes saved successfully</span>
        </div>
      ),
      duration: 3000,
    });
  };

  const handlePageChange = (newPage: number) => {
    setSearchParams(prev => {
      prev.set("page", newPage.toString());
      return prev;
    });
  };

  const columns = getColumns({ 
    onTransactionChange: handleTransactionChange,
    pendingChanges: pendingChanges
  });

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
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              className="bg-green-100 text-black hover:bg-green-200"
              onClick={handleSaveChanges}
              disabled={Object.keys(pendingChanges).length === 0}
            >
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
            <Button variant="outline" className="bg-purple-100 text-black hover:bg-purple-200">
              Auto Reconcile ✨
            </Button>
            <AddAccountDialog />
          </div>
        </div>
        <DataTable
          columns={columns}
          data={transactions}
          globalFilter={globalFilter}
          onGlobalFilterChange={setGlobalFilter}
          pagination={{
            pageIndex: page - 1,
            pageSize: page_size,
            pageCount: total_pages,
            totalRows: total_count,
            onPageChange: handlePageChange,
          }}
        />
      </div>
    </div>
  );
}
