import TransactionChart from '~/components/hub/chart';
import { json, redirect } from '@remix-run/node';
import { useLoaderData } from '@remix-run/react';
import type { LoaderFunction } from '@remix-run/node';
import { getAuth } from "@clerk/remix/ssr.server";
import type { TransactionDataResponse } from '~/types/TransactionDataResponse';

// Mark this route as client-only
export const handle = { hydrate: true };

export const loader: LoaderFunction = async (args) => {
  const { userId, getToken } = await getAuth(args);

  if (!userId) {
    return redirect("/sign-in");
  }

  const token = await getToken();

  try {
    const response = await fetch(
      `${process.env.VITE_API_BASE_URL}/transactions`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error("Failed to fetch transactions");
    }

    const data: TransactionDataResponse = await response.json();
    return json({ data });
  } catch (error) {
    console.error("Error fetching transactions:", error);
    return json({ 
      data: { transactions: [], total_count: 0, page: 1, page_size: 10, total_pages: 0 },
      error: "Failed to fetch transactions" 
    });
  }
};

export default function Charts() {
  const { data } = useLoaderData<typeof loader>();
  
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Financial Hub</h2>
      <div className="bg-white rounded-lg shadow p-4">
        <TransactionChart data={data} />
      </div>
    </div>
  );
}
