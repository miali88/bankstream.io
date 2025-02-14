import { useEffect, useRef } from "react";
import { useSearchParams } from "@remix-run/react";

export default function GocardlessCallback() {
    const [searchParams] = useSearchParams();
    const processedRef = useRef(false);
    
    useEffect(() => {
        async function processCallback() {
            if (processedRef.current) return;
            
            try {
                const ref = searchParams.get('ref');
                if (!ref) {
                    console.error('No ref parameter found in URL');
                    return;
                }

                const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/gocardless/callback?ref=${ref}`, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                    },
                });

                if (!response.ok) {
                    const errorData = await response.text();
                    console.error('Failed to process callback:', response.status, errorData);
                    return;
                }

                processedRef.current = true;
            } catch (error) {
                console.error('Error processing callback:', error);
                processedRef.current = false;
            }
        }

        processCallback();
    }, [searchParams]);

    return (
      <div className="flex h-screen items-center justify-center bg-white relative">
        <div className="absolute top-4 left-4">
          <img src="/logo_3.png" alt="BankStream Logo" className="h-32" />
        </div>
        <div className="rounded-lg bg-green-100 p-6 text-center">
          <h2 className="text-xl font-semibold text-green-800">
            Bank data successfully linked
          </h2>
          <p className="text-black">You may now close this window and return to your dashboard</p>
        </div>
      </div>
    );
} 