# 获取哔哩哔哩直播的真实流媒体地址，默认最高画质。
# 参考 biliup 项目：使用 WBI 签名 + getInfoByRoom API。
import hashlib
import time
import urllib.parse
from functools import reduce

import requests

API_BASE = "https://api.live.bilibili.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


# ---- WBI 签名 ----

_MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]


def _get_mixin_key(raw: str) -> str:
    return reduce(lambda s, i: s + raw[i], _MIXIN_KEY_ENC_TAB, "")[:32]


def _fetch_wbi_keys(session: requests.Session) -> tuple:
    """从 nav 接口获取 img_key 和 sub_key。"""
    resp = session.get("https://api.bilibili.com/x/web-interface/nav",
                       headers={"User-Agent": UA}, timeout=10)
    data = resp.json()["data"]
    img_url = data["wbi_img"]["img_url"]
    sub_url = data["wbi_img"]["sub_url"]
    img_key = img_url.rsplit("/", 1)[-1].split(".")[0]
    sub_key = sub_url.rsplit("/", 1)[-1].split(".")[0]
    return img_key, sub_key


def sign_params(params: dict, img_key: str, sub_key: str) -> dict:
    """对参数字典进行 WBI 签名，添加 w_rid 和 wts。"""
    mixin = _get_mixin_key(img_key + sub_key)
    params = dict(sorted(params.items()))
    params["wts"] = str(int(time.time()))
    query = urllib.parse.urlencode(params)
    params["w_rid"] = hashlib.md5((query + mixin).encode()).hexdigest()
    return params


# ---- Bilibili API ----

class BiliBili:

    def __init__(self, rid):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": UA, "Referer": "https://live.bilibili.com"})

        # 获取 WBI 签名密钥
        self._img_key, self._sub_key = _fetch_wbi_keys(self._session)

        # 获取房间信息
        params = sign_params({"room_id": str(rid), "web_location": "444.8"},
                             self._img_key, self._sub_key)
        resp = self._session.get(f"{API_BASE}/xlive/web-room/v1/index/getInfoByRoom",
                                 params=params, timeout=10).json()

        if resp["code"] != 0:
            raise Exception(resp.get("message", "房间不存在"))

        room = resp["data"]["room_info"]
        if room["live_status"] != 1:
            raise Exception("未开播")

        self.room_id = room["room_id"]
        self.title = room["title"]
        self.uid = room["uid"]

    def get_real_url(self, qn: int = 10000) -> dict:
        """返回所有可用的 HLS (m3u8) 流地址。qn: 150高清 250超清 400蓝光 10000原画。"""
        params = sign_params({
            "room_id": str(self.room_id),
            "qn": str(qn),
            "platform": "html5",
            "protocol": "0,1",
            "format": "0,1,2",
            "codec": "0",
            "dolby": "5",
            "web_location": "444.8",
        }, self._img_key, self._sub_key)

        resp = self._session.get(
            f"{API_BASE}/xlive/web-room/v2/index/getRoomPlayInfo",
            params=params, timeout=10).json()

        if resp["code"] != 0:
            raise Exception(resp.get("message", "获取播放信息失败"))

        streams = resp["data"]["playurl_info"]["playurl"]["stream"]
        result = {}

        for stream in streams:
            for fmt in stream.get("format", []):
                format_name = fmt.get("format_name", "")
                if format_name != "ts":
                    continue
                for codec in fmt.get("codec", []):
                    base = codec.get("base_url", "")
                    current_qn = codec.get("current_qn", qn)
                    for i, info in enumerate(codec.get("url_info", [])):
                        host = info["host"]
                        extra = info["extra"]
                        label = f"线路{i + 1}_{current_qn}"
                        result[label] = f"{host}{base}{extra}"
                break  # 只取第一种格式 (ts=HLS)

        return result


def get_real_url(rid, qn=10000):
    try:
        bb = BiliBili(rid)
        return bb.get_real_url(qn)
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    rid = input("输入B站直播间号：\n").strip()
    urls = get_real_url(rid)
    for k, v in urls.items():
        print(f"{k}: {v}")
