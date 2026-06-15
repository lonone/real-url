# Real-Url

## 说明


这个仓库存放的是：获取一些直播平台真实流媒体地址（直播源）和弹幕的 Python 代码实现。获取的地址经测试，均可在 PotPlayer、VLC、DPlayer(flv.js + hls.js)等播放器中播放。

>  🤘👌🤙🙏🐉👉 ：如果该项目能帮助到您，欢迎 star 和 pr；或在您的项目中标注 Real-Url 为参考来源。

目前已实现：

 **5** 个直播平台的直播源获取：斗鱼直播、虎牙直播、哔哩哔哩直播、TikTok、抖音。

 **3** 个直播平台的弹幕获取：斗鱼直播、虎牙直播、哔哩哔哩直播。

## 运行

1. 项目使用了很简单的 Python 代码，仅在 Python 3 环境运行测试。
2. 具体所需模块请查看 requirements.txt
3. 获取斗鱼和爱奇艺的直播源，需 JavaScript 环境，可使用 node.js。爱奇艺直播里有个参数是加盐的 MD5，由仓库中的 iqiyi.js 生成。


## 反馈

有直播平台失效或新增其他平台解析的，可发 [issue](https://github.com/lonone/real-url/issues/new)。

## 更新

# real-url
