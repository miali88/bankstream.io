import logging
from tiktoken import encoding_for_model
import requests
import json
import os
from typing import List, Tuple, Literal, Union
from dotenv import load_dotenv
from enum import Enum
load_dotenv()

# import spacy
from openai import AsyncOpenAI
import voyageai
from app.services.etl.supabase import get_supabase

openai = AsyncOpenAI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

""" CONSIDERING REMOVING SPACY """
# nlp = spacy.load("en_core_web_md")

class JinaTask(str, Enum):
    RETRIEVAL_QUERY = "retrieval.query"
    RETRIEVAL_PASSAGE = "retrieval.passage"
    CLASSIFICATION = "classification"
    TEXT_MATCHING = "text-matching"
    SEPARATION = "separation"

# Type alias for type hinting
JinaTaskType = Literal[
    "retrieval.query",
    "retrieval.passage", 
    "classification",
    "text-matching",
    "separation"
]

def clean_data(data: str) -> str:
    doc = nlp(data)
    cleaned_text = ' '.join(
        [token.text for token in doc if not token.is_space and not token.is_punct]
    )
    return cleaned_text

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    encoder = encoding_for_model(model)
    tokens = encoder.encode(text)
    return len(tokens)

def sliding_window_chunking(text: str, max_window_size: int = 600, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks of specified token size.

    Args:
        text (str): The input text to be chunked
        max_window_size (int, optional): Maximum number of tokens per chunk. Defaults to 600.
        overlap (int, optional): Number of overlapping tokens between chunks. Defaults to 200.

    Returns:
        List[str]: List of text chunks with specified overlap
    """
    encoder = encoding_for_model("gpt-4o")  # Use the same model as in count_tokens
    tokens = encoder.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + max_window_size
        chunk_tokens = tokens[start:end]
        chunk = encoder.decode(chunk_tokens)
        chunks.append(chunk)
        start += max_window_size - overlap
    return chunks

async def insert_chunk(
    parent_id: str, 
    content: str, 
    chunk_index: int, 
    embedding: List[float], 
    user_id: str, 
    token_count: int, 
    title: str,
    source_table: str
) -> None:
    """
    Insert or update a chunk's embeddings in the database.

    Args:
        parent_id (str): ID of the parent document
        content (str): The chunk's text content
        chunk_index (int): Index position of the chunk in the document
        embedding (List[float]): Vector embedding of the chunk
        user_id (str): ID of the user who owns the document
        token_count (int): Number of tokens in the chunk
        title (str): Title of the parent document
        source_table (str): Name of the table containing the parent document

    Raises:
        Exception: If database operation fails
    """
    logger.info(f"Inserting chunk {chunk_index} for document {parent_id}")
    try:
        supabase = await get_supabase()

        # First, check if the chunk exists
        result = await supabase.table('chunks').select('id').eq('parent_id', parent_id).eq('chunk_index', chunk_index).eq('user_id', user_id).execute()
        
        if not result.data:
            # Create new chunk if it doesn't exist
            await supabase.table('chunks').insert({
                'parent_id': parent_id,
                'content': content,
                'chunk_index': chunk_index,
                'voyage_embeddings': embedding,
                'user_id': user_id,
                'token_count': token_count,
                'title': title,
                'source_table': source_table
            }).execute()
            logger.debug(f"Created new chunk {chunk_index}")
        else:
            # Update existing chunk
            chunk_id = result.data[0]['id']
            await supabase.table('chunks').update({
                'voyage_embeddings': embedding,
                'content': content,
                'token_count': token_count
            }).eq('id', chunk_id).execute()
            logger.debug(f"Updated existing chunk {chunk_index}")
            
    except Exception as e:
        logger.error(f"Failed to insert/update chunk {chunk_index}: {str(e)}")
        raise

async def get_embedding(
    text: str,
    task: JinaTaskType = JinaTask.RETRIEVAL_PASSAGE,
) -> list[float]:
    jina_api_key = os.getenv("JINA_API_KEY")
    if not jina_api_key:
        raise ValueError("JINA_API_KEY is not set")
    logger.info("Requesting embedding from Jina AI")
    try:
        url = 'https://api.jina.ai/v1/embeddings'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {jina_api_key}'
        }
        data = {
            "model": "jina-embeddings-v3",
            "task": task,
            "dimensions": 1024,
            "late_chunking": False,
            "embedding_type": "float",
            "input": text
        }
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(data),
            timeout=30  # Add timeout to prevent potential DoS attacks
        )
        response.raise_for_status()
        logger.debug("Successfully received embedding from Jina AI")

        embedding = response.json()['data'][0]['embedding']
        token_count = response.json()['usage']['total_tokens']
        return embedding, token_count
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get embedding from Jina AI: {str(e)}")
        raise

async def get_voyage_embedding(text: str, input_type: Literal["document", "query"]) -> list[float]:
    voyage_api_key = os.getenv("VOYAGE_API_KEY")
    if not voyage_api_key:
        raise ValueError("VOYAGE_API_KEY is not set")
    logger.info("Requesting embedding from Voyage AI")
    try:
        client = voyageai.Client(api_key=voyage_api_key)

        response = client.embed(
            texts=text,
            model="voyage-finance-2",
            input_type=input_type
        )
        return response.embeddings[0]
    except Exception as e:
        logger.error(f"Failed to get embedding from Voyage AI: {str(e)}")
        raise


async def process_item(item_id: str, content: str, user_id: str, title: str, source_table: str) -> int:
    """
    Process a text document by chunking it and generating embeddings.

    Args:
        item_id (str): Unique identifier for the document
        content (str): Full text content of the document
        user_id (str): ID of the user who owns the document
        title (str): Title of the document

    Returns:
        int: Total number of tokens processed

    Raises:
        Exception: If chunk processing fails
    """
    logger.info(f"Processing item {item_id} for user {user_id}")
    chunks = sliding_window_chunking(content)
    logger.info(f"Created {len(chunks)} chunks for processing")
    total_tokens = 0
    for index, chunk in enumerate(chunks):
        logger.debug(f"Processing chunk {index}/{len(chunks)}")
        try:
            # Get embeddings from Voyage AI (no token count)
            embedding = await get_voyage_embedding(text=chunk, input_type="document")
            # Estimate token count using tiktoken (approximate)
            token_count = count_tokens(chunk)
            await insert_chunk(
                item_id,
                chunk,
                index,
                embedding,
                user_id,
                token_count,
                title,
                source_table
            )
            total_tokens += token_count
        except Exception as e:
            logger.error(f"Failed to process chunk {index}: {str(e)}")
            raise
    return total_tokens

async def process_tabular_item(item_id: str, rows: List[dict], user_id: str, title: str, source_table: str) -> int:
    """
    Process tabular data by treating each row as a chunk and generating embeddings.

    Args:
        item_id (str): Unique identifier for the tabular document
        rows (List[dict]): List of dictionaries representing table rows
        user_id (str): ID of the user who owns the document
        title (str): Title of the document

    Returns:
        int: Total number of tokens processed

    Raises:
        Exception: If row processing fails
    """
    logger.info(f"Processing tabular item {item_id} with {len(rows)} rows")
    total_tokens = 0
    
    for index, row in enumerate(rows):
        logger.debug(f"Processing row {index}/{len(rows)}")
        try:
            # Convert row dict to string representation
            row_content = json.dumps(row, ensure_ascii=False)
            
            # Get embedding for the row
            embedding, token_count = await get_embedding(row_content)
            
            # Store in chunks table
            await insert_chunk(
                item_id,
                row_content,
                index,
                embedding,
                user_id,
                token_count,
                title,
                source_table
            )
            total_tokens += token_count
            
        except Exception as e:
            logger.error(f"Failed to process row {index}: {str(e)}")
            raise
    
    return total_tokens


""" ENTRY POINT """
async def kb_item_to_chunks(
    data_id: str, 
    data_content: Union[str, List[dict]], 
    user_id: str, 
    title: str, 
    source_table: str,
    is_tabular: bool = False,
) -> None:
    """
    Process a knowledge base item by chunking it and generating embeddings.
    Handles both text documents and tabular data.

    Args:
        data_id (str): Unique identifier for the document
        data_content (Union[str, List[dict]]): Either full text content or list of table rows
        user_id (str): ID of the user who owns the document
        title (str): Title of the document
        is_tabular (bool, optional): Whether the content is tabular data. Defaults to False.

    Raises:
        Exception: If processing fails
    """
    logger.info(f"Starting knowledge base item processing for ID {data_id}")
    
    try:
        if is_tabular:
            # For tabular data, data_content will be a list of dictionaries
            total_tokens = await process_tabular_item(
                item_id=data_id,
                rows=data_content,
                user_id=user_id,
                title=title,
                source_table=source_table
            )
        else:
            """ removed text processing logic """
            # Existing text processing logic
            # cleaned_text = clean_data(data_content)
            # logger.debug(f"Cleaned text length: {len(cleaned_text)} characters")
            
            # if not cleaned_text:
            #     logger.warning(f"No valid text content for item {title}")
            #     return
                
            total_tokens = await process_item(
                item_id=data_id,
                content=data_content,
                user_id=user_id,
                title=title,
                source_table=source_table
            )
            
        logger.info(f"Successfully processed knowledge base item {title}")
        
    except Exception as e:
        logger.error(f"Failed to process knowledge base item {title}: {str(e)}")
        raise
