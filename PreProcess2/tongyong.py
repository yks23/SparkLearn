import requests
import base64
import hashlib
import hmac
from datetime import datetime
from email.utils import formatdate
import json
from pdf2image import convert_from_path
from PIL import Image

# ========== 配置 ==========
APPID = "b97bb794"
API_KEY = "c87bad1f164b70337becc4d833246d17"
API_SECRET = "Y2ExMGViM2RjMjdjNmZhNjkyNjZkZDhi"
HOST = "cbm01.cn-huabei-1.xf-yun.com"
REQUEST_LINE = "POST /v1/private/se75ocrbm HTTP/1.1"
URL_PATH = "/v1/private/se75ocrbm"
IMAGE_PATH = "./source/formula_text.png"  # 替换为你的图片路径


# ========== 鉴权函数 ==========
def get_authorization(api_key, api_secret, host, request_line, date_str):
    signature_origin = f"host: {host}\ndate: {date_str}\n{request_line}"
    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature_sha).decode("utf-8")

    authorization_origin = (
        f'api_key="{api_key}",algorithm="hmac-sha256",'
        f'headers="host date request-line",signature="{signature}"'
    )
    return base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")


# ========== 构造 body ==========
def build_body(app_id, image_path):
    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    return {
        "header": {
            "app_id": app_id,
            "status": 0
        },
        "parameter": {
            "ocr": {
                "result_option": "normal",
                "result_format": "json,markdown",
                "output_type": "one_shot",
                "exif_option": "0",
                "markdown_element_option": "watermark=0,page_header=0,page_footer=0,page_number=0,graph=0",
                "sed_element_option": "watermark=0,page_header=0,page_footer=0,page_number=0,graph=0",
                "rotation_min_angle": 5,
                "result": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "plain"
                }
            }
        },
        "payload": {
            "image": {
                "encoding": "jpg",
                "image": img_base64,
                "status": 0,
                "seq": 0
            }
        }
    }





# ========== 主流程 ==========
def main():
    date_str = formatdate(timeval=None, localtime=False, usegmt=True)
    auth = get_authorization(API_KEY, API_SECRET, "api.xf-yun.com", REQUEST_LINE, date_str)

    # 构造带鉴权参数的 URL（注意 host 固定写 api.xf-yun.com）
    url = f"https://{HOST}{URL_PATH}" \
          f"?authorization={auth}&host=api.xf-yun.com&date={requests.utils.quote(date_str)}"

    body = build_body(APPID, IMAGE_PATH)

    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(body))

    if response.status_code != 200:
        print("❌ 请求失败:", response.status_code, response.text)
        return

    result = response.json()
    if result.get("header", {}).get("code", -1) != 0:
        print("❌ 识别失败:", result["header"])
        return

        # 解码 base64 内容为文本
    text = result["payload"]["result"].get("text", "")
    if text:
        try:
            decoded_text = base64.b64decode(text).decode("utf-8")
            parsed_json = json.loads(decoded_text)  # 关键步骤！
        except Exception as e:
            print(f"❌ 解码失败: {e}")
            parsed_json = {}
            decoded_text = "[无法解码的内容]"
    else:
        parsed_json = {}
        decoded_text = "[空结果]"

    print("\n✅ 识别成功，输出内容：\n")
    print(decoded_text)

    # 提取 markdown 段落
    markdown_doc = ""
    for item in parsed_json.get("document", []):
        if item.get("name") == "markdown":
            markdown_doc = item.get("value", "")
            break  # 只取第一段

    if markdown_doc:
        markdown_doc = markdown_doc.replace("\\n", "\n")  # 转换换行符
        print("\n✅ 提取成功，输出内容：\n")
        print(markdown_doc)
        with open("result.md", "w", encoding="utf-8") as f:
            f.write(markdown_doc)
    else:
        print("⚠️ 未找到 markdown 内容")


if __name__ == "__main__":
    main()
