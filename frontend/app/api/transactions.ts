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

export async function enrichTransactions(transactions: Transaction[]): Promise<string> {
    const response = await fetch('/api/ntropy/enrich', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(transactions),
    });

    if (!response.ok) {
        throw new Error('Failed to start enrichment process');
    }

    const data = await response.json();
    return data.id; // Return the batch ID
}

export function subscribeToEnrichmentStatus(
    batchId: string,
    onProgress: (progress: EnrichmentProgress) => void,
    onComplete: (result: EnrichmentResult) => void,
    onError: (error: EnrichmentError) => void
): () => void {
    const eventSource = new EventSource(`/api/ntropy/enrich/${batchId}/status`);

    eventSource.addEventListener('progress', (event) => {
        const data = JSON.parse(event.data);
        onProgress(data);
    });

    eventSource.addEventListener('complete', (event) => {
        const data = JSON.parse(event.data);
        onComplete(data);
        eventSource.close();
    });

    eventSource.addEventListener('error', (event: Event) => {
        const messageEvent = event as MessageEvent;
        const data = messageEvent.data ? JSON.parse(messageEvent.data) : { error: 'Connection lost' };
        onError(data);
        eventSource.close();
    });

    // Return cleanup function
    return () => {
        eventSource.close();
    };
}
