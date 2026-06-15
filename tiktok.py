# 获取 TikTok 直播的真实流媒体地址。
# 从分享链接页面提取预签名的 HLS URL。
import re
import requests

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")


class TikTok:

    def __init__(self, url):
        """
        url: TikTok 直播间分享链接 (如 https://vm.tiktok.com/xxx 或 https://www.tiktok.com/@user/live)
        """
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": UA})

        # 解析短链接
        if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
            resp = self._session.head(url, allow_redirects=True, timeout=10)
            url = resp.url

        # 提取用户名
        m = re.search(r"tiktok\.com/@([^/?]+)", url)
        self.username = m.group(1) if m else ""

        # 获取直播页面
        resp = self._session.get(url, timeout=10)
        text = resp.text

        # 提取 LiveUrl (预签名 HLS)
        m = re.search(r'"LiveUrl":"(.*?m3u8)"', text)
        if not m:
            # 尝试其他格式
            m = re.search(r'"liveUrl":"([^"]*)"', text, re.IGNORECASE)

        if m:
            self._url = m.group(1).replace("\\u002F", "/")
        else:
            raise Exception("未找到直播流地址，可能未开播或链接无效")

    @property
    def live_url(self):
        return self._url

    def get_real_url(self) -> dict:
        return {"hls": self._url}


def get_real_url(url):
    try:
        tt = TikTok(url)
        return tt.get_real_url()
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    url = input("输入 TikTok 直播链接：\n").strip()
    print(get_real_url(url))
