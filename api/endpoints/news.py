from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from db.session import get_db
from db.models import News
from core.security import verify_token
import httpx
from datetime import datetime, timedelta
import uuid
import logging
from typing import Optional, List
from core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

NEWS_API_URL = settings.NEWS_API_URL
NEWS_API_KEY = settings.NEWS_API_KEY

@router.get("/")
async def get_news(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    # Calculate pagination parameters
    skip = (page - 1) * page_size

    # Get total count for pagination metadata
    total_count = db.query(News).count()

    # Get paginated news items
    news_items = db.query(News).order_by(desc(News.published_at)).offset(skip).limit(page_size).all()

    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1

    # Format response
    return {
        "items": [{
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "url": item.url,
            "published_at": item.published_at
        } for item in news_items],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_count,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
    }

@router.post("/save-latest")
async def save_latest_news(db: Session = Depends(get_db), token: str = Depends(verify_token)):

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NEWS_API_URL}/top-headlines",
                params={"apiKey": NEWS_API_KEY, "country": "us", "pageSize": 3},
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                raise HTTPException(status_code=500, detail="Failed to fetch news from external API")

            saved_count = 0
            for article in data.get("articles", [])[:3]:

                published_at = datetime.fromisoformat(article.get("publishedAt", "").replace("Z", "+00:00"))


                news_item = News(
                    id=str(uuid.uuid4()),
                    title=article.get("title", ""),
                    description=article.get("description", ""),
                    url=article.get("url", ""),
                    published_at=published_at
                )

                db.add(news_item)
                saved_count += 1

            db.commit()
            return {"message": f"Successfully saved {saved_count} news articles"}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"HTTP error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Error saving latest news: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving latest news: {str(e)}")

