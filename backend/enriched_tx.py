from pydantic import BaseModel
from typing import List, Union, Literal
from datetime import datetime
import logging

from extract_invoice_data import InvoiceResults, InvoiceTable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('enriched_tx.log')
    ]
)
logger = logging.getLogger(__name__)


class EmailSchema(BaseModel):
    id: str
    from_email: dict
    to_email: dict
    date: dict
    subject: str
    body: str

class AttachmentTable(BaseModel):
    id: str
    created_at: datetime
    transaction_ids: List[str] = []  # List of transaction IDs this attachment is assigned to
    type: Union[Literal["invoice", "email"]] 
    data: Union[InvoiceTable, EmailSchema]  # The actual attachment data

class InternetSearch(BaseModel):
    query: str
    results: List[dict]

class EnrichedTxTable(BaseModel):
    id: str
    bank_id: str
    amount: int
    currency: str
    date: str
    category: dict 
    entity: dict 
    llm_chart_of_accounts: str
    user_chart_of_accounts: str
    attachment_ids: List[str] #TODO:

"""
# TODO: complete flow:

# entity from ntropy - done
# web search - done (brave_search.py)
# LLM enrich - done (llm_categorise.py)
# invoice attachments - TODO: assign invoices to tx (simi_search_invoices.py). Cnsider entity simi search + amount and date range. Data extraction is (extract_invoice_data.py)
# previous user assigned coa - TODO:
# simi search for coa - done (simi_search_coa.py)
"""


"""
attachments: invoices, receipts, contracts
emails: email correspondence 
"""

# Invoice processing functionality has been moved to extract_invoice_data.py

if __name__ == "__main__":
    logger.info("EnrichedTx module loaded")