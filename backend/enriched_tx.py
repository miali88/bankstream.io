from pydantic import BaseModel
from typing import List, Union, Literal
from datetime import datetime
from pathlib import Path
import json
import uuid
import base64
from openai import AsyncOpenAI
import pdf2image
import io
import logging
from supabase import create_client, Client
import os
from tqdm import tqdm
import asyncio
from itertools import islice

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('invoice_processing.log')
    ]
)
logger = logging.getLogger(__name__)


class InvoiceResults(BaseModel):
    """Business logic schema for invoice processing"""
    invoice_from: dict
    invoice_to: dict
    date: dict
    amount: dict
    line_items: dict
    payment_terms: str | None = None
    notes: str | None = None
    ai_description: str
    
class InvoiceTable(BaseModel):
    """Database table schema for invoices"""
    id: str
    client_id: str
    results: InvoiceResults 
    created_at: datetime
    updated_at: datetime | None = None
    status: str  

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
# invoice attachments - TODO: assign invoices to tx (simi_search_invoices.py). Cnsider entity simi search + amount and date range. Data extraction is (enriched_tx.py)
# previous user assigned coa - TODO:
# simi search for coa - done (simi_search_coa.py)
"""


"""
attachments: invoices, receipts, contracts
emails: email correspondence 
"""



""" EXTRACTING INVOICE DATA FROM PDF """
async def invoke_llm(base64_image: str, json_schema: dict) -> str:
    """
    Invoke OpenAI's vision model to extract information from an invoice image.
    
    Args:
        base64_image: Base64 encoded image string
        json_schema: JSON schema defining the expected response structure
    
    Returns:
        str: The extracted data as a JSON string
    """
    logger.debug("Initializing OpenAI client")
    client = AsyncOpenAI()

    # Call OpenAI API with function calling
    logger.info("Sending request to OpenAI API")
    response = await client.chat.completions.create(
        model="gpt-4o",  # Updated to correct model name
        messages=[
            {
                "role": "system",
                "content": "You are a precise invoice data extraction assistant. You will first review the content of the invoice and internally understand it, then you will extract the information exactly according to the specified schema."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract the invoice information in JSON format."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        functions=[
            {
                "name": "extract_invoice_data",
                "description": "Extract structured data from invoice",
                "parameters": json_schema
            }
        ],
        function_call={"name": "extract_invoice_data"},
        max_tokens=1500
    )
    logger.info("Received response from OpenAI")
    
    return response.choices[0].message.function_call.arguments

async def save_to_supabase(invoice_data: InvoiceResults, pdf_path: str) -> str:
    """Save the extracted invoice data to Supabase."""
    
    logger.info("Preparing to save invoice data to Supabase")
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Prepare invoice record
    invoice_record = {
        "id": str(uuid.uuid4()),
        "client_id": "b917c3db-759c-4e8f-80b6-9131298e0f37", 
        "results": invoice_data.model_dump(),
        "status": "processed",
        "source_file": "email"
    }
    
    try:
        # Insert into Supabase
        response = supabase.table("invoices").insert(invoice_record).execute()
        logger.info(f"Successfully saved invoice to Supabase with ID: {invoice_record['id']}")
        return invoice_record['id']
    except Exception as e:
        logger.error(f"Failed to save invoice to Supabase: {str(e)}")
        raise

async def process_image_batch(images_batch, json_schema):
    """Process a batch of images concurrently"""
    tasks = []
    for img in images_batch:
        # Convert image to base64
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
        
        # Create task for each image
        tasks.append(invoke_llm(base64_image, json_schema))
    
    # Run all tasks concurrently and return results
    return await asyncio.gather(*tasks, return_exceptions=True)

async def extract_invoice_data(pdf_path: str) -> List[InvoiceResults]:
    """Extract information from all pages of a PDF invoice using OpenAI's vision model."""
    
    logger.info(f"Starting to process PDF: {pdf_path}")
    
    try:
        # Convert PDF to images
        logger.debug(f"Converting PDF to images: {pdf_path}")
        images = pdf2image.convert_from_path(pdf_path)
        logger.info(f"Successfully converted PDF to {len(images)} images")
        
        # Process images in batches of 5
        BATCH_SIZE = 10
        results = []
        
        for i in range(0, len(images), BATCH_SIZE):
            batch = images[i:i + BATCH_SIZE]
            logger.info(f"Processing batch {i//BATCH_SIZE + 1} of {(len(images) + BATCH_SIZE - 1)//BATCH_SIZE}")
            
            # Define the JSON schema (same as before)
            json_schema = {
                "type": "object",
                "properties": {
                    "invoice_from": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {"type": "string"},
                            "tax_id": {"type": "string"},
                            # Additional optional fields
                            "email": {"type": "string"},
                            "phone": {"type": "string"},
                            "website": {"type": "string"},
                            "registration_number": {"type": "string"},
                            "vat_number": {"type": "string"}
                        },
                        "required": ["name", "address"]  # Only these are required
                    },
                    "invoice_to": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {"type": "string"},
                            "tax_id": {"type": "string"},
                            # Additional optional fields
                            "email": {"type": "string"},
                            "phone": {"type": "string"},
                            "reference": {"type": "string"},
                            "department": {"type": "string"}
                        },
                        "required": ["name", "address"]
                    },
                    "date": {
                        "type": "object",
                        "properties": {
                            "issue_date": {"type": "string"},
                            "due_date": {"type": "string"},
                            "payment_due_by": {"type": "string"},  # Explicit field for AP tracking
                            # Additional optional fields
                            "delivery_date": {"type": "string"},
                            "service_period_start": {"type": "string"},
                            "service_period_end": {"type": "string"},
                            "payment_status": {  # Additional metadata for AP
                                "type": "string",
                                "enum": ["pending", "overdue", "paid", "partially_paid"]
                            },
                        },
                        "required": ["issue_date"]
                    },
                    "amount": {
                        "type": "object",
                        "properties": {
                            "subtotal": {"type": "string"},
                            "tax": {
                                "type": "object",
                                "properties": {
                                    "rate": {"type": "string"},
                                    "amount": {"type": "string"}
                                }
                            },
                            "shipping": {"type": "string"},
                            "discounts": {"type": "string"},
                            "total": {"type": "string"},
                            "currency": {"type": "string"}
                        }
                    },
                    "line_items": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "description": {"type": "string"},
                                        "quantity": {"type": "number"},
                                        "unit_price": {"type": "string"},
                                        "vat_rate": {"type": "string"},
                                        "total": {"type": "string"},
                                        # Additional optional fields
                                        "sku": {"type": "string"},
                                        "unit": {"type": "string"},
                                        "discount": {"type": "string"},
                                        "category": {"type": "string"}
                                    },
                                    "required": ["description", "quantity", "total"]
                                }
                            }
                        }
                    },
                    "payment_terms": {"type": "string"},
                    "notes": {"type": "string"},
                    "ai_description": {"type": "string"}
                },
                "required": ["invoice_from", "invoice_to", "date", "amount", "line_items", "ai_description"]
            }
            
            # Process batch
            batch_results = await process_image_batch(batch, json_schema)
            
            # Parse results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error processing page: {str(result)}")
                    continue
                try:
                    parsed_result = InvoiceResults(**json.loads(result))
                    results.append(parsed_result)
                except Exception as e:
                    logger.error(f"Error parsing result: {str(e)}")
        
        return results
            
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}")
        raise

