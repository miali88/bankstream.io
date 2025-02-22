export interface Transaction {
    id: string;
    currency: string;
    category_set_by?: string;
    coa_set_by?: "AI" | string;
    creditor_name?: string;
    debtor_name?: string;
    amount: number;
    remittance_info?: string;
    chart_of_accounts?: string;
    category?: string;
    created_at: string;  // ISO date string
    booking_date: string; // ISO date string for actual transaction date
    bban?: string;
}

export interface TransactionDataResponse {
    transactions: Transaction[];
    total_count: number;
    page: number;
    page_size: number;
    total_pages: number;
}