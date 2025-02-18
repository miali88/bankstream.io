/* eslint-disable import/no-unresolved */
import { TransactionDataResponse } from "~/types/TransactionDataResponse";
import { buildUrl } from "./config";

export interface Transactions {
  id: string;
  user_id?: string;
  creditor_name?: string;
  debtor_name?: string;
  amount?: number;
  currency?: string;
  remittance_info?: string;
  code?: string;
  created_at: Date;
  institution_id?: string;
  iban?: string;
  transaction_id?: string;
  internal_transaction_id?: string;
  logo?: string;
  category?: string;
  chart_of_account?: string;
}

export type TransactionCreate = Transactions;
export type Transaction = Transactions;

export interface TransactionUpdate {
  id: string;
  category?: string;
  chart_of_account?: string;
  // Add other optional fields that can be updated
}

export interface TransactionBatchUpdate {
  transactions: TransactionUpdate[];
  page?: number;
  pageSize?: number;
}

export interface EnrichmentProgress {
  status: string;
  progress: number;
  total: number;
}

export interface EnrichmentResult {
  status: string;
  results: any; // Replace with proper type from Ntropy response
}

export interface EnrichmentError {
  status?: string;
  error: string;
}

export interface BatchCreateResponse {
  id: string;
  operation: string;
  status: string;
  created_at: string;
  updated_at: string;
  progress: number;
  total: number;
  request_id: string;
}

async function checkEnrichmentStatus(
  token: string,
  batchId: string,
  signal?: AbortSignal
): Promise<{ success: boolean }> {
  const statusUrl = buildUrl(`ntropy/enrich/${batchId}/status`);
  let enrichmentComplete = false;

  while (!enrichmentComplete) {
    const statusResponse = await fetch(statusUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal,
    });

    if (!statusResponse.ok) {
      throw new Error("Failed to check enrichment status");
    }

    const status = await statusResponse.json();

    console.log(status, " HAH HHHHA HH");
    if (status.status === "complete") {
      enrichmentComplete = true;
    } else if (status.status === "error") {
      throw new Error(`Enrichment failed: ${status.error}`);
    } else {
      // Wait before checking again
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }

  return { success: true };
}

export async function getTransactions(
  token: string,
  page: string | number = 1,
  pageSize: string | number = 10,
  signal?: AbortSignal,
  batchId?: string
): Promise<TransactionDataResponse> {
  if (batchId) {
    // Check enrichment status if batchId is provided
    const enrichResult = await checkEnrichmentStatus(token, batchId, signal);
    if (!enrichResult.success) {
      throw new Error("Enrichment status check failed");
    }
    console.log(batchId, "BAtchhh", enrichResult);
  }

  // Then fetch the transactions
  const searchParams = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  const url = buildUrl("transactions", searchParams);

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    signal,
  });

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

  return response.json();
}

export async function startEnrichment(
  token: string,
  signal?: AbortSignal
): Promise<BatchCreateResponse> {
  const enrichUrl = buildUrl("ntropy/enrich");
  const response = await fetch(enrichUrl, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    signal,
  });

  if (!response.ok) {
    throw new Error("Failed to start enrichment process");
  }
  return response.json();
}

export async function downloadTransactionsCsv(token: string): Promise<Blob> {
  const url = buildUrl("transactions/fetch_csv");

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to download transactions CSV");
  }

  return response.blob();
}