async def main():
    """Process invoices from the invoices folder, starting after the first three."""
    
    logger.info("Starting invoice processing")
    
    # Get the path to the invoices folder
    invoice_folder = Path("invoices")
    
    if not invoice_folder.exists():
        logger.error("Invoices folder not found")
        raise FileNotFoundError("Invoices folder not found")
    
    # Get list of PDF files, starting after the first three
    pdf_files = sorted(list(invoice_folder.glob("*.pdf")))
    start_index = 3  # Skip the first three files
    pdf_files = pdf_files[start_index:]
    
    total_pdfs = len(pdf_files)
    logger.info(f"Found {total_pdfs} PDF files to process")
    
    if not pdf_files:
        logger.warning("No PDF files found to process after the first three")
        return
    
    processed_invoices = []
    
    # Create progress bar
    with tqdm(total=total_pdfs, desc="Processing PDFs") as pbar:
        # Process each PDF file
        for pdf_file in pdf_files:
            try:
                logger.info(f"Processing file: {pdf_file.name}")
                invoice_data_list = await extract_invoice_data(str(pdf_file))
                
                # Save each page result to Supabase
                for invoice_data in invoice_data_list:
                    invoice_id = await save_to_supabase(invoice_data, str(pdf_file))
                    processed_invoices.append((pdf_file.name, invoice_data, invoice_id))
                
                logger.info(f"Successfully processed: {pdf_file.name}")
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {str(e)}")
            finally:
                pbar.update(1)
    
    # Output results with detailed summaries
    logger.info(f"\nProcessed {len(processed_invoices)} pages successfully")
    print("\n=== Invoice Processing Results ===")
    for filename, invoice, invoice_id in processed_invoices:
        print(f"File: {filename}")
        print(f"Invoice ID: {invoice_id}")
        print(f"From: {invoice.invoice_from.get('name', 'N/A')}")
        print(f"Amount: {invoice.amount.get('total', 'N/A')} {invoice.amount.get('currency', '')}")
        print("\nAI Description:")
        print(invoice.ai_description)
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())