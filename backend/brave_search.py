import asyncio
import aiohttp
import os
import time
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Pydantic models to structure the response
class QueryInfo(BaseModel):
    original: str
    is_navigational: bool = False
    is_news_breaking: bool = False
    country: str = "us"
    more_results_available: bool = True

class Profile(BaseModel):
    name: str
    url: str
    long_name: str
    img: Optional[str] = None

class Thumbnail(BaseModel):
    src: str
    original: str
    logo: bool = False

class MetaUrl(BaseModel):
    scheme: str
    netloc: str
    hostname: str
    favicon: Optional[str]
    path: Optional[str]

class SearchResult(BaseModel):
    title: str
    url: str
    description: str
    profile: Profile
    meta_url: MetaUrl
    thumbnail: Optional[Thumbnail] = None
    age: Optional[str] = None
    language: str = "en"
    family_friendly: bool = True
    content: Optional[str] = None  # Added field to store fetched content

class WebResults(BaseModel):
    results: List[SearchResult]

class BraveSearchResponse(BaseModel):
    query: QueryInfo
    web: WebResults

class UrlContent(BaseModel):
    """Model to store URL content with metadata"""
    url: str
    title: str
    content: str
    content_length: int
    fetch_time: float

async def format_search_results(response: Dict[Any, Any], include_content: bool = False) -> str:
    """Format search results in markdown format and return as string"""
    try:
        search_response = BraveSearchResponse(
            query=response["query"],
            web=WebResults(results=response["web"]["results"])
        )
        
        markdown_results = []
        markdown_results.append(f"# Search Results for: {search_response.query.original}\n")
        
        for idx, result in enumerate(search_response.web.results, 1):
            markdown_results.append(f"{idx}. {result.title}")
            markdown_results.append(f"URL: {result.url}")
            markdown_results.append(f"Description: {result.description}")
            if result.age:
                markdown_results.append(f"Age: {result.age}")
            
            # Include content if available and requested
            if include_content and hasattr(result, 'content') and result.content:
                markdown_results.append("\nContent Preview:")
                # Limit content preview to avoid overwhelming output
                content_preview = result.content[:500] + "..." if len(result.content) > 500 else result.content
                markdown_results.append(f"```\n{content_preview}\n```")
            
            markdown_results.append("----------------------------------------\n")
            
        return "\n".join(markdown_results)
            
    except Exception as e:
        logger.error(f"Error formatting results: {str(e)}")
        return ""

async def fetch_url_content(url: str, session: aiohttp.ClientSession, retry_count: int = 2, delay: float = 1.0) -> Optional[str]:
    """
    Fetch content from a URL and extract the main text.
    
    Args:
        url (str): The URL to fetch content from
        session (aiohttp.ClientSession): The aiohttp session to use for the request
        retry_count (int): Number of retries if request fails
        delay (float): Delay between retries in seconds
        
    Returns:
        Optional[str]: The extracted text content or None if request fails
    """
    for attempt in range(retry_count + 1):
        try:
            logger.info(f"Fetching content from URL: {url} (attempt {attempt + 1}/{retry_count + 1})")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            async with session.get(url, headers=headers, timeout=10) as response:
                if not response.ok:
                    logger.warning(f"Failed to fetch URL {url}: Status {response.status}")
                    if attempt < retry_count:
                        logger.info(f"Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    return None
                
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                    logger.warning(f"Skipping non-HTML content from {url}: {content_type}")
                    return None
                
                html = await response.text()
                
                # Parse HTML and extract text
                soup = BeautifulSoup(html, 'html.parser')
                
                # Get title
                title = soup.title.string if soup.title else "No title"
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get text
                text = soup.get_text(separator='\n')
                
                # Break into lines and remove leading and trailing space on each
                lines = (line.strip() for line in text.splitlines())
                # Break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                # Remove blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                logger.info(f"Successfully extracted {len(text)} characters from {url}")
                return text
                
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            if attempt < retry_count:
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                return None

async def fetch_all_url_contents(urls: List[str], session: aiohttp.ClientSession, concurrency_limit: int = 3, delay_between_requests: float = 1.0) -> Dict[str, str]:
    """
    Fetch content from multiple URLs with rate limiting.
    
    Args:
        urls (List[str]): List of URLs to fetch content from
        session (aiohttp.ClientSession): The aiohttp session to use for requests
        concurrency_limit (int): Maximum number of concurrent requests
        delay_between_requests (float): Delay between requests in seconds
        
    Returns:
        Dict[str, str]: Dictionary mapping URLs to their content
    """
    semaphore = asyncio.Semaphore(concurrency_limit)
    url_contents = {}
    
    async def fetch_with_semaphore(url):
        async with semaphore:
            content = await fetch_url_content(url, session)
            if content:
                url_contents[url] = content
            await asyncio.sleep(delay_between_requests)  # Add delay between requests
    
    # Create tasks for fetching content from each URL
    tasks = [fetch_with_semaphore(url) for url in urls]
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)
    
    return url_contents

