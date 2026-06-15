# 获取斗鱼直播间的真实流媒体地址，默认最高画质。
# 参考 biliup 项目：使用 getEncryption 加密密钥 API，无需 execjs。
import hashlib
import time

import requests

DOUYU_DID = "10000000000000000000000000001501"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def _md5(data: str) -> str:
    return hashlib.md5(data.encode()).hexdigest()


def _sign_stream(encrypt_key: dict, room_id: str, ts: int) -> str:
    """计算斗鱼播放接口的 auth 签名。"""
    salt = "" if encrypt_key.get("is_special") == 1 else f"{room_id}{ts}"
    secret = encrypt_key["rand_str"]
    for _ in range(encrypt_key["enc_time"]):
        secret = _md5(f"{secret}{encrypt_key['key']}")
    return _md5(f"{secret}{encrypt_key['key']}{salt}")


class DouYu:

    def __init__(self, rid):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": UA,
            "Referer": "https://www.douyu.com",
        })

        # 1. 从移动端页面获取真实 rid
        rid = self._resolve_room_id(str(rid))

        # 2. 获取直播状态
        room_info = self._get_room_info(rid)
        if room_info is None:
            raise Exception("未开播")
        self.rid = rid
        self.room_name = room_info["room_name"]

        # 3. 获取加密密钥
        self._encrypt_key = self._get_encryption()

    def _resolve_room_id(self, short_id: str) -> str:
        """从短房间号解析真实 rid。"""
        resp = self._session.get(f"https://m.douyu.com/{short_id}", timeout=10)
        text = resp.text

        import re
        m = re.search(r'"roomInfo":\{"rid":(\d+)', text)
        if m:
            return m.group(1)

        # 如果本身就是纯数字 rid
        if short_id.isdigit():
            return short_id

        raise Exception("房间号解析失败")

    def _get_room_info(self, room_id: str) -> dict | None:
        """获取直播间信息。"""
        resp = self._session.get(
            f"https://www.douyu.com/betard/{room_id}",
            headers={"Referer": "https://www.douyu.com"},
            timeout=10,
        ).json()

        room = resp.get("room")
        if room is None:
            return None
        if room.get("show_status") != 1 or room.get("videoLoop", 0) != 0:
            return None
        return room

    def _get_encryption(self) -> dict:
        """获取斗鱼白盒加密密钥。"""
        resp = self._session.get(
            "https://www.douyu.com/wgapi/livenc/liveweb/websec/getEncryption",
            params={"did": DOUYU_DID},
            timeout=10,
        ).json()

        if resp.get("error") != 0:
            raise Exception(f"获取加密密钥失败: {resp.get('msg', '')}")
        if resp.get("data") is None:
            raise Exception("加密密钥为空")

        return resp["data"]

    def get_real_url(self, cdn: str = "", rate: int = 0) -> dict:
        """
        返回直播流地址。
        cdn: 空=自动, ws-h5=主线路, tct-h5=备用线路
        rate: 0=蓝光最高, 1=流畅, 2=高清, 3=超清, 4=蓝光4M
        """
        now = int(time.time())
        auth = _sign_stream(self._encrypt_key, self.rid, now)

        form = {
            "cdn": cdn,
            "rate": str(rate),
            "ver": "Douyu_new",
            "iar": "0",
            "ive": "0",
            "rid": self.rid,
            "hevc": "0",
            "fa": "0",
            "sov": "0",
            "enc_data": self._encrypt_key["enc_data"],
            "tt": str(now),
            "did": DOUYU_DID,
            "auth": auth,
        }

        resp = self._session.post(
            f"https://www.douyu.com/lapi/live/getH5PlayV1/{self.rid}",
            data=form,
            timeout=10,
        ).json()

        error = resp.get("error", -1)
        msg = resp.get("msg", "")

        if error == 0 and resp.get("data"):
            data = resp["data"]
            key = data["rtmp_live"]
            rtmp_url = data["rtmp_url"]
            return {
                "flv": f"{rtmp_url}/{key}",
            }
        elif error == -5:
            raise Exception("主播未开播")
        elif error == 126:
            raise Exception(f"版权限制: {msg}")
        else:
            raise Exception(f"获取播放信息失败 (code={error}): {msg}")


def get_real_url(rid):
    try:
        dy = DouYu(rid)
        return dy.get_real_url()
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    rid = input("输入斗鱼直播间号：\n").strip()
    urls = get_real_url(rid)
    for k, v in urls.items():
        print(f"{k}: {v}")
