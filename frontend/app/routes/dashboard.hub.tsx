import TransactionChart from '~/components/hub/chart';
import { json, redirect } from '@remix-run/node';
import { useLoaderData, useSearchParams } from '@remix-run/react';
import type { LoaderFunction } from '@remix-run/node';
import { getAuth } from "@clerk/remix/ssr.server";
import type { TransactionDataResponse } from '~/types/TransactionDataResponse';

// Mark this route as client-only
export const handle = { hydrate: true };

export const loader: LoaderFunction = async (args) => {
  const { userId, getToken } = await getAuth(args);
  const url = new URL(args.request.url);
  const page = parseInt(url.searchParams.get('page') || '1', 10);
  const page_size = parseInt(url.searchParams.get('page_size') || '100', 10); // Default to 100 for chart data

  if (!userId) {
    return redirect("/sign-in");
  }

  const token = await getToken();

  try {
    // Ensure trailing slash and handle redirects
    const apiUrl = `${process.env.VITE_API_BASE_URL}/transactions/`;
    console.log('Fetching transactions from:', apiUrl);

    const response = await fetch(
      `${apiUrl}?page=${page}&page_size=${page_size}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        redirect: 'follow', // Explicitly follow redirects
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Failed to fetch transactions:", {
        status: response.status,
        statusText: response.statusText,
        error: errorText,
        url: response.url
      });
      throw new Error(`Failed to fetch transactions: ${response.status} ${response.statusText}`);
    }

    const data: TransactionDataResponse = await response.json();
    console.log('Received transaction data:', {
      count: data.transactions?.length,
      totalCount: data.total_count,
      page: data.page,
      totalPages: data.total_pages
    });
    
    if (!data.transactions || !Array.isArray(data.transactions)) {
      console.error("Invalid transaction data format:", data);
      throw new Error("Invalid transaction data format");
    }

    return json({ 
      data,
      page,
      page_size 
    });
  } catch (error) {
    console.error("Error fetching transactions:", error);
    return json({ 
      data: { 
        transactions: [], 
        total_count: 0, 
        page: page, 
        page_size: page_size, 
        total_pages: 0 
      },
      error: error instanceof Error ? error.message : "Failed to fetch transactions" 
    });
  }
};

export default function Charts() {
  const { data, error } = useLoaderData<typeof loader>();
  const [searchParams] = useSearchParams();
  
  console.log('Rendering chart with data:', {
    hasData: data?.transactions?.length > 0,
    error
  });
  
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Financial Hub</h2>
      <div className="bg-white rounded-lg shadow p-4">
        {error ? (
          <div className="text-red-500 p-4 text-center">
            {error}
          </div>
        ) : data.transactions.length === 0 ? (
          <div className="text-gray-500 p-4 text-center">
            No transaction data available
          </div>
        ) : (
          <TransactionChart data={data} />
        )}
      </div>
    </div>
  );
}
