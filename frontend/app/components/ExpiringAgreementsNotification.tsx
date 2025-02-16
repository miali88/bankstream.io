import { useEffect, useState } from "react";
import { useAuth } from "@clerk/remix";
import { checkExpiringAgreements, type ExpiringAgreement } from "~/api/gocardless";
import { Alert, AlertTitle, AlertDescription } from "~/components/ui/alert";
import { Button } from "~/components/ui/button";
import { RefreshCw } from "lucide-react";

export function ExpiringAgreementsNotification() {
  const { getToken } = useAuth();
  const [expiringAgreements, setExpiringAgreements] = useState<ExpiringAgreement[]>([]);
  const [loading, setLoading] = useState(false);

  const checkAgreements = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;

      const agreements = await checkExpiringAgreements(token);
      setExpiringAgreements(agreements);
    } catch (error) {
      console.error("Failed to check expiring agreements:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAgreements();
    // Check every hour
    const interval = setInterval(checkAgreements, 60 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (expiringAgreements.length === 0) return null;

  return (
    <div className="space-y-4">
      {expiringAgreements.map((agreement) => (
        <Alert key={agreement.id} variant="warning" className="bg-yellow-50">
          <AlertTitle className="text-yellow-800 flex items-center justify-between">
            Bank Connection Expiring
            <Button
              variant="ghost"
              size="sm"
              onClick={checkAgreements}
              disabled={loading}
              className="h-6 w-6 p-0"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </Button>
          </AlertTitle>
          <AlertDescription className="text-yellow-700">
            Your connection to {agreement.institution_id.replace(/_/g, " ")} will expire in{" "}
            {agreement.days_until_expiry} days. Please reconnect your bank account to ensure
            uninterrupted access to your transaction data.
          </AlertDescription>
        </Alert>
      ))}
    </div>
  );
} 