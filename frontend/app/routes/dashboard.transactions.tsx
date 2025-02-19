/* eslint-disable import/no-unresolved */
import { getColumns } from "../components/transactions/columns";
import { DataTable } from "../components/transactions/data-table";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";
import { AddAccountDialog } from "~/components/transactions/add-account-dialog";
import { ExpiringAgreementsNotification } from "~/components/ExpiringAgreementsNotification";
import type { LoaderFunction, ActionFunction } from "@remix-run/node";
import { getBankList, getBuildLink } from "~/api/gocardless";
import {
  useSearchParams,
  useLoaderData,
  useFetcher,
  useActionData,
  useSubmit,
  useNavigation,
} from "@remix-run/react";
import { useEffect, useState } from "react";
import { useToast } from "~/components/ui/use-toast";
import { CheckCircle, Save, Download } from "lucide-react";
import { redirect, json } from "@remix-run/node";
import { getAuth } from "@clerk/remix/ssr.server";
import type {
  Transaction,
  TransactionDataResponse,
} from "~/types/TransactionDataResponse";
import { config } from "~/config.server";
import { getTransactions, startEnrichment } from "~/api/transactions";
import { buildUrl } from "~/api/config";
import type { ActionData } from "@remix-run/node";

const API_BASE_URL = config.apiBaseUrl;

interface CountryData {
  cca2: string;
  name: { common: string };
  flag: string;
}

const ALLOWED_COUNTRIES: Record<string, string> = {
  GB: "United Kingdom",
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
};

export const loader: LoaderFunction = async (args) => {
  const { userId, getToken } = await getAuth(args);

  if (!userId) {
    return redirect("/sign-in");
  }

  const token = await getToken();
  const url = new URL(args.request.url);
  const page = url.searchParams.get("page") || "1";
  const pageSize = url.searchParams.get("pageSize") || "10";
  const batchId = url.searchParams.get("batch_id");

  try {
    const transactionData = await getTransactions(
      token as string,
      page,
      pageSize,
      args.request.signal,
      batchId || undefined
    );

    console.log(transactionData, "HAHHH HH");
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

    return {
      countries,
      token,
      ...transactionData,
    };
  } catch (error) {
    console.error("Error fetching transactions:", error);
    return {
      countries: [],
      token,
      transactions: [],
      total_count: 0,
      page: parseInt(page),
      page_size: parseInt(pageSize),
      total_pages: 0,
      error: "Failed to fetch transactions",
    };
  }
};

interface EnrichActionData {
  batchId?: string;
  bankList?: any;
  link?: string;
  ref?: string;
  success?: boolean;
  data?: any;
}

export const action: ActionFunction = async (args): Promise<Response> => {
  const { userId, getToken } = await getAuth(args);

  if (!userId) {
    throw new Error("Not authenticated");
  }

  const token = await getToken();
  const { request } = args;
  const formData = await request.formData();
  const action = formData.get("_action");

  if (action === "enrich") {
    try {
      const enrichResponse = await startEnrichment(token as string);
      return json<EnrichActionData>({ batchId: enrichResponse.id });
    } catch (error) {
      console.error("Enrichment error:", error);
      throw new Error("Failed to start enrichment process");
    }
  }

  // Handle transaction updates
  if (action === "updateTransactions") {
    const updatesJson = formData.get("updates");
    if (!updatesJson || typeof updatesJson !== "string") {
      throw new Error("No updates provided");
    }

    const updates = JSON.parse(updatesJson);

    try {
      // Use the API_BASE_URL constant instead of config.apiBaseUrl
      const updateUrl = `${API_BASE_URL}/transactions/batch`;
      console.log("Attempting to update transactions at:", updateUrl);

      const response = await fetch(updateUrl, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Failed to update transactions:", {
          status: response.status,
          url: response.url,
          error: errorData,
        });
        throw new Error(errorData.detail || "Failed to update transactions");
      }

      const result = await response.json();
      console.log("Update successful:", result);
      return json<EnrichActionData>({ success: true, data: result });
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
    if (countryValue && typeof countryValue === "string") {
      const bankList = await getBankList(countryValue, token);
      return json<EnrichActionData>({ bankList });
    }

    if (bankIdValue && typeof bankIdValue === "string") {
      const transactionTotalDaysValue = formData.get("transactionTotalDays");

      if (
        !transactionTotalDaysValue ||
        typeof transactionTotalDaysValue !== "string"
      ) {
        throw new Error("Missing transaction total days");
      }

      const { link, ref } = await getBuildLink(
        bankIdValue,
        transactionTotalDaysValue,
        token as string
      );
      return json<EnrichActionData>({ link, ref });
    }

    // Default response if no conditions are met
    return json<EnrichActionData>({});
  } catch (error) {
    console.error("Error:", error);
    throw new Error("Failed to process request");
  }
};

