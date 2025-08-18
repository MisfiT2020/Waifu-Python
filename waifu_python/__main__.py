import sys
import asyncio
import secrets
from dotenv import load_dotenv  

load_dotenv()                   

from .CLI.parser import create_parser
from .CLI.commands import handle_api_command, handle_tags_command
from .API.base import APIRegistryCMD
from .API.pixiv_auth import login, refresh

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.list:
        info = APIRegistryCMD.get_all_api_info()
        print("Available APIs:")
        for name, availability in info:
            print(f" - {name.ljust(15)} [{availability.upper()}]")
        sys.exit(0)
    
    if not args.api:
        parser.print_help()
        sys.exit(0)

    if args.api.lower() == "pixiv":
        if args.login:
            login()
            sys.exit(0)
        elif args.refresh:
            refresh(args.refresh)
            sys.exit(0)

    try:
        args.api = args.api.lower()  
        
        api = APIRegistryCMD.get_api(args.api)
        if api is None:
            print(f"Error: API '{args.api}' is not registered.")
            sys.exit(1)

        if args.tags:
            tags = asyncio.run(handle_tags_command(args.api))
            print(f"{args.api.capitalize()} tags: {tags}")
            sys.exit(0)

        if args.api == "random" and not args.sfw and not args.nsfw:
            nsfw_selected = bool(secrets.randbits(1))
            data = asyncio.run(handle_api_command(args.api, nsfw_selected, args.query, args.limit))
            flag = "nsfw" if nsfw_selected else "sfw"
            print(f"\n[{flag.upper()}] Results from {args.api.capitalize()}:")
            for item in (data if isinstance(data, list) else [data]):
                print(f" - {item}")
            sys.exit(0)

        if api['sfw'].__name__.lower() == "safe_wrapper":
            nsfw = True
        else:
            nsfw = args.nsfw  
        if args.sfw:
            nsfw = False
    
        result = asyncio.run(handle_api_command(args.api, nsfw, args.query, args.limit))
        
        if isinstance(result, tuple):
            data, flag = result
        else:
            data = result
            flag = "nsfw" if nsfw else "sfw"
        
        print(f"\n[{flag.upper()}] Results from {args.api.capitalize()}:")
        for item in (data if isinstance(data, list) else [data]):
            print(f" - {item}")
    
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
