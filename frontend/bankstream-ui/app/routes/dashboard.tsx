import { getAuth } from "@clerk/remix/ssr.server";
import { useLoaderData } from "@remix-run/react";
import { useUser } from "@clerk/remix";
import { useState } from "react";
import axios from "axios";

interface LoaderData {
  banks: Array<{
    id: string;
    name: string;
    logo_url: string;
  }>;
  error?: string;
}

// Protect this route - redirect to sign-in if not authenticated
export async function loader(args: { 
  request: Request; 
  params: Record<string, string | undefined>;
  context: any;
}) {
  const { userId } = await getAuth(args);
  if (!userId) {
    return new Response(null, {
      status: 302,
      headers: {
        Location: "/sign-in",
      },
    });
  }

  try {
    const response = await axios.get(`${process.env.BASE_API_URL}/gocardless/bank_list`);
    return new Response(JSON.stringify({ banks: response.data }), {
      headers: {
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    console.error('Error fetching banks:', error);
    return new Response(JSON.stringify({ banks: [], error: 'Failed to fetch banks' }), {
      headers: {
        "Content-Type": "application/json",
      },
    });
  }
}

export default function Dashboard() {
  const { user } = useUser();
  const { banks, error } = useLoaderData<LoaderData>();
  const [selectedBank, setSelectedBank] = useState<string | null>(null);

  const handleBankSelect = async (bankId: string) => {
    try {
      const response = await axios.post(`${process.env.BASE_API_URL}/gocardless/create_link`, {
        bank_id: bankId,
        user_id: user?.id
      });
      // Redirect to the bank's authentication page
      window.location.href = response.data.link;
    } catch (error) {
      console.error('Error creating bank link:', error);
    }
  };

  return (
    <div className="py-10">
      <header>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold leading-tight tracking-tight text-gray-900">
            Dashboard
          </h1>
        </div>
      </header>
      <main>
        <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
          <div className="px-4 py-8 sm:px-0">
            <div className="rounded-lg border-4 border-dashed border-gray-200 p-4">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {/* Welcome Card */}
                <div className="rounded-lg bg-white p-6 shadow">
                  <h2 className="text-lg font-medium text-gray-900">Welcome, {user?.firstName || 'User'}!</h2>
                  <p className="mt-1 text-sm text-gray-500">Manage your banking in one place</p>
                </div>

                {/* Bank Connection Card */}
                <div className="rounded-lg bg-white p-6 shadow col-span-2">
                  <h2 className="text-lg font-medium text-gray-900">Connect a Bank</h2>
                  {error ? (
                    <p className="mt-2 text-sm text-red-600">{error}</p>
                  ) : (
                    <div className="mt-4 grid grid-cols-2 gap-4">
                      {banks.map((bank) => (
                        <button
                          key={bank.id}
                          onClick={() => handleBankSelect(bank.id)}
                          className={`flex items-center justify-center p-4 rounded-lg border-2 ${
                            selectedBank === bank.id
                              ? 'border-indigo-600 bg-indigo-50'
                              : 'border-gray-200 hover:border-indigo-400'
                          }`}
                        >
                          <div className="text-center">
                            <img
                              src={bank.logo_url}
                              alt={bank.name}
                              className="h-12 w-12 mx-auto mb-2"
                            />
                            <span className="text-sm font-medium text-gray-900">
                              {bank.name}
                            </span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Connected Banks Card */}
                <div className="rounded-lg bg-white p-6 shadow col-span-3">
                  <h2 className="text-lg font-medium text-gray-900">Connected Banks</h2>
                  <p className="mt-1 text-sm text-gray-500">
                    Your connected bank accounts will appear here
                  </p>
                  {/* We'll add the connected banks list in the next iteration */}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 