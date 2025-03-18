import random
from typing import Optional

from ..API.api import RULE34_BASE_URL
from ..Client.Client import client

class Rule34:
    @staticmethod
    async def fetch_images(tag: Optional[str] = None, total_images: int = 1000, max_retries: int = 5) -> Optional[str]:
        limit_per_page = 100  
        total_pages = max(total_images // limit_per_page, 1)
        collected_images = []

        for _ in range(max_retries):
            try:
                for page in range(total_pages):
                    params = {
                        "page": "dapi",
                        "s": "post",
                        "q": "index",
                        "json": "1",
                        "limit": limit_per_page,
                        "pid": page
                    }
                    if tag:
                        params["tags"] = tag.replace(" ", "_")
                    
                    response = await client.get(RULE34_BASE_URL, params=params)
                    response.raise_for_status()

                    posts = response.json()
                    if isinstance(posts, list):
                        collected_images.extend(
                            post["file_url"] for post in posts if "file_url" in post
                        )
                    
                    if len(collected_images) >= total_images:
                        break
                
                if collected_images:
                    return random.choice(collected_images)
            except Exception:
                pass
        return None
