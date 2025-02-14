import { useEffect } from "react";
import { useToast } from "~/components/ui/use-toast";

interface BankLinkSSEListenerProps {
  ref: string;
}

export function BankLinkSSEListener({ ref }: BankLinkSSEListenerProps) {
  const { toast } = useToast();

  useEffect(() => {
    if (!ref) {
      console.log('No ref available, skipping SSE setup');
      return;
    }

    console.log('Setting up SSE connection for ref:', ref);
    const setupEventSource = () => {
      const sseUrl = `${import.meta.env.VITE_API_BASE_URL}/gocardless/sse?ref=${encodeURIComponent(ref)}`;
      console.log('Connecting to SSE endpoint:', sseUrl);
      
      const eventSource = new EventSource(sseUrl);

      eventSource.onopen = () => {
        console.log('SSE connection established successfully');
      };

      eventSource.onmessage = (event) => {
        console.log('Received SSE message:', event.data);
        // Skip processing keepalive messages
        if (event.data.startsWith(': keepalive')) {
          console.log('Received keepalive');
          return;
        }
        
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
        setTimeout(() => {
          console.log('Attempting to reconnect SSE...');
          setupEventSource();
        }, 5000);
      };

      return eventSource;
    };

    const eventSource = setupEventSource();

    return () => {
      console.log('Cleaning up SSE connection');
      eventSource.close();
    };
  }, [ref, toast]);

  return null;
} 