async def brave_search_with_content(
    query: str,
    count: int = 5,
    offset: int = 0,
    fetch_content: bool = True,
    retry_count: int = 2,
    retry_delay: float = 2.0,
    concurrency_limit: int = 3,
    delay_between_requests: float = 1.0
) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """
    Perform an asynchronous search query using the Brave Search API, 
    fetch content from the URLs in the results, and return both.
    
    Args:
        query (str): The search query
        count (int): Number of results to return (max 20) (default: 5)
        offset (int): Number of results to skip for pagination (default: 0)
        fetch_content (bool): Whether to fetch content from the URLs (default: True)
        retry_count (int): Number of retries if request fails (default: 2)
        retry_delay (float): Delay between retries in seconds (default: 2.0)
        concurrency_limit (int): Maximum number of concurrent requests (default: 3)
        delay_between_requests (float): Delay between requests in seconds (default: 1.0)
        
    Returns:
        Tuple[Optional[str], Optional[Dict[str, str]]]: 
            - Markdown formatted search results or None if request fails
            - Dictionary mapping URLs to their content or None if fetch_content is False
    """
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    if not api_key:
        raise ValueError("BRAVE_SEARCH_API_KEY environment variable is not set")

    base_url = "https://api.search.brave.com/res/v1/web/search"
    
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key
    }
    
    count = min(count, 20)
    
    params = {
        "q": query,
        "count": count
    }
    
    if offset > 0:
        params["offset"] = offset

    for attempt in range(retry_count + 1):
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch search results
                logger.info(f"Performing Brave search for query: {query} (attempt {attempt + 1}/{retry_count + 1})")
                async with session.get(base_url, headers=headers, params=params) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error(f"Error response from Brave Search API: {error_text}")
                        
                        # Check if rate limited
                        if response.status == 429:
                            if attempt < retry_count:
                                wait_time = retry_delay * (attempt + 1)  # Exponential backoff
                                logger.info(f"Rate limited. Retrying in {wait_time} seconds...")
                                await asyncio.sleep(wait_time)
                                continue
                        
                        return None, None
                    
                    try:
                        data = await response.json()
                        
                        # If we don't need to fetch content, just return the formatted results
                        if not fetch_content:
                            return await format_search_results(data), None
                        
                        # Extract URLs from search results
                        urls = [result["url"] for result in data["web"]["results"]]
                        logger.info(f"Found {len(urls)} URLs in search results")
                        
                        # Fetch content from each URL with rate limiting
                        url_to_content = await fetch_all_url_contents(
                            urls, 
                            session, 
                            concurrency_limit=concurrency_limit,
                            delay_between_requests=delay_between_requests
                        )
                        
                        logger.info(f"Successfully fetched content from {len(url_to_content)} URLs")
                        
                        # Add content to search results
                        for result in data["web"]["results"]:
                            result["content"] = url_to_content.get(result["url"])
                        
                        return await format_search_results(data, include_content=True), url_to_content
                        
                    except ValueError as e:
                        logger.error(f"Failed to decode JSON response: {str(e)}")
                        raw_response = await response.text()
                        logger.error(f"Raw response: {raw_response[:200]}...")
                        return None, None
                    
        except aiohttp.ClientError as e:
            logger.error(f"Error making request to Brave Search API: {str(e)}")
            if attempt < retry_count:
                wait_time = retry_delay * (attempt + 1)
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                return None, None
    
    return None, None

async def brave_search(
    query: str,
    count: int = 5,
    offset: int = 0,
    retry_count: int = 2,
    retry_delay: float = 2.0
) -> Optional[str]:
    """
    Perform an asynchronous search query using the Brave Search API and return markdown formatted results.
    
    Args:
        query (str): The search query
        count (int): Number of results to return (max 20) (default: 5)
        offset (int): Number of results to skip for pagination (default: 0)
        retry_count (int): Number of retries if request fails (default: 2)
        retry_delay (float): Delay between retries in seconds (default: 2.0)
        
    Returns:
        Optional[str]: Markdown formatted search results or None if request fails
    """
    results, _ = await brave_search_with_content(
        query, 
        count, 
        offset, 
        fetch_content=False,
        retry_count=retry_count,
        retry_delay=retry_delay
    )
    return results

