import asyncio
import aiohttp
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

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

class WebResults(BaseModel):
    results: List[SearchResult]

class BraveSearchResponse(BaseModel):
    query: QueryInfo
    web: WebResults

async def format_search_results(response: Dict[Any, Any]) -> str:
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
            markdown_results.append("----------------------------------------\n")
            
        return "\n".join(markdown_results)
            
    except Exception as e:
        print(f"Error formatting results: {str(e)}")
        return ""

async def brave_search(
    query: str,
    count: int = 5,
    offset: int = 0
) -> Optional[str]:
    """
    Perform an asynchronous search query using the Brave Search API and return markdown formatted results.
    
    Args:
        query (str): The search query
        count (int): Number of results to return (max 20) (default: 5)
        offset (int): Number of results to skip for pagination (default: 0)
        
    Returns:
        Optional[str]: Markdown formatted search results or None if request fails
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

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, headers=headers, params=params) as response:
                if not response.ok:
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
                    return None
                
                try:
                    data = await response.json()
                    return await format_search_results(data)
                except ValueError:
                    print("Failed to decode JSON response")
                    raw_response = await response.text()
                    print(f"Raw response: {raw_response[:200]}...")
                    return None
                
    except aiohttp.ClientError as e:
        print(f"Error making request to Brave Search API: {str(e)}")
        return None

if __name__ == "__main__":
    # Example usage
    async def main():
        results = await brave_search("AMAZON CO UK RETAIL", count=4)
        if results:
            print(results)

    asyncio.run(main())
