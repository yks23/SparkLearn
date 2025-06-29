import time
import hmac
import hashlib
import base64
import json
import requests
from datetime import datetime
from email.utils import formatdate
from config import APIKEY, APISecret, APPID
# 配置项，请替换为你控制台获取的值
API_KEY = APIKEY
API_SECRET = APISecret
APP_ID = APPID  # 一般在 doc 中是 app_id
HOST = "ocr.xfyun.cn"  # 文档中示例 Host，实际请根据服务地址填写
URI = "/v2/ocr"       # 文档中对应的 OCR 接口路径
URL = "https://cbm01.cn-huabei-1.xf-yun.com/v1/private/se75ocrbm"

def make_auth_header(body: bytes):
    digest = "SHA-256=" + base64.b64encode(hashlib.sha256(body).digest()).decode()
    date = formatdate(timeval=None, localtime=False, usegmt=True)

    signature_origin = f"host: {HOST}\n" \
                       f"date: {date}\n" \
                       f"POST {URI} HTTP/1.1\n" \
                       f"digest: {digest}"

    signature_sha = hmac.new(
        API_SECRET.encode(), signature_origin.encode(), hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature_sha).decode()

    auth_header = (
        f'api_key="{API_KEY}", '
        f'algorithm="hmac-sha256", '
        f'headers="host date request-line digest", '
        f'signature="{signature}"'
    )
    return {
        "Content-Type": "application/json",
        "Accept": "application/json,version=1.0",
        "Host": HOST,
        "Date": date,
        "Digest": digest,
        "Authorization": auth_header,
    }

def ocr_image(image_path: str):
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    body_dict = {
        "common": {"app_id": APP_ID},
        "business": {"type": "ocr_general"},  # 根据文档改
        "data": {"image": img_b64}
    }
    body = json.dumps(body_dict).encode()

    headers = make_auth_header(body)
    resp = requests.post(URL, headers=headers, data=body)
    resp.raise_for_status()

    res = resp.json()
    if res.get("code") != 0:
        raise RuntimeError(f"OCR 调用失败, code={res.get('code')}, msg={res.get('message')}")
    # result 内容格式请根据 OCR for LLM 文档解析
    return res["data"]

if __name__ == "__main__":
  
    out = ocr_image('C:\CODE\EduSpark\kg-construction\image-4.png')
    print(json.dumps(out, indent=2, ensure_ascii=False))