async def get_content_for_llm(
    query: str,
    count: int = 5,
    max_content_length: int = 10000,
    concurrency_limit: int = 3,
    delay_between_requests: float = 1.0
) -> Optional[str]:
    """
    Perform a search and fetch content from URLs, formatting it for LLM consumption.
    
    Args:
        query (str): The search query
        count (int): Number of results to return (max 20) (default: 5)
        max_content_length (int): Maximum length of content to return per URL (default: 10000)
        concurrency_limit (int): Maximum number of concurrent requests (default: 3)
        delay_between_requests (float): Delay between requests in seconds (default: 1.0)
        
    Returns:
        Optional[str]: Formatted content for LLM consumption or None if request fails
    """
    _, url_content = await brave_search_with_content(
        query, 
        count=count, 
        fetch_content=True,
        concurrency_limit=concurrency_limit,
        delay_between_requests=delay_between_requests
    )
    
    if not url_content:
        return None
    
    # Format content for LLM consumption
    llm_content = []
    llm_content.append(f"# Search Results for: {query}\n")
    
    for url, content in url_content.items():
        # Truncate content if too long
        if len(content) > max_content_length:
            content = content[:max_content_length] + "... [content truncated]"
        
        llm_content.append(f"## Source: {url}")
        llm_content.append(content)
        llm_content.append("\n---\n")
    
    return "\n".join(llm_content)

async def fetch_documentation_for_llm(
    query: str,
    count: int = 5,
    max_content_length: int = 10000,
    max_total_length: int = 50000,
    concurrency_limit: int = 2,
    delay_between_requests: float = 1.5,
    retry_count: int = 2,
    retry_delay: float = 2.0
) -> Dict[str, Any]:
    """
    Fetch documentation content from search results and format it for LLM consumption.
    This function is specifically designed for retrieving documentation and API references.
    
    Args:
        query (str): The search query, preferably specific to documentation or API references
        count (int): Number of search results to process (max 20) (default: 5)
        max_content_length (int): Maximum length of content to return per URL (default: 10000)
        max_total_length (int): Maximum total length of all content combined (default: 50000)
        concurrency_limit (int): Maximum number of concurrent requests (default: 2)
        delay_between_requests (float): Delay between requests in seconds (default: 1.5)
        retry_count (int): Number of retries if request fails (default: 2)
        retry_delay (float): Delay between retries in seconds (default: 2.0)
        
    Returns:
        Dict[str, Any]: Dictionary containing:
            - 'query': The original search query
            - 'search_results': List of search result objects with title, url, and description
            - 'content': Dictionary mapping URLs to their extracted content
            - 'formatted_content': Formatted content ready for LLM consumption
            - 'total_content_length': Total length of all content combined
            - 'sources': List of sources with metadata
    """
    logger.info(f"Fetching documentation for query: {query}")
    
    # Perform search and fetch content
    search_results, url_content = await brave_search_with_content(
        query, 
        count=count, 
        fetch_content=True,
        concurrency_limit=concurrency_limit,
        delay_between_requests=delay_between_requests,
        retry_count=retry_count,
        retry_delay=retry_delay
    )
    
    if not url_content:
        logger.warning(f"No content found for query: {query}")
        return {
            'query': query,
            'search_results': [],
            'content': {},
            'formatted_content': "",
            'total_content_length': 0,
            'sources': []
        }
    
    # Extract search results from markdown
    search_result_objects = []
    if search_results:
        lines = search_results.split('\n')
        current_result = {}
        
        for line in lines:
            if line.startswith('# Search Results for:'):
                continue
            elif line.startswith('URL:'):
                current_result['url'] = line.replace('URL:', '').strip()
            elif line.startswith('Description:'):
                current_result['description'] = line.replace('Description:', '').strip()
                search_result_objects.append(current_result)
                current_result = {}
            elif line.startswith('----------------------------------------'):
                continue
            elif line.strip() and not line.startswith('Age:') and not line.startswith('Content Preview:'):
                # This must be a title
                current_result = {'title': line.strip()}
    
    # Format content for LLM consumption with better structure
    formatted_content = []
    formatted_content.append(f"# Documentation Results for: {query}\n")
    
    sources = []
    total_content_length = 0
    truncated_content = {}
    
    # Sort URLs by content length (descending) to prioritize more comprehensive documentation
    sorted_urls = sorted(url_content.items(), key=lambda x: len(x[1]), reverse=True)
    
    for url, content in sorted_urls:
        # Find the title from search results
        title = next((result['title'] for result in search_result_objects if result.get('url') == url), "Unknown Title")
        
        # Clean and format the content
        content = content.strip()
        content_length = len(content)
        
        # Truncate content if too long
        if content_length > max_content_length:
            truncated_content[url] = content[:max_content_length] + "... [content truncated]"
        else:
            truncated_content[url] = content
        
        # Add to total length
        total_content_length += len(truncated_content[url])
        
        # Add source metadata
        sources.append({
            'url': url,
            'title': title,
            'content_length': content_length,
            'truncated': content_length > max_content_length
        })
    
    # Check if total content exceeds maximum and truncate if necessary
    if total_content_length > max_total_length:
        logger.warning(f"Total content length ({total_content_length}) exceeds maximum ({max_total_length}). Truncating...")
        
        # Reset and recalculate
        total_content_length = 0
        new_truncated_content = {}
        
        # Allocate content proportionally to each source
        for url, content in sorted_urls:
            # Calculate proportion of max_total_length this source should get
            original_length = len(url_content[url])
            proportion = original_length / sum(len(content) for _, content in sorted_urls)
            allocated_length = int(proportion * max_total_length)
            
            # Ensure minimum content is preserved
            allocated_length = max(allocated_length, 1000)  # At least 1000 chars per source
            allocated_length = min(allocated_length, original_length)  # But not more than original
            
            # Truncate content
            if original_length > allocated_length:
                new_truncated_content[url] = url_content[url][:allocated_length] + "... [content truncated]"
            else:
                new_truncated_content[url] = url_content[url]
            
            # Update source metadata
            for source in sources:
                if source['url'] == url:
                    source['truncated'] = original_length > allocated_length
                    break
            
            # Add to total length
            total_content_length += len(new_truncated_content[url])
            
            # Stop if we've exceeded max_total_length
            if total_content_length >= max_total_length:
                break
        
        truncated_content = new_truncated_content
    
    # Format the content for LLM consumption
    for url, content in truncated_content.items():
        # Find the title from search results
        title = next((result['title'] for result in search_result_objects if result.get('url') == url), "Unknown Title")
        
        formatted_content.append(f"## {title}")
        formatted_content.append(f"Source: {url}")
        formatted_content.append(f"```")
        formatted_content.append(content)
        formatted_content.append(f"```")
        formatted_content.append("\n---\n")
    
    # Add a summary of sources at the end
    formatted_content.append("## Sources Summary")
    for i, source in enumerate(sources, 1):
        if source['url'] in truncated_content:
            formatted_content.append(f"{i}. [{source['title']}]({source['url']}) - {source['content_length']} chars" + 
                                    (" (truncated)" if source['truncated'] else ""))
    
    return {
        'query': query,
        'search_results': search_result_objects,
        'content': url_content,
        'formatted_content': "\n".join(formatted_content),
        'total_content_length': total_content_length,
        'sources': sources
    }

