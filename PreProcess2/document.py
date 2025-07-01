import base64
import json
import queue
import websocket
import threading
from datetime import datetime
from wsgiref.handlers import format_date_time
import hmac
import hashlib
from time import mktime
from urllib.parse import urlencode
import os
import subprocess

'''
    1、图片文档还原 WebAPI调用示例
    2、运行前：请先填写Appid、APIKey、APISecret 相关信息
'''
class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg



class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema
        pass


def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + requset_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u

# build websocket auth request url
def assemble_ws_auth_url(requset_url, method="GET", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    print(date)
    # date = "Thu, 12 Dec 2019 01:57:27 GMT"
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    # print(signature_origin)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    # print(authorization_origin)
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }

    return requset_url + "?" + urlencode(values)


class WebsocketDemo:

    def __init__(self, appId, apiKey, apiSecret):
        self.requestUrl = "wss://ws-api.xf-yun.com/v1/private/ma008db16"
        self.appId = appId
        self.apiSecret = apiSecret
        self.streamSeqCounter = {}
        self.queue = queue.Queue()
        self.result_type = result_type
        onOpen = lambda ws: self.__onOpen(ws)
        onMessage = lambda ws, msg: self.__onMessage(ws, msg)
        onError = lambda ws, err: self.__onFail(ws, err)
        onClose = lambda ws: self.__onClose(ws)
        self.requestUrl = assemble_ws_auth_url(self.requestUrl, api_key=apiKey, api_secret=apiSecret)
        # print("url:",self.requestUrl)
        ws = websocket.WebSocketApp(self.requestUrl, on_message=onMessage, on_error=onError, on_close=onClose,
                                    on_open=onOpen)
        self.ws = ws
        run = lambda: ws.run_forever()
        t = threading.Thread(target=run)
        t.start()

    def startSendMessage(self):
        file = open(file_path, 'rb')
        buf = file.read()
        if not buf:
            print("end-------------")

        body = {
            "header": {
                "app_id": self.appId,
                "status": 2,
            },
            "parameter": {
                "s15282f39": {
                    "category": "ch_en_public_cloud",
                    "result": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "plain"
                    }
                },
                "s5eac762f": {
                    "result_type": self.result_type,
                    "result": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "plain"
                    }
                }
            },
            "payload": {
                "test": {
                    "encoding": "png",
                    "image": str(base64.b64encode(buf), 'utf-8'),
                    "status": 3
                }
            }
        }
        paramStr = json.dumps(body)
        self.queue.put(paramStr)
        self.queue.put(4)


    def __onOpen(self, ws):
        print("onOpen")
        run = lambda: self.start()
        t = threading.Thread(target=run)
        t.start()

    def __onMessage(self, ws, message):
        print("onMessage", message)
        message = eval(message)
        if message["header"]["status"] == 1:
            text = message["payload"]["result"]["text"]
            text_de = base64.b64decode(text)

            os.makedirs("output", exist_ok=True)

            if result_type == "0":
                file = open("output/表格.xls", 'wb')
            elif result_type == "1":
                file = open("output/文档.docx",'wb')
            elif result_type == "2":
                file = open("output/PPT.pptx",'wb')
            file.write(text_de)
        pass

    def __onFail(self, ws, err):
        #print("onError", err)
        pass

    def __onClose(self, ws):
        print("***onClose***")
        pass

    def start(self):
        while True:
            frame = self.queue.get()
            if frame==4:
                return
            self.ws.send(frame)
            #print("start send message", frame)
            print("start send message...")

def convert_docx_to_md_with_pandoc(docx_path, md_path, media_dir=None):
    cmd = [
        "pandoc",
        docx_path,
        "-f", "docx",
        "-t", "markdown",
        "--atx-headers",
        "--wrap=preserve",
        "-o", md_path
    ]
    if media_dir:
        cmd.extend(["--extract-media", media_dir])

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ 转换成功：{md_path}")
    except subprocess.CalledProcessError as e:
        print("❌ 转换失败：", e)

if __name__ == '__main__':
    appId = "b97bb794"
    apiSecret = "Y2ExMGViM2RjMjdjNmZhNjkyNjZkZDhi"
    apiKey = "c87bad1f164b70337becc4d833246d17"
    file_path = "./source/CS1.jpg" # 上传图片地址
    result_type = "0" # 选择输出格式 2:ppt、1:doc、0:excel,结果将保存在output中

    demo = WebsocketDemo(appId, apiKey, apiSecret)
    demo.startSendMessage()
    # 调用
    convert_docx_to_md_with_pandoc("output/文档.docx", "output/result.md", media_dir="output/media")
