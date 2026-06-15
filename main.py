"""
Unified entry point for real-url.
Interactive mode: select platform, enter room ID, get stream URL.
"""

import sys


def get_real_url(platform, identifier):
    """Route to the right platform module."""
    if platform == "bilibili":
        import bilibili
        return bilibili.get_real_url(identifier)
    elif platform == "douyin":
        import douyin
        return douyin.get_real_url(identifier)
    elif platform == "douyu":
        import douyu
        return douyu.get_real_url(identifier)
    elif platform == "huya":
        import huya
        try:
            return {"flv": huya.build_url(identifier, "flv")}
        except Exception as e:
            return {"error": str(e)}
    elif platform == "tiktok":
        import tiktok
        return tiktok.get_real_url(identifier)
    else:
        return {"error": f"Unknown platform: {platform}"}


PLATFORMS = [
    ("bilibili", "Bilibili (live.bilibili.com)"),
    ("douyin",   "Douyin (live.douyin.com)"),
    ("douyu",    "Douyu (www.douyu.com)"),
    ("huya",     "Huya (www.huya.com)"),
    ("tiktok",   "TikTok (tiktok.com/@user)"),
]


def main():
    print("Select platform:")
    for i, (_, desc) in enumerate(PLATFORMS, 1):
        print(f"  {i}. {desc}")

    try:
        choice = int(input("\nEnter number: ").strip())
        if choice < 1 or choice > len(PLATFORMS):
            raise ValueError
    except ValueError:
        print("Invalid selection")
        sys.exit(1)

    platform, _ = PLATFORMS[choice - 1]
    identifier = input("Enter room ID or URL: ").strip()
    if not identifier:
        print("Empty input")
        sys.exit(1)

    result = get_real_url(platform, identifier)
    print()
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    for key, value in result.items():
        print(f"  {key}")
        print(f"    {value}")
    print()


if __name__ == "__main__":
    main()