if __name__ == "__main__":
    # Example usage
    async def main():
        # Example 1: Just search results
        logger.info("Running example 1: Just search results")
        results = await brave_search("NYLAS API WEBHOOK REGISTRATION", count=2)
        if results:
            print(results)
            print("\n" + "="*50 + "\n")
        
        # Add delay to avoid rate limiting
        await asyncio.sleep(3)
        
        # Example 2: Search results with content
        logger.info("Running example 2: Search results with content")
        results, url_content = await brave_search_with_content(
            "NYLAS API WEBHOOK REGISTRATION", 
            count=2,
            concurrency_limit=1,  # Limit concurrency to avoid rate limiting
            delay_between_requests=2.0  # Add delay between requests
        )
        if results:
            print(results)
            print("\n" + "="*50 + "\n")
        
        # Add delay to avoid rate limiting
        await asyncio.sleep(3)
        
        # Example 3: Get content for LLM processing
        logger.info("Running example 3: Get content for LLM processing")
        llm_content = await get_content_for_llm(
            "NYLAS API WEBHOOK REGISTRATION", 
            count=2,
            concurrency_limit=1,  # Limit concurrency to avoid rate limiting
            delay_between_requests=2.0  # Add delay between requests
        )
        if llm_content:
            print(f"Content for LLM processing (preview):")
            print(llm_content[:500] + "...\n")
        
        # Add delay to avoid rate limiting
        await asyncio.sleep(3)
        
        # Example 4: Fetch documentation for LLM with advanced formatting
        logger.info("Running example 4: Fetch documentation for LLM with advanced formatting")
        doc_results = await fetch_documentation_for_llm(
            "NYLAS API WEBHOOK REGISTRATION", 
            count=2,
            concurrency_limit=1,
            delay_between_requests=2.0
        )
        if doc_results['formatted_content']:
            print(f"Documentation for LLM (preview):")
            print(doc_results['formatted_content'][:500] + "...\n")
            print(f"Total content length: {doc_results['total_content_length']} characters")
            print(f"Sources: {len(doc_results['sources'])}")
            for i, source in enumerate(doc_results['sources'], 1):
                print(f"  {i}. {source['title']} - {source['content_length']} chars" + 
                      (" (truncated)" if source['truncated'] else ""))

    asyncio.run(main())
