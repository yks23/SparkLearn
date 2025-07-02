import requests
import base64
import hashlib
import hmac
import os
import json
from datetime import datetime
from email.utils import formatdate
from pdf2image import convert_from_path
from PIL import Image

# ========== 配置(调用的是科大讯飞的通用文档（大模型）) ==========
APPID = "b97bb794"
API_KEY = "c87bad1f164b70337becc4d833246d17"
API_SECRET = "Y2ExMGViM2RjMjdjNmZhNjkyNjZkZDhi"
HOST = "cbm01.cn-huabei-1.xf-yun.com"
REQUEST_LINE = "POST /v1/private/se75ocrbm HTTP/1.1"
URL_PATH = "/v1/private/se75ocrbm"

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

# ========== 图片到md ==========
def process_image(image_path, output_md_name):
    date_str = formatdate(timeval=None, localtime=False, usegmt=True)
    auth = get_authorization(API_KEY, API_SECRET, "api.xf-yun.com", REQUEST_LINE, date_str)

    url = f"https://{HOST}{URL_PATH}" \
          f"?authorization={auth}&host=api.xf-yun.com&date={requests.utils.quote(date_str)}"

    body = build_body(APPID, image_path)

    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(body))

    if response.status_code != 200:
        print("❌ 请求失败:", response.status_code, response.text)
        return

    result = response.json()
    if result.get("header", {}).get("code", -1) != 0:
        print("❌ 识别失败:", result["header"])
        return

    text = result["payload"]["result"].get("text", "")
    if text:
        try:
            decoded_text = base64.b64decode(text).decode("utf-8")
            parsed_json = json.loads(decoded_text)
        except Exception as e:
            print(f"❌ 解码失败: {e}")
            parsed_json = {}
            decoded_text = "[无法解码的内容]"
    else:
        parsed_json = {}
        decoded_text = "[空结果]"

    print(f"\n✅ {os.path.basename(image_path)} 识别成功，输出内容：\n")
    print(decoded_text)

    markdown_doc = ""
    for item in parsed_json.get("document", []):
        if item.get("name") == "markdown":
            markdown_doc = item.get("value", "")
            break

    if markdown_doc:
        markdown_doc = markdown_doc.replace("\\n", "\n")
        with open(output_md_name, "a", encoding="utf-8") as f:
            f.write(markdown_doc + "\n\n")
        print(f"✅ 写入 Markdown 文件: {output_md_name}")
    else:
        print("⚠️ 未找到 markdown 内容")

import subprocess

# word to md，调用的是pandoc，需要安装pandoc
def check_pandoc_installed():
    try:
        subprocess.run(["pandoc", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

def process_docx(docx_path, output_md_name):
    if not check_pandoc_installed():
        print("❌ 未检测到 pandoc，请先安装：conda install -c conda-forge pandoc")
        return

    doc_basename = os.path.splitext(os.path.basename(docx_path))[0]
    media_output_dir = f"media_{doc_basename}"
    try:
        command = [
            "pandoc",
            docx_path,
            "-f", "docx",
            "-t", "markdown",
            "-o", output_md_name,
            "--wrap=none",
            f"--extract-media={media_output_dir}"  # 可选：将图片资源提取为本地文件夹
        ]
        subprocess.run(command, check=True)
        print(f"✅ 成功使用 Pandoc 转换 Word 文件为 Markdown：{output_md_name}")
    except Exception as e:
        print(f"❌ Pandoc 转换失败: {e}")


# ========== 输入路径判断 + 调用 ==========
def process_input(input_path):
    if not os.path.exists(input_path):
        print("❌ 输入文件不存在")
        return

    name, ext = os.path.splitext(os.path.basename(input_path))
    output_md_name = f"{name}_output.md"

    if os.path.exists(output_md_name):
        os.remove(output_md_name)

    if ext.lower() in ['.jpg', '.png']:
        process_image(input_path, output_md_name)

    elif ext.lower() == '.pdf':
        print(f"📄 正在将 PDF 拆分为图片: {input_path}")
        pages = convert_from_path(input_path, dpi=300)
        for i, page in enumerate(pages):
            temp_path = f"temp_page_{i}.png"
            page.save(temp_path, "PNG")
            process_image(temp_path, output_md_name)
            os.remove(temp_path)

    elif ext.lower() == '.docx':
        print(f"📄 正在处理 Word 文件: {input_path}")
        process_docx(input_path, output_md_name)

    elif ext.lower() == '.doc':
        print(f"📄 请在WPS或office中手动打开并另存为docx文件！{input_path}")
        return

    else:
        print("❌ 不支持的文件类型，请输入 .jpg/.png/.pdf 文件")
        return
    

    print(f"\n✅ 最终 Markdown 文件已保存至: {output_md_name}")

# ========== 启动 ==========
if __name__ == "__main__":
    inputfile="./example/MaoGai.docx"
    input_path = inputfile
    process_input(input_path)