@router.get("/headlines/country/{country_code}")
async def get_headlines_by_country(
    country_code: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    token: str = Depends(verify_token)
):
    try:
        logger.info(f"Fetching headlines for country: {country_code}, page: {page}, page_size: {page_size}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NEWS_API_URL}/top-headlines",
                params={
                    "apiKey": NEWS_API_KEY,
                    "country": country_code,
                    "page": page,
                    "pageSize": page_size
                },
            )

            # Log the request details for debugging
            logger.debug(f"Request URL: {response.request.url}")
            logger.debug(f"Response status: {response.status_code}")

            # Handle different HTTP status codes
            if response.status_code == 401:
                logger.error("NewsAPI authentication failed. Invalid API key.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="NewsAPI authentication failed. Please check your API key."
                )
            elif response.status_code == 429:
                logger.error("NewsAPI rate limit exceeded.")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="NewsAPI rate limit exceeded. Please try again later."
                )

            response.raise_for_status()
            data = response.json()

            # Check if the API returned an error
            if data.get("status") == "error":
                error_message = data.get("message", "Unknown error from NewsAPI")
                logger.error(f"NewsAPI error: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"NewsAPI error: {error_message}"
                )

            return data
    except httpx.TimeoutException:
        logger.error("Request to NewsAPI timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to NewsAPI timed out. Please try again later."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"HTTP error occurred: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to NewsAPI. Please try again later."
        )
    except Exception as e:
        logger.exception(f"Unexpected error when fetching headlines: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )

@router.get("/headlines/source/{source_id}")
async def get_headlines_by_source(
    source_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    token: str = Depends(verify_token)
):
    try:
        logger.info(f"Fetching headlines for source: {source_id}, page: {page}, page_size: {page_size}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NEWS_API_URL}/top-headlines",
                params={
                    "apiKey": NEWS_API_KEY,
                    "sources": source_id,
                    "page": page,
                    "pageSize": page_size
                },
            )

            # Log the request details for debugging
            logger.debug(f"Request URL: {response.request.url}")
            logger.debug(f"Response status: {response.status_code}")

            # Handle different HTTP status codes
            if response.status_code == 401:
                logger.error("NewsAPI authentication failed. Invalid API key.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="NewsAPI authentication failed. Please check your API key."
                )
            elif response.status_code == 429:
                logger.error("NewsAPI rate limit exceeded.")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="NewsAPI rate limit exceeded. Please try again later."
                )

            response.raise_for_status()
            data = response.json()

            # Check if the API returned an error
            if data.get("status") == "error":
                error_message = data.get("message", "Unknown error from NewsAPI")
                logger.error(f"NewsAPI error: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"NewsAPI error: {error_message}"
                )

            return data
    except httpx.TimeoutException:
        logger.error("Request to NewsAPI timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to NewsAPI timed out. Please try again later."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"HTTP error occurred: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to NewsAPI. Please try again later."
        )
    except Exception as e:
        logger.exception(f"Unexpected error when fetching headlines: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )

@router.get("/headlines/filter")
async def get_headlines_by_filter(
    country: str = Query(None, description="Country code (e.g., 'us', 'gb')"),
    source: str = Query(None, description="Source ID (e.g., 'bbc-news')"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    token: str = Depends(verify_token)
):
    if not country and not source:
        raise HTTPException(status_code=400, detail="At least one filter parameter (country or source) is required")

    try:
        logger.info(f"Fetching headlines with filters - country: {country}, source: {source}, page: {page}, page_size: {page_size}")
        params = {
            "apiKey": NEWS_API_KEY,
            "page": page,
            "pageSize": page_size
        }
        if country:
            params["country"] = country
        if source:
            params["sources"] = source

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NEWS_API_URL}/top-headlines",
                params=params,
            )

            # Log the request details for debugging
            logger.debug(f"Request URL: {response.request.url}")
            logger.debug(f"Response status: {response.status_code}")

            # Handle different HTTP status codes
            if response.status_code == 401:
                logger.error("NewsAPI authentication failed. Invalid API key.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="NewsAPI authentication failed. Please check your API key."
                )
            elif response.status_code == 429:
                logger.error("NewsAPI rate limit exceeded.")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="NewsAPI rate limit exceeded. Please try again later."
                )

            response.raise_for_status()
            data = response.json()

            # Check if the API returned an error
            if data.get("status") == "error":
                error_message = data.get("message", "Unknown error from NewsAPI")
                logger.error(f"NewsAPI error: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"NewsAPI error: {error_message}"
                )

            # Add pagination metadata if not present in the response
            if "totalResults" in data and "articles" in data:
                total_results = data["totalResults"]
                total_pages = (total_results + page_size - 1) // page_size
                data["pagination"] = {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_results,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }

            return data
    except httpx.TimeoutException:
        logger.error("Request to NewsAPI timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to NewsAPI timed out. Please try again later."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"HTTP error occurred: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to NewsAPI. Please try again later."
        )
    except Exception as e:
        logger.exception(f"Unexpected error when fetching headlines: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )

@router.get("/everything")
async def search_news(
    q: str = Query(..., description="Keywords or phrases to search for in the article title and body"),
    from_date: Optional[str] = Query(None, alias="from", description="A date and optional time for the oldest article allowed"),
    to_date: Optional[str] = Query(None, alias="to", description="A date and optional time for the newest article allowed"),
    language: Optional[str] = Query(None, description="The 2-letter ISO-639-1 code of the language"),
    sort_by: Optional[str] = Query("publishedAt", description="The order to sort the articles in"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize", description="Number of results per page"),
    token: str = Depends(verify_token)
):
    """
    Search through millions of articles from over 80,000 large and small news sources and blogs.
    This endpoint is great for news analysis and article discovery.
    """
    try:
        logger.info(f"Searching news with query: {q}, from: {from_date}, to: {to_date}, language: {language}, sort_by: {sort_by}")

        # Build parameters
        params = {
            "apiKey": NEWS_API_KEY,
            "q": q,
            "page": page,
            "pageSize": page_size,
            "sortBy": sort_by
        }

        # Add optional parameters if provided
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if language:
            params["language"] = language

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NEWS_API_URL}/everything",
                params=params,
            )

            # Log the request details for debugging
            logger.debug(f"Request URL: {response.request.url}")
            logger.debug(f"Response status: {response.status_code}")

            # Handle different HTTP status codes
            if response.status_code == 401:
                logger.error("NewsAPI authentication failed. Invalid API key.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="NewsAPI authentication failed. Please check your API key."
                )
            elif response.status_code == 429:
                logger.error("NewsAPI rate limit exceeded.")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="NewsAPI rate limit exceeded. Please try again later."
                )

            response.raise_for_status()
            data = response.json()

            # Check if the API returned an error
            if data.get("status") == "error":
                error_message = data.get("message", "Unknown error from NewsAPI")
                logger.error(f"NewsAPI error: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"NewsAPI error: {error_message}"
                )

            # Add pagination metadata if not present in the response
            if "totalResults" in data and "articles" in data:
                total_results = data["totalResults"]
                total_pages = (total_results + page_size - 1) // page_size
                data["pagination"] = {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_results,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }

            return data
    except httpx.TimeoutException:
        logger.error("Request to NewsAPI timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to NewsAPI timed out. Please try again later."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"HTTP error occurred: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to NewsAPI. Please try again later."
        )
    except Exception as e:
        logger.exception(f"Unexpected error when searching news: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )

@router.get("/sources")
async def get_sources(
    category: Optional[str] = Query(None, description="Find sources that display news of this category"),
    language: Optional[str] = Query(None, description="Find sources that display news in a specific language"),
    country: Optional[str] = Query(None, description="Find sources that display news in a specific country"),
    token: str = Depends(verify_token)
):
    """
    This endpoint returns the subset of news publishers that top headlines are available from.
    It's mainly used to obtain a list of all possible sources/publishers available in the system.
    """
    try:
        logger.info(f"Fetching sources with category: {category}, language: {language}, country: {country}")

        # Build parameters
        params = {"apiKey": NEWS_API_KEY}

        # Add optional parameters if provided
        if category:
            params["category"] = category
        if language:
            params["language"] = language
        if country:
            params["country"] = country

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{NEWS_API_URL}/top-headlines/sources",
                params=params,
            )

            # Log the request details for debugging
            logger.debug(f"Request URL: {response.request.url}")
            logger.debug(f"Response status: {response.status_code}")

            # Handle different HTTP status codes
            if response.status_code == 401:
                logger.error("NewsAPI authentication failed. Invalid API key.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="NewsAPI authentication failed. Please check your API key."
                )
            elif response.status_code == 429:
                logger.error("NewsAPI rate limit exceeded.")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="NewsAPI rate limit exceeded. Please try again later."
                )

            response.raise_for_status()
            data = response.json()

            # Check if the API returned an error
            if data.get("status") == "error":
                error_message = data.get("message", "Unknown error from NewsAPI")
                logger.error(f"NewsAPI error: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"NewsAPI error: {error_message}"
                )

            return data
    except httpx.TimeoutException:
        logger.error("Request to NewsAPI timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request to NewsAPI timed out. Please try again later."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"HTTP error occurred: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to NewsAPI. Please try again later."
        )
    except Exception as e:
        logger.exception(f"Unexpected error when fetching sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )