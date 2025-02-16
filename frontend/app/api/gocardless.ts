import { buildUrl } from "./config";

export async function getBankList(country: string | null, token: string) {
  if (!country) throw new Error("Country is required");
  
  const searchParams = new URLSearchParams({ country });
  const url = buildUrl("gocardless/bank_list", searchParams);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail || `HTTP error! status: ${response.status}`
    );
  }

  return await response.json();
}

export async function getBuildLink(institutionId: string | null, transactionTotalDays: string | null, token: string) {
  if (!institutionId) throw new Error("Institution ID is required");
  if (!transactionTotalDays) throw new Error("Transaction total days is required");

  const searchParams = new URLSearchParams({ institution_id: institutionId, transaction_total_days: transactionTotalDays });
  const url = buildUrl("gocardless/build_link", searchParams);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

export interface ExpiringAgreement {
  id: string;
  institution_id: string;
  expires_at: string;
  days_until_expiry: number;
}

export async function checkExpiringAgreements(token: string, daysThreshold: number = 7): Promise<ExpiringAgreement[]> {
  const searchParams = new URLSearchParams({ days_threshold: daysThreshold.toString() });
  const url = buildUrl("gocardless/check-expiring", searchParams);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail || `HTTP error! status: ${response.status}`
    );
  }

  return await response.json();
}
