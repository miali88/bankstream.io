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
