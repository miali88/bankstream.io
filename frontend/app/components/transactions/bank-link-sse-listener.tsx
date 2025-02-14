import { useEffect } from "react";
import { useAuth } from "@clerk/remix";
import { useToast } from "~/components/ui/use-toast";

export function BankLinkSSEListener() {
  const { toast } = useToast();
  const { userId, getToken } = useAuth();

  useEffect(() => {
    if (!userId) {
      console.log('No userId available, skipping SSE setup');
      return;
    }

    async function setupSSE() {
      try {
        const token = await getToken();
        if (!token) {
          console.log('No session token available from Clerk, skipping SSE setup');
          return;
        }

        console.log('Setting up SSE connection for user:', userId);
        const setupEventSource = () => {
          const sseUrl = `${import.meta.env.VITE_API_BASE_URL}/gocardless/sse?token=Bearer ${encodeURIComponent(token)}`;
          console.log('Connecting to SSE endpoint:', sseUrl);
          
          const eventSource = new EventSource(sseUrl);

          eventSource.onopen = () => {
            console.log('SSE connection established successfully');
          };

          eventSource.onmessage = (event) => {
            console.log('Received SSE message:', event.data);
            try {
              const data = JSON.parse(event.data);
              if (data.type === 'account_linked') {
                console.log('Processing account_linked notification');
                toast({
                  title: "Success!",
                  description: data.message,
                  variant: "default",
                });
              }
            } catch (error) {
              console.error('Error parsing SSE message:', error);
            }
          };

          eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            eventSource.close();
            
            // Attempt to reconnect after 5 seconds
            setTimeout(async () => {
              if (userId) {
                const newToken = await getToken();
                if (newToken) {
                  console.log('Attempting to reconnect SSE...');
                  setupEventSource();
                } else {
                  console.log('Cannot reconnect SSE - no valid token available');
                }
              } else {
                console.log('Cannot reconnect SSE - no userId available');
              }
            }, 5000);
          };

          return eventSource;
        };

        const eventSource = setupEventSource();

        return () => {
          console.log('Cleaning up SSE connection');
          eventSource.close();
        };
      } catch (error) {
        console.error('Error setting up SSE:', error);
      }
    }

    setupSSE();
  }, [userId, toast, getToken]);

  return null;
} 