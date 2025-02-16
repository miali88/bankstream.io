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
    bban?: string;
    institution_id?: string;
    iban?: string;
    transaction_id?: string;
    internal_transaction_id?: string;
    logo?: string;
    category?: string;
    chart_of_account?: string;
}

export interface TransactionDataResponse {
    transactions: Transaction[];
    total_count: number;
    page: number;
    page_size: number;
    total_pages: number;
}