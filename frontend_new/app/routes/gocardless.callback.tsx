import { useEffect, useRef } from "react";
import { useSearchParams } from "@remix-run/react";
import { useAuth } from "@clerk/remix";

export default function GocardlessCallback() {
    const [searchParams] = useSearchParams();
    const { getToken } = useAuth();
    const processedRef = useRef(false);
    
    useEffect(() => {
        async function processCallback() {
            // Prevent duplicate processing
            if (processedRef.current) return;
            processedRef.current = true;

            try {
                const ref = searchParams.get('ref');
                if (!ref) {
                    console.error('No ref parameter found in URL');
                    return;
                }

                const token = await getToken();
                const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/gocardless/callback?ref=${ref}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) {
                    console.error('Failed to process callback on backend');
                }
            } catch (error) {
                console.error('Error processing callback:', error);
                // Reset the ref if there's an error, allowing for retry
                processedRef.current = false;
            }
        }

        processCallback();
    }, [searchParams, getToken]);

    return (
      <div className="flex h-screen items-center justify-center bg-white relative">
        <div className="absolute top-4 left-4">
          <img src="/logo_3.png" alt="BankStream Logo" className="h-32" />
        </div>
        <div className="rounded-lg bg-green-100 p-6 text-center">
          <h2 className="text-xl font-semibold text-green-800">
            Bank data successfully linked
          </h2>
          <p className="text-black">User may now return to the dashboard and close this window</p>
        </div>
      </div>
    );
  } 