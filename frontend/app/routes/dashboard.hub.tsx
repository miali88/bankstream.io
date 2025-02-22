import TransactionChart from "~/components/hub/chart";
import Insights from "~/components/hub/insights";
import { json, redirect } from "@remix-run/node";
import { useLoaderData, useSearchParams } from "@remix-run/react";
import type { LoaderFunction } from "@remix-run/node";
import { getAuth } from "@clerk/remix/ssr.server";
import type { TransactionDataResponse } from "~/types/TransactionDataResponse";
import { config } from "~/config.server";
import { fetchInsights, type InsightData } from "~/api/transactions";

// Mark this route as client-only
export const handle = { hydrate: true };

export const loader: LoaderFunction = async (args) => {
  const { userId, getToken } = await getAuth(args);
  const url = new URL(args.request.url);
  const page = parseInt(url.searchParams.get("page") || "1", 10);
  const page_size = parseInt(url.searchParams.get("page_size") || "100", 10);

  if (!userId) {
    return redirect("/sign-in");
  }

  const token = await getToken();
  let transactionData = null;
  let insightData = null;
  let error = null;

  try {
    // Fetch transactions
    const apiUrl = `${config.apiBaseUrl}/transactions/`;
    console.log("Fetching transactions from:", apiUrl);

    const response = await fetch(
      `${apiUrl}?page=${page}&page_size=${page_size}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        redirect: "follow",
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Failed to fetch transactions:", {
        status: response.status,
        statusText: response.statusText,
        error: errorText,
        url: response.url,
      });
      throw new Error(
        `Failed to fetch transactions: ${response.status} ${response.statusText}`
      );
    }

    transactionData = await response.json();
    
    // Fetch insights
    insightData = await fetchInsights(token);

  } catch (err) {
    console.error("Error fetching data:", err);
    error = err instanceof Error ? err.message : "Failed to fetch data";
    
    // Set default empty data structures
    transactionData = {
      transactions: [],
      total_count: 0,
      page: page,
      page_size: page_size,
      total_pages: 0,
    };
    insightData = {
      spending_by_category: [],
      spending_by_entity: [],
    };
  }

  return json({
    data: transactionData,
    insights: insightData,
    error,
    page,
    page_size,
  });
};

export default function Charts() {
  const { data, insights, error } = useLoaderData<typeof loader>();
  const [searchParams] = useSearchParams();

  console.log("Rendering hub with data:", {
    hasTransactionData: data?.transactions?.length > 0,
    hasInsightData: insights != null,
    error,
  });

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold mb-4">Financial Hub</h2>

      {/* Chart Section */}
      <div className="bg-white rounded-lg shadow p-4">
        {error ? (
          <div className="text-red-500 p-4 text-center">{error}</div>
        ) : data.transactions.length === 0 ? (
          <div className="text-gray-500 p-4 text-center">
            No transaction data available
          </div>
        ) : (
          <TransactionChart data={data} />
        )}
      </div>

      
      {/* Insights Section */}
      {insights && (
        <div className="mb-8">
          <Insights data={insights} />
        </div>
      )}

    </div>
  );
}
