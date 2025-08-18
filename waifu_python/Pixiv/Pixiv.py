import requests, asyncio, time, hashlib, random, os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Any, Union
import urllib.parse as up

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"
HASH_SECRET = "28c1fdd170a5204386cb1313c7077b34f83e4aaf4aa829ce78c231e05b0bae2c"
OAUTH_URL = "https://oauth.secure.pixiv.net/auth/token"

CACHE_FILE = Path(os.getcwd()) / ".cache"

class DotDict:
    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, DotDict(value))
            elif isinstance(value, list):
                setattr(self, key, [DotDict(item) if isinstance(item, dict) else item for item in value])
            else:
                setattr(self, key, value)
                
    def __repr__(self):
        return str({k: v for k, v in self.__dict__.items()})
    
    def get(self, key, default=None):
        return self.__dict__.get(key, default)

class Pixiv:

    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.hosts = "https://app-api.pixiv.net"

    @classmethod
    def _load_cached_token(cls) -> Optional[str]:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                token = f.read().strip()
            if token:
                return token
        return None

    @classmethod
    def _cache_token(cls, token: str):
        with open(CACHE_FILE, "w") as f:
            f.write(token)

    @classmethod
    def pixiv_init(cls) -> "Pixiv":
        cached_token = cls._load_cached_token()
        refresh_token = os.getenv("PIXIV_REFRESH_TOKEN")
        if not refresh_token:
            raise ValueError("Pixiv refresh token missing in .env.")
        instance = cls(cached_token if cached_token else "", refresh_token)
        
        if not instance.access_token:
            success = instance.refresh_access_token()
            if not success:
                raise Exception("Failed to obtain access token via refresh token.")
        return instance

    @staticmethod
    def parse_next_url(next_url: Optional[str]) -> dict:
        if next_url is None:
            return {}
        query = up.urlparse(next_url).query
        qs = up.parse_qs(query)
        return {key: value[-1] for key, value in qs.items()}

    def get_pixiv_headers(self) -> dict:
        client_time = str(int(time.time()))
        client_hash = hashlib.md5((client_time + HASH_SECRET).encode("utf-8")).hexdigest()
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "PixivIOSApp/7.13.3 (iOS 14.4; iPhone12,1)",
            "X-Client-Time": client_time,
            "X-Client-Hash": client_hash
        }
        return headers

    def refresh_access_token(self) -> bool:
        local_time = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
        client_hash = hashlib.md5((local_time + HASH_SECRET).encode("utf-8")).hexdigest()
        headers = {
            "x-client-time": local_time,
            "x-client-hash": client_hash,
            "User-Agent": "PixivIOSApp/7.13.3 (iOS 14.4; iPhone12,1)"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "get_secure_url": 1
        }
        response = requests.post(OAUTH_URL, headers=headers, data=data)
        try:
            response.raise_for_status()
        except Exception as e:
            print(f"Token refresh error: {e}")
            return False

        token_data = response.json()
        new_access = token_data.get("response", {}).get("access_token")
        if new_access:
            self.access_token = new_access  
            self._cache_token(new_access)     
            print("Token refreshed successfully.")
            return True
        return False

    def format_bool(self, bool_value: Union[bool, str, None]) -> str:
        if isinstance(bool_value, bool):
            return "true" if bool_value else "false"
        if bool_value in {"true", "True"}:
            return "true"
        return "false"

    def paginate_search(self, initial_word: str, max_pages: int = 3) -> list[DotDict]:
        results = []
        current_url = None
        page_count = 0
    
        while page_count < max_pages:
            response = self.search_illust(
                word=initial_word if page_count == 0 else None,
                next_url=current_url
            )
            if not response or not response.illusts:
                break
            results.append(response)
            page_count += 1
            if not hasattr(response, 'next_url') or not response.next_url:
                break
            current_url = response.next_url
        return results
            
    def _extract_original_url(self, illust: dict) -> Optional[str]:
        meta_single_page = illust.get("meta_single_page", {})
        if meta_single_page and meta_single_page.get("original_image_url"):
            return meta_single_page.get("original_image_url")
        if illust.get("original_image_url"):
            return illust.get("original_image_url")
        meta_pages = illust.get("meta_pages")
        if meta_pages and isinstance(meta_pages, list) and meta_pages:
            first_page = meta_pages[0]
            image_urls = first_page.get("image_urls")
            if image_urls and image_urls.get("original"):
                return image_urls.get("original")
        image_urls = illust.get("image_urls")
        if image_urls and image_urls.get("original"):
            return image_urls.get("original")
        return None
    
    def download_image(self, image_url: str, filename: str) -> bool:
        project_root = Path(__file__).resolve().parent.parent.parent
        downloads_dir = project_root / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)  
        filepath = downloads_dir / filename
        headers = self.get_pixiv_headers()
        headers["Referer"] = "https://app-api.pixiv.net/"
        response = requests.get(image_url, headers=headers, stream=True)
        try:
            response.raise_for_status()
        except Exception as e:
            print(f"Error downloading image: {e}")
            return False
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Image downloaded as '{filepath}'")
        return True
    
    @classmethod
    async def fetch_images(
        cls,
        query: Optional[Union[str, int]] = None,
        tag: Optional[str] = None,
        max_pages: int = 100,
        sort: str = "date_desc",
        limit: int = 50,
        fetch_limit: int = 1,
        download: bool = False,
        return_json: bool = False  
    ) -> Union[list[str], tuple[list[str], dict], str, tuple[str, dict]]:
    
        api = await asyncio.to_thread(cls.pixiv_init)
        
        async def safe_api_call(func, *args, **kwargs):
            try:
                return await asyncio.to_thread(func, *args, **kwargs)
            except requests.HTTPError as e:
                error_json = {}
                try:
                    error_json = e.response.json()
                except Exception:
                    pass
                if (e.response is not None and (e.response.status_code == 401 or 
                    (e.response.status_code == 400 and "invalid" in str(error_json.get("error", "")).lower()))):
                    refreshed = await asyncio.to_thread(api.refresh_access_token)
                    if refreshed:
                        return await asyncio.to_thread(func, *args, **kwargs)
                    else:
                        raise Exception("Token refresh failed.")
                else:
                    raise

        if isinstance(query, int):
            result = await safe_api_call(api.illust_related, query)
            all_illusts = result.get("illusts")
            combined_json = result
        elif isinstance(query, str) or tag is not None:
            search_word = tag if tag is not None else query
            search_word = search_word.replace(" ", "_")
            all_illusts = []
            next_url = None
            page_count = 0
            combined_json = {"illusts": []}
            while page_count < max_pages:
                result = await safe_api_call(api.search_illust,
                                             word=search_word if page_count == 0 else None,
                                             next_url=next_url,
                                             sort=sort,
                                             limit=limit)
                illusts = result.get("illusts")
                if not result or not illusts:
                    break
                all_illusts.extend(illusts)
                combined_json["illusts"].extend(illusts)
                next_url = result.get("next_url")
                if not next_url:
                    break
                page_count += 1
        else:
            result = await safe_api_call(api.illust_recommended)
            all_illusts = result.get("illusts")
            combined_json = result
        
        if not all_illusts:
            return "" if not return_json else ("", combined_json)
        
        image_urls = [
            api._extract_original_url(illust)
            for illust in all_illusts
            if api._extract_original_url(illust)
        ]
        
        if not image_urls:
            return "" if not return_json else ("", combined_json)
        
        if isinstance(query, int):
            result_urls = image_urls
        else:
            if fetch_limit == 1:
                result_urls = random.choice(image_urls)
            else:
                result_urls = random.sample(image_urls, min(fetch_limit, len(image_urls)))
        
        if download:
            if isinstance(result_urls, list):
                for url in result_urls:
                    filename = url.split("/")[-1]
                    await asyncio.to_thread(api.download_image, url, filename)
            else:
                filename = result_urls.split("/")[-1]
                await asyncio.to_thread(api.download_image, result_urls, filename)
        
        if return_json:
            return result_urls, combined_json
        return result_urls

    def search_illust(
        self,
        word: Optional[str] = None,
        next_url: Optional[str] = None,
        search_target: str = "partial_match_for_tags",
        sort: str = "date_desc",
        duration: Optional[str] = None,
        filter: str = "for_ios",
        limit: Optional[int] = None,
    ) -> Optional[DotDict]:
        if next_url:
            url = next_url
            params = None
        else:
            url = f"{self.hosts}/v1/search/illust"
            params = {
                "word": word,
                "search_target": search_target,
                "sort": sort,
                "filter": filter,
            }
            if duration:
                params["duration"] = duration
            if limit:
                params["limit"] = limit  
        headers = self.get_pixiv_headers()
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        wrapped_data = DotDict(data)
        if limit and hasattr(wrapped_data, "illusts"):
            wrapped_data.illusts = wrapped_data.illusts[:limit]
        return wrapped_data


    def illust_related(
        self,
        illust_id: Union[int, str],
        filter: str = "for_ios",
        seed_illust_ids: Optional[Union[int, str, list[str]]] = None,
        offset: Union[int, str, None] = None,
        viewed: Optional[Union[str, list[str]]] = None,
        req_auth: bool = True,
    ) -> Optional[dict]:
        url = f"{self.hosts}/v2/illust/related"
        params: dict[str, Any] = {
            "illust_id": illust_id,
            "filter": filter,
            "offset": offset,
        }
        if isinstance(seed_illust_ids, str):
            params["seed_illust_ids[]"] = [seed_illust_ids]
        elif isinstance(seed_illust_ids, list):
            params["seed_illust_ids[]"] = seed_illust_ids
        if isinstance(viewed, str):
            params["viewed[]"] = [viewed]
        elif isinstance(viewed, list):
            params["viewed[]"] = viewed
        headers = self.get_pixiv_headers()
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def illust_recommended(
        self,
        content_type: str = "illust",
        include_ranking_label: Union[bool, str] = True,
        filter: str = "for_ios",
        max_bookmark_id_for_recommend: Union[int, str, None] = None,
        min_bookmark_id_for_recent_illust: Union[int, str, None] = None,
        offset: Union[int, str, None] = None,
        include_ranking_illusts: Union[bool, str, None] = None,
        bookmark_illust_ids: Union[str, list[Union[int, str]], None] = None,
        include_privacy_policy: Union[str, list[Union[int, str]], None] = None,
        viewed: Union[str, list[str], None] = None,
        req_auth: bool = True,
    ) -> Optional[dict]:
        if req_auth:
            url = f"{self.hosts}/v1/illust/recommended"
        else:
            url = f"{self.hosts}/v1/illust/recommended-nologin"
        params: dict[str, Any] = {
            "content_type": content_type,
            "include_ranking_label": self.format_bool(include_ranking_label),
            "filter": filter,
        }
        if max_bookmark_id_for_recommend:
            params["max_bookmark_id_for_recommend"] = max_bookmark_id_for_recommend
        if min_bookmark_id_for_recent_illust:
            params["min_bookmark_id_for_recent_illust"] = min_bookmark_id_for_recent_illust
        if offset:
            params["offset"] = offset
        if include_ranking_illusts:
            params["include_ranking_illusts"] = self.format_bool(include_ranking_illusts)
        if isinstance(viewed, str):
            params["viewed[]"] = [viewed]
        elif isinstance(viewed, list):
            params["viewed[]"] = viewed
        if not req_auth and isinstance(bookmark_illust_ids, (str, list)):
            if isinstance(bookmark_illust_ids, list):
                params["bookmark_illust_ids"] = ",".join(str(iid) for iid in bookmark_illust_ids)
            else:
                params["bookmark_illust_ids"] = bookmark_illust_ids
        if include_privacy_policy:
            params["include_privacy_policy"] = include_privacy_policy
        headers = self.get_pixiv_headers()
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
