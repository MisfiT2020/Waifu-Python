from waifu_python import *

class APIRegistryCMD:
    _apis = {}
    _tag_handlers = {}

    @classmethod
    def register(cls, name, sfw_func=None, nsfw_func=None, tags_func=None):
        if sfw_func is None and nsfw_func is not None:
            def safe_wrapper(*args, **kwargs):
                print(f"Warning: API '{name}' does not have a dedicated SFW function. Using NSFW function instead.")
                return nsfw_func(*args, **kwargs)
            sfw_func = safe_wrapper
        if sfw_func is None:
            raise ValueError(f"APIRegistryCMD: You must provide at least one function for API '{name}'.")
        cls._apis[name] = {
            'sfw': sfw_func,
            'nsfw': nsfw_func or sfw_func  
        }
        if tags_func:
            cls._tag_handlers[name] = tags_func

    @classmethod
    def get_api(cls, name):
        return cls._apis.get(name)

    @classmethod
    def get_tag_handler(cls, name):
        return cls._tag_handlers.get(name)
    
    @classmethod
    def get_all_api_names(cls):
        """Return a list of all registered API names."""
        return list(cls._apis.keys())
    
    @classmethod
    def get_all_api_info(cls):
        info_list = []
        for name, funcs in cls._apis.items():
            sfw_func = funcs.get("sfw")
            nsfw_func = funcs.get("nsfw")
    
            if sfw_func.__name__.lower() in {"fetch_images", "get_random"}:
                avail = "ambiguous"
            elif sfw_func.__name__.lower() == "safe_wrapper":
                avail = "nsfw"
            elif nsfw_func is not sfw_func:
                avail = "both"
            else:
                avail = "sfw"
            
            info_list.append((name, avail))
        return info_list


          # AI Boards

APIRegistryCMD.register(
    name="aibooru",
    sfw_func=Aibooru.fetch_sfw_images,
    nsfw_func=Aibooru.fetch_nsfw_images
)

          # Boards

APIRegistryCMD.register(
    name="danbooru",
    sfw_func=Danbooru.fetch_sfw_images,
    nsfw_func=Danbooru.fetch_nsfw_images,

)

APIRegistryCMD.register(
    name="safebooru",
    sfw_func=Safebooru.fetch_images,
)

APIRegistryCMD.register(
    name="gelbooru",
    sfw_func=Gelbooru.fetch_images,
)

      # Galleries

APIRegistryCMD.register(
    name="kemono",
    nsfw_func=KemonoParty.fetch_nsfw_images
)


APIRegistryCMD.register(
    name="konachan",
    sfw_func=Konachan.fetch_sfw_images,
    nsfw_func=Konachan.fetch_nsfw_images
)

APIRegistryCMD.register(
    name="nekosbest",
    sfw_func=NekosBest.fetch_sfw_images,
    tags_func=NekosBest.get_tags
)

APIRegistryCMD.register(
    name="nsfwbot",
    sfw_func=NSFWBot.fetch_sfw_images,
    nsfw_func=NSFWBot.fetch_nsfw_images,
    tags_func=NSFWBot.get_tags
)


APIRegistryCMD.register(
    name="picsre",
    sfw_func=PicRe.fetch_sfw_images,
    tags_func=PicRe.get_tags
)

APIRegistryCMD.register(
    name="purrbot",
    sfw_func=PurrBot.fetch_purrbot_sfw,
    nsfw_func=PurrBot.fetch_nsfw_gif,
    tags_func=PurrBot.get_tags
)

APIRegistryCMD.register(
    name="rule34",
    nsfw_func=Rule34.fetch_images
    )

APIRegistryCMD.register(
    name="waifuim",
    sfw_func=WaifuIm.fetch_sfw_images,
    nsfw_func=WaifuIm.fetch_nsfw_images,
    tags_func=WaifuIm.get_tags
)

APIRegistryCMD.register(
    name="waifupics",
    sfw_func=WaifuPics.fetch_sfw_images,
    nsfw_func=WaifuPics.fetch_nsfw_images,
    tags_func=WaifuPics.get_tags
)

APIRegistryCMD.register(
    name="sankaku",
    sfw_func=Sankaku.fetch_sfw_images,
    nsfw_func=Sankaku.fetch_nsfw_images
)

APIRegistryCMD.register(
    name="yandere",
    nsfw_func=Yandere.fetch_images,
)

APIRegistryCMD.register(
    name="zerochan",
    sfw_func=Zerochan.fetch_sfw_images,
)

APIRegistryCMD.register(
    name="tbib",
    sfw_func=Tbib.fetch_sfw_images,
    nsfw_func=Tbib.fetch_nsfw_images,
)

APIRegistryCMD.register(
    name="hiji",
    sfw_func=Hijiribe.fetch_sfw_images,
    nsfw_func=Hijiribe.fetch_nsfw_images,
)

          # Pixiv

APIRegistryCMD.register(
    name="pixiv",
    nsfw_func=Pixiv.fetch_images
)

          # Random

APIRegistryCMD.register(
    name="random",
    sfw_func=RandomWaifu.get_random_sfw_image,
    nsfw_func=RandomWaifu.get_random_nsfw_image
)

APIRegistryCMD.register(
    name="random-nsfw",
    nsfw_func=RandomWaifu.get_random_nsfw_image
)

APIRegistryCMD.register(
    name="random-sfw",
    sfw_func=RandomWaifu.get_random_sfw_image
)

APIRegistryCMD.register(
    name="random-gif",
    sfw_func=RandomWaifu.get_random_sfw_gif
)

APIRegistryCMD.register(
    name="random-ngif",
    nsfw_func=RandomWaifu.get_random_nsfw_gif
)


       # Misc - Iwara
APIRegistryCMD.register(
    name="iwara",
    nsfw_func=Iwara.iwara_fetch
)

APIRegistryCMD.register(
    name="iwara-random",
    nsfw_func=Iwara.fetch_random
)