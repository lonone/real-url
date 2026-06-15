# 虎牙直播源获取（biliup 式 URL 签名，extended wsTime）
#   python huya.py              # 输出 FLV 直播源
#   python huya.py --hls        # 输出 HLS 直播源（首次有效）
import json
import re
import time
import random
import base64
import hashlib
from urllib.parse import parse_qs, urlencode

import requests

MOBILE_UA = "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36"


def build_url(room_id, fmt="flv"):
    """
    生成虎牙直播流地址，wsTime 延长至 12 小时（URL 可复用）。
    fmt: "flv" 或 "hls"。推荐 FLV（播放器断线会自动重连同一 URL）。
    """
    html = requests.get("https://m.huya.com/" + str(room_id),
                        headers={"User-Agent": MOBILE_UA}, timeout=10).text

    m = re.findall(r"<script>\s*window\.HNF_GLOBAL_INIT\s*=\s*(.*?)\s*</script>", html)
    if not m:
        raise ValueError("Room not found or page structure changed")
    info = json.loads(m[0])
    if "roomInfo" not in info:
        raise ValueError("Room not found")

    ts = info["roomInfo"]["tLiveInfo"]["tLiveStreamInfo"]
    if info["roomInfo"]["eLiveStatus"] != 2:
        raise ValueError("Room not live")

    # 选最优 CDN（HS 优先，TX 备用），跳过不可用线路
    best = None
    for s in ts["vStreamInfo"]["value"]:
        if s.get("lFreeFlag", 0) >= 2:
            continue
        if s["sCdnType"] in ("HY", "HUYA", "HYZJ"):
            continue
        if s["sCdnType"] == "HS":
            best = s
            break
    if best is None:
        for s in ts["vStreamInfo"]["value"]:
            if s.get("lFreeFlag", 0) < 2:
                best = s
                break
    if best is None:
        raise ValueError("No available CDN lines")

    # 选择格式
    if fmt == "flv":
        anti = best.get("sFlvAntiCode", "")
        suffix = best.get("sFlvUrlSuffix", "flv")
        base_url = best.get("sFlvUrl", "")
    else:
        anti = best.get("sHlsAntiCode", "")
        suffix = best.get("sHlsUrlSuffix", "m3u8")
        base_url = best.get("sHlsUrl", "")

    if not anti or not base_url:
        raise ValueError("No %s stream available for CDN %s" % (fmt, best["sCdnType"]))

    # 重组签名：延长 wsTime 到未来 12 小时 → URL 可复用
    q = dict(parse_qs(anti))
    uid = random.randint(1400000000000, 1499999999999)
    wsTime = "%x" % (int(time.time()) + 12 * 3600)
    seqid = uid + int(time.time() * 1000)
    ctype = q.get("ctype", ["tars_mobile"])[0]
    t_val = q.get("t", ["103"])[0]
    fs_val = q.get("fs", ["bgct"])[0]
    fm_raw = q.get("fm", [""])[0]

    fm_tpl = base64.b64decode(fm_raw).decode("utf-8")
    ss = hashlib.md5(("%d|%s|%s" % (seqid, ctype, t_val)).encode()).hexdigest()
    fm_filled = fm_tpl.replace("$0", str(uid)).replace("$1", best["sStreamName"]).replace("$2", ss).replace("$3", wsTime)
    wsSecret = hashlib.md5(fm_filled.encode()).hexdigest()

    params = {
        "wsSecret": wsSecret,
        "wsTime": wsTime,
        "seqid": str(seqid),
        "ctype": ctype,
        "ver": "1",
        "fs": fs_val,
        "t": t_val,
    }

    return "%s/%s.%s?%s" % (base_url, best["sStreamName"], suffix, urlencode(params))


if __name__ == "__main__":
    import sys

    rid = input("Enter Huya room ID: ").strip()
    use_hls = "--hls" in sys.argv

    try:
        url = build_url(rid, "hls" if use_hls else "flv")
        cdn = "HS"  # we always pick HS first
        if use_hls:
            print("HLS (m3u8) – 仅首次请求有效，播放器刷新会断流")
        else:
            print("FLV – URL 12 小时内可复用，播放器断线自动重连即可")
        print()
        print(url)
    except Exception as e:
        print("Error: %s" % e)
