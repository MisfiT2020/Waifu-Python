import random
import inspect
from typing import Any, Optional, Union, List, Tuple, Callable, Coroutine

from waifu_python import *
from ..Utils.stdout import suppress_stdout

class RandomWaifu:
    
    fetch_functions: List[Tuple[Callable[[Optional[str], int], Coroutine[Any, Any, Any]], type, bool]] = [
        (Danbooru.fetch_sfw_images, Danbooru, False),
        (Danbooru.fetch_nsfw_images, Danbooru, False),
        (Gelbooru.fetch_images, Gelbooru, False),
        (Yandere.fetch_images, Yandere, False),
        (Rule34.fetch_images, Rule34, False),
        (WaifuIm.fetch_sfw_images, WaifuIm, True),
        (WaifuIm.fetch_nsfw_images, WaifuIm, True),
        (WaifuPics.fetch_sfw_images, WaifuPics, True),
        (WaifuPics.fetch_nsfw_images, WaifuPics, True),
        (Safebooru.fetch_images, Safebooru, False),
        (NekosBest.fetch_sfw_images, NekosBest, True),
        (NSFWBot.fetch_sfw_images, NSFWBot, True),
        (NSFWBot.fetch_nsfw_images, NSFWBot, True),
        (PicRe.fetch_sfw_images, PicRe, True),
        (Pixiv.fetch_images, Pixiv, False),
        (Konachan.fetch_sfw_images, Konachan, False),
        (Konachan.fetch_nsfw_images, Konachan, False),
        (Zerochan.fetch_sfw_images, Zerochan, False),
        (PurrBot.fetch_sfw_gif, PurrBot, True),
        (PurrBot.fetch_nsfw_gif, PurrBot, True),
        (Sankaku.fetch_sfw_images, Sankaku, False),
        (Sankaku.fetch_nsfw_images, Sankaku, False),
        (KemonoParty.fetch_nsfw_images, KemonoParty, True),
        (Iwara.iwara_fetch, Iwara, True),
        (Aibooru.fetch_sfw_images, Iwara, False),
        (Aibooru.fetch_nsfw_images, Iwara, True),
        (Tbib.fetch_sfw_images, Tbib, False),
        (Tbib.fetch_sfw_images, Tbib, True),
        (Hijiribe.fetch_sfw_images, Hijiribe, False),
        (Hijiribe.fetch_sfw_images, Hijiribe, True)
    ]

    @classmethod
    async def _call_Random_func(cls, func: Callable, tag: Optional[str] = None, limit: int = 1) -> Optional[Union[str, List[str]]]:
        try:
            sig = inspect.signature(func)
            kwargs = {}
            if 'tag' in sig.parameters:
                kwargs['tag'] = tag
            if 'limit' in sig.parameters:
                kwargs['limit'] = limit
                
            with suppress_stdout():
                result = await func(**kwargs)
                
            if isinstance(result, dict) and 'error' in result:
                return None
            if isinstance(result, list) and any(isinstance(item, dict) and 'error' in item for item in result):
                return None

            return result

        except Exception:
            return None
        
    @classmethod
    async def _get_supported_tags(cls, service_cls: type) -> Optional[List[str]]:
        """Get supported tags for a class, if available."""
        try:
            if hasattr(service_cls, 'get_tags'):
                return await service_cls.get_tags()
        except Exception:
            return None
        return None

    @classmethod
    async def _try_function(cls, func: Callable, service_cls: type, tag: Optional[str], limit: int) -> Optional[str]:
        try:
            if tag:
                if service_cls in (WaifuIm, WaifuPics, NekosBest, NSFWBot, PicRe, PurrBot):
                    return None
                if hasattr(service_cls, 'validate_tag'):
                    is_valid = await service_cls.validate_tag(tag)
                    if not is_valid:
                        return None
                else:
                    supported_tags = await cls._get_supported_tags(service_cls)
                    if supported_tags and tag not in supported_tags:
                        return None
            sig = inspect.signature(func)
            kwargs = {}
            if 'tag' in sig.parameters:
                kwargs['tag'] = tag
            if 'limit' in sig.parameters:
                kwargs['limit'] = limit
            with suppress_stdout():
                result = await func(**kwargs)
            if isinstance(result, list):
                result = result[0] if result else None
            if isinstance(result, dict) and result.get("error"):
                return None
            return result
        except Exception:
            return None

    @classmethod
    async def get_random(cls, tag: Optional[str] = None, limit: int = 1) -> Optional[Tuple[Union[str, List[str]], str]]:
        funcs = cls.fetch_functions.copy()
        random.shuffle(funcs)
        for func, service_cls, supports_tags in funcs:
            result = await cls._try_function(func, service_cls, tag, limit)
            if result:
                func_name = func.__name__.lower() 
                if func_name == "fetch_images":
                    flag = "ambiguous"
                elif "nsfw" in func_name:
                    flag = "nsfw"
                else:
                    flag = "sfw"
                return result, flag
        return None

    @classmethod
    async def get_random_sfw_image(cls, tag: Optional[str] = None, limit: int = 1) -> Optional[Union[str, List[str]]]:
        funcs = [(f, svc, _) for f, svc, _ in cls.fetch_functions if f.__name__ == "fetch_sfw_images"]        
        random.shuffle(funcs)
        results = []
        for func, svc, _ in funcs:
            if tag and svc in (WaifuIm, WaifuPics, NekosBest, NSFWBot, PicRe, PurrBot):
                continue
            result = await cls._call_Random_func(func, tag, limit)
            
            if not result or (isinstance(result, dict) and "error" in result):
                continue
            
            if isinstance(result, list):
                valid_items = [
                    item for item in result
                    if not isinstance(item, dict) or "error" not in item
                ]
                results.extend(valid_items[:max(0, limit - len(results))])
            else:
                results.append(result)
                
            if len(results) >= limit:
                break

        return results if limit > 1 else (results[0] if results else None)
    
    @classmethod
    async def get_random_nsfw_image(cls, tag: Optional[str] = None, limit: int = 1) -> Optional[Union[str, List[str]]]:
        funcs = [(f, svc, _) for f, svc, _ in cls.fetch_functions 
                 if svc in (Rule34, NSFWBot, KemonoParty, Konachan, WaifuIm, WaifuPics, Aibooru, Pixiv, Tbib, Hijiribe)
                    and 'gif' not in f.__name__.lower() and 'nsfw' in f.__name__.lower()]
        random.shuffle(funcs)
        results = []
        
        for func, svc, _ in funcs:
            if tag and svc in (WaifuIm, WaifuPics, NekosBest, NSFWBot, PicRe, PurrBot):
                continue
            result = await cls._call_Random_func(func, tag, limit)
            if not result or (isinstance(result, dict) and "error" in result):
                continue
            if isinstance(result, list):
                valid_items = [
                    item for item in result
                    if not (isinstance(item, dict) and "error" in item)
                ]
                results.extend(valid_items[:max(0, limit - len(results))])
            else:
                results.append(result)
            if len(results) >= limit:
                break
    
        return results if limit > 1 else (results[0] if results else None)

    @classmethod
    async def get_random_sfw_gif(cls, tag: Optional[str] = None, limit: int = 1) -> Optional[Union[str, List[str]]]:
        """
        Filter for SFW GIF
        """
        funcs = [(f, svc, _) for f, svc, _ in cls.fetch_functions 
                 if svc == PurrBot and 'gif' in f.__name__ and 'nsfw' not in f.__name__]
        random.shuffle(funcs)
        for func, svc, _ in funcs:
            if tag and svc in (WaifuIm, WaifuPics, NekosBest, NSFWBot, PicRe, PurrBot):
                continue
            result = await cls._call_Random_func(func, tag, limit)
            if result:
                return result
        return None

    @classmethod
    async def get_random_nsfw_gif(cls, tag: Optional[str] = None, limit: int = 1) -> Optional[Union[str, List[str]]]:
        """
        Filter for NSFW GIF
        """
        funcs = [(f, svc, _) for f, svc, _ in cls.fetch_functions 
                 if svc == PurrBot and 'gif' in f.__name__ and 'nsfw' in f.__name__]
        random.shuffle(funcs)
        for func, svc, _ in funcs:
            if tag and svc in (WaifuIm, WaifuPics, NekosBest, NSFWBot, PicRe, PurrBot):
                continue
            result = await cls._call_Random_func(func, tag, limit)
            if result:
                return result
        return None
