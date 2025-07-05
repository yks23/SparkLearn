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
import html2text
from urllib.parse import urlparse

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

# ========== 提取并保存图片，返回图片引用信息 ==========
def extract_and_save_images(parsed_json, page_image, page_num, base_name):
    images_dir = f"images_{base_name}"
    os.makedirs(images_dir, exist_ok=True)
    
    img_width, img_height = page_image.size
    image_refs = {}
    
    # ========== 提取图片说明文字 ==========
    def extract_text_from_note(content):
        if isinstance(content, list):
            for item in content:
                result = extract_text_from_note(item)
                if result:
                    return result
        elif isinstance(content, dict):
            if "text" in content:
                return content["text"][0] if isinstance(content["text"], list) else str(content["text"])
            if "content" in content:
                return extract_text_from_note(content["content"])
        return ""

    def find_images(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "graph" and "note" in obj:
                coord = obj.get("coord", [])
                if len(coord) >= 2:
                    y_pos = coord[0]["y"]  # 使用y坐标确定文档位置
                    
                    title = ""
                    for note in obj["note"]:
                        if "content" in note:
                            title = extract_text_from_note(note["content"])
                            break
                    
                    if not title:
                        title = f"图片_{page_num}_{len(image_refs)+1}"
                    
                    try:
                        x_coords = [point["x"] for point in coord]
                        y_coords = [point["y"] for point in coord]

                        left = max(0, min(x_coords))
                        right = min(img_width, max(x_coords))
                        top = max(0, min(y_coords))
                        bottom = min(img_height, max(y_coords))
                        
                        cropped = page_image.crop((left, top, right, bottom))
                        
                        img_filename = f"page_{page_num}_img_{len(image_refs)+1}.png"
                        img_path = os.path.join(images_dir, img_filename)
                        cropped.save(img_path)
                        
                        img_ref = f"\n\n![{title}](images_{base_name}/{img_filename})\n\n"
                        image_refs[y_pos] = img_ref
                        
                        print(f"✅ 保存图片: {img_filename}")
                        
                    except Exception as e:
                        print(f"❌ 图片保存失败: {e}")
            
            # 递归查找
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    find_images(value)
        elif isinstance(obj, list):
            for item in obj:
                find_images(item)
    
    find_images(parsed_json)
    return image_refs

# ========== 根据坐标插入图片 ==========
def insert_images_to_markdown(markdown_doc, image_refs, parsed_json):
    if not image_refs:
        return markdown_doc
    
    text_to_images = {}
    head_images = []  # 用于存储开头无文本时出现的图片
    last_text = None
    has_seen_text = False

    def collect_text_image_pairs(obj):
        nonlocal last_text, has_seen_text

        if isinstance(obj, dict):
            if obj.get("type") in ["paragraph", "textline"] and "text" in obj:
                texts = obj.get("text", [])
                text_content = texts[0] if isinstance(texts, list) and texts else ""
                if text_content.strip():
                    last_text = text_content.strip()
                    has_seen_text = True

            elif obj.get("type") == "graph" and obj.get("coord"):
                img_y = obj["coord"][0]["y"]
                if img_y in image_refs:
                    img_ref = image_refs[img_y]
                    if has_seen_text and last_text:
                        text_to_images.setdefault(last_text, []).append(img_ref)
                    else:
                        head_images.append(img_ref)

            for value in obj.values():
                collect_text_image_pairs(value)

        elif isinstance(obj, list):
            for item in obj:
                collect_text_image_pairs(item)

    collect_text_image_pairs(parsed_json)

    result = markdown_doc
    for text, img_list in text_to_images.items():
        if text in result:
            all_imgs = "".join(img_list)
            result = result.replace(text, text + all_imgs, 1)

    if head_images:
        prefix_imgs = "".join(head_images)
        result = prefix_imgs + "\n\n" + result

    return result


# ========== 图片到md ==========
def process_image(image_path, output_md_name, page_num=1):
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

    base_name = os.path.splitext(os.path.basename(output_md_name))[0]
    image_refs = {}

    if parsed_json and os.path.exists(image_path):
        from PIL import Image
        page_image = Image.open(image_path)
        image_refs = extract_and_save_images(parsed_json, page_image, page_num, base_name)

    markdown_doc = ""
    for item in parsed_json.get("document", []):
        if item.get("name") == "markdown":
            markdown_doc = item.get("value", "")
            break

    if markdown_doc:
        markdown_doc = markdown_doc.replace("\\n", "\n")
        markdown_doc = insert_images_to_markdown(markdown_doc, image_refs, parsed_json)

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
    media_output_dir = f"outputs/media_{doc_basename}"
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

# ========== HTML到md ==========
def process_html(input_source, output_md_name):
    """处理HTML文件或URL转换为Markdown"""
    try:
        # 判断是URL还是文件路径
        if input_source.startswith(('http://', 'https://')):
            html_content = fetch_from_url(input_source)
        else:
            html_content = read_html_file(input_source)
        
        # 配置转换器
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = False
        converter.body_width = 0
        converter.unicode_snob = True
        
        markdown_content = converter.handle(html_content).strip()
        
        with open(output_md_name, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✅ HTML转换完成: {output_md_name}")
        
    except Exception as e:
        print(f"❌ HTML转换失败: {e}")

def fetch_from_url(url):
    """从URL获取HTML内容"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text

def read_html_file(file_path):
    """读取本地HTML文件"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("无法解码HTML文件")

# ========== 输入路径判断 + 调用 ==========
def process_input(input_path,output_path='./outputs'):
    os.makedirs(output_path, exist_ok=True)

    if input_path.startswith(('http://', 'https://')):
        from urllib.parse import urlparse
        parsed_url = urlparse(input_path)
        name = parsed_url.netloc.replace('.', '_')
        output_md_name = f"outputs/{name}_output.md"
        if os.path.exists(output_md_name):
            os.remove(output_md_name)
        print(f"🌐 正在处理 URL: {input_path}")
        process_html(input_path, output_md_name)
        print(f"\n✅ 最终 Markdown 文件已保存至: {output_md_name}")
        return

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
            temp_path = f"outputs/temp_page_{i}.png"
            page.save(temp_path, "PNG")
            process_image(temp_path, output_md_name, page_num=i+1)
            os.remove(temp_path)

    elif ext.lower() == '.docx':
        print(f"📄 正在处理 Word 文件: {input_path}")
        process_docx(input_path, output_md_name)

    elif ext.lower() == '.doc':
        print(f"📄 请在WPS或office中手动打开并另存为docx文件！{input_path}")
        return
    
    elif ext.lower() in ['.html', '.htm']:
        print(f"🌐 正在处理 HTML 文件: {input_path}")
        process_html(input_path, output_md_name)

    else:
        print("❌ 不支持的文件类型，请输入 .jpg/.png/.pdf/.docx/.html/.htm 文件或URL")
        return
    

    print(f"\n✅ 最终 Markdown 文件已保存至: {output_md_name}")


# ========== 启动 ==========
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("使用方法: python processtext.py <文件路径或URL>")
        print("支持格式: .jpg, .png, .pdf, .docx, .html, .htm 或 URL")
        print("示例: python processtext.py example.pdf")
        print("示例: python processtext.py https://example.com")
        sys.exit(1)
    
    input_path = sys.argv[1]
    process_input(input_path)