export default function Transactions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();
  const { transactions, page, page_size, total_pages, total_count } =
    useLoaderData<typeof loader>();
  const [globalFilter, setGlobalFilter] = useState("");
  const [pendingChanges, setPendingChanges] = useState<
    Record<string, Record<string, string>>
  >({});
  const submit = useSubmit();
  const navigation = useNavigation();
  const actionData = useActionData<EnrichActionData>();
  const csvFetcher = useFetcher();
  const loaderData = useLoaderData<typeof loader>();

  console.log("Loader Data:", loaderData);

  console.log(actionData, "KK AKKK");

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

  useEffect(() => {
    if (actionData && actionData.batchId) {
      setSearchParams((prev) => {
        prev.set("batch_id", actionData.batchId!);
        return prev;
      });
    }
  }, [actionData, setSearchParams]);

  const handleTransactionChange = (
    transactionId: string,
    field: string,
    value: string
  ) => {
    console.log("Transaction Change:", { transactionId, field, value });
    setPendingChanges((prev) => {
      const newChanges = {
        ...prev,
        [transactionId]: {
          ...(prev[transactionId] || {}),
          [field]: value,
        },
      };
      console.log("New Pending Changes:", newChanges);
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

    const updates = Object.entries(pendingChanges).map(
      ([transactionId, changes]) => ({
        id: transactionId,
        ...changes,
      })
    );

    console.log("Sending updates:", {
      transactions: updates,
      page: page || 1,
      pageSize: page_size || 10,
    });

    const formData = new FormData();
    formData.append("_action", "updateTransactions");
    formData.append(
      "updates",
      JSON.stringify({
        transactions: updates,
        page: page || 1,
        pageSize: page_size || 10,
      })
    );

    submit(formData, { method: "patch" });

    // Add response logging
    console.log("Submit state:", submit.state);
    console.log("Submit data:", submit.data);

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
    setSearchParams((prev) => {
      prev.set("page", newPage.toString());
      return prev;
    });
  };

  const handleEnrichClick = () => {
    const formData = new FormData();
    formData.append("_action", "enrich");
    submit(formData, {
      method: "post",
      action: "/dashboard/transactions",
    });
  };

  const handleDownloadCsv = () => {
    csvFetcher.load("/resources/download-transactions");
  };

  const columns = getColumns({
    onTransactionChange: handleTransactionChange,
    pendingChanges: pendingChanges,
  });

  const isSubmitting = navigation.state === "submitting";

  useEffect(() => {
    if (csvFetcher.data && csvFetcher.state === "idle") {
      const date = new Date().toISOString().split("T")[0];
      const blob = new Blob([csvFetcher.data.csvData], {
        type: csvFetcher.data.contentType,
      });
      const dataUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = dataUrl;
      anchor.download = `transactions-${date}.csv`;
      anchor.click();
      URL.revokeObjectURL(dataUrl);
    }
  }, [csvFetcher.data, csvFetcher.state]);

  return (
    <div className="container mx-auto py-10">
      <ExpiringAgreementsNotification />
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
            <Button
              variant="outline"
              className="bg-purple-100 text-black hover:bg-purple-200"
              onClick={handleEnrichClick}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Loading..." : "AI Reconcile✨"}
            </Button>
            <AddAccountDialog />

            <Button
              variant="outline"
              className="bg-blue-100 text-black hover:bg-blue-200"
              onClick={handleDownloadCsv}
              disabled={csvFetcher.state === "loading"}
            >
              <Download className="w-4 h-4 mr-2" />
              {csvFetcher.state === "loading"
                ? "Downloading..."
                : "export as CSV"}
            </Button>
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
