export interface Transaction {
    id: string;
    user_id?: string;
    creditor_name?: string;
    debtor_name?: string;
    amount?: number;
    currency?: string;
    remittance_info?: string;
    code?: string;
    created_at: string;  // ISO date string
}

export interface TransactionDataResponse {
    transactions: Transaction[];
    total_count: number;
    page: number;
    page_size: number;
    total_pages: number;
}