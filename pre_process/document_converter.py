import os
import json
import base64
import hmac
import hashlib
import requests
import html2text
import subprocess
from email.utils import formatdate
from urllib.parse import urlparse
from pdf2image import convert_from_path
from PIL import Image


class DocumentProcessor:
    """文档处理器，支持图片、PDF、Word、HTML转Markdown"""
    
    def __init__(self):
        self.config = {
            'APPID': "b97bb794",
            'API_KEY': "c87bad1f164b70337becc4d833246d17", 
            'API_SECRET': "Y2ExMGViM2RjMjdjNmZhNjkyNjZkZDhi",
            'HOST': "api.xf-yun.com",
            'REQUEST_LINE': "POST /v1/private/se75ocrbm HTTP/1.1",
            'URL_PATH': "/v1/private/se75ocrbm"
        }
        
    def process(self, input_path, output_dir="outputs"):
        """
        统一处理入口
        input_path: 输入文件路径或URL
        output_dir: 输出目录
        返回: 输出文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if input_path.startswith(('http://', 'https://')):
            return self._process_url(input_path, output_dir)
        
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
            
        name, ext = os.path.splitext(os.path.basename(input_path))
        output_path = os.path.join(output_dir, f"{name}_output.md")
        
        if os.path.exists(output_path):
            os.remove(output_path)
            
        if ext.lower() in ['.jpg', '.png']:
            self._process_image(input_path, output_path)
        elif ext.lower() == '.pdf':
            self._process_pdf(input_path, output_path, output_dir)
        elif ext.lower() == '.docx':
            self._process_docx(input_path, output_path)
        elif ext.lower() in ['.html', '.htm']:
            self._process_html_file(input_path, output_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")
            
        return output_path
    
    def _process_url(self, url, output_dir):
        """处理URL"""
        parsed_url = urlparse(url)
        name = parsed_url.netloc.replace('.', '_')
        output_path = os.path.join(output_dir, f"{name}_output.md")
        
        if os.path.exists(output_path):
            os.remove(output_path)
            
        self._process_html(url, output_path)
        return output_path
    
    def _process_image(self, image_path, output_path, page_num=1):
        """处理图片OCR"""
            
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        auth = self._get_authorization(date_str)
        
        url = f"https://cbm01.cn-huabei-1.xf-yun.com{self.config['URL_PATH']}" \
              f"?authorization={auth}&host=api.xf-yun.com&date={requests.utils.quote(date_str)}"
        
        body = self._build_body(image_path)
        response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(body))
        
        if response.status_code != 200:
            raise Exception(f"OCR请求失败: {response.status_code} {response.text}")
            
        result = response.json()
        if result.get("header", {}).get("code", -1) != 0:
            raise Exception(f"OCR识别失败: {result['header']}")
            
        # 解析结果
        text = result["payload"]["result"].get("text", "")
        if not text:
            return
            
        try:
            decoded_text = base64.b64decode(text).decode("utf-8")
            parsed_json = json.loads(decoded_text)
        except Exception as e:
            print(f"解码失败: {e}")
            return
            
        # 提取图片和生成markdown
        base_name = os.path.splitext(os.path.basename(output_path))[0]
        image_refs = {}
        
        if parsed_json and os.path.exists(image_path):
            page_image = Image.open(image_path)
            image_refs = self._extract_and_save_images(parsed_json, page_image, page_num, base_name)
            
        # 生成markdown内容
        markdown_doc = ""
        for item in parsed_json.get("document", []):
            if item.get("name") == "markdown":
                markdown_doc = item.get("value", "")
                break
                
        if markdown_doc:
            markdown_doc = markdown_doc.replace("\\n", "\n")
            markdown_doc = self._insert_images_to_markdown(markdown_doc, image_refs, parsed_json)
            
            with open(output_path, "a", encoding="utf-8") as f:
                f.write(markdown_doc + "\n\n")
    
    def _process_pdf(self, pdf_path, output_path, output_dir):
        """处理PDF文件"""
        pages = convert_from_path(pdf_path, dpi=300)
        for i, page in enumerate(pages):
            temp_path = os.path.join(output_dir, f"temp_page_{i}.png")
            page.save(temp_path, "PNG")
            try:
                self._process_image(temp_path, output_path, page_num=i+1)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
    
    def _process_docx(self, docx_path, output_path):
        """处理Word文档"""
        if not self._check_pandoc_installed():
            raise Exception("未检测到pandoc，请先安装：conda install -c conda-forge pandoc")
            
        doc_basename = os.path.splitext(os.path.basename(docx_path))[0]
        media_output_dir = f"outputs/media_{doc_basename}"
        
        try:
            command = [
                "pandoc", docx_path, "-f", "docx", "-t", "markdown",
                "-o", output_path, "--wrap=none", f"--extract-media={media_output_dir}"
            ]
            subprocess.run(command, check=True)
        except Exception as e:
            raise Exception(f"Pandoc转换失败: {e}")
    
    def _process_html_file(self, html_path, output_path):
        """处理HTML文件"""
        html_content = self._read_html_file(html_path)
        self._convert_html_to_markdown(html_content, output_path)
    
    def _process_html(self, input_source, output_path):
        """处理HTML内容（文件或URL）"""
        if input_source.startswith(('http://', 'https://')):
            html_content = self._fetch_from_url(input_source)
        else:
            html_content = self._read_html_file(input_source)
        self._convert_html_to_markdown(html_content, output_path)
    
    def _convert_html_to_markdown(self, html_content, output_path):
        """HTML转Markdown"""
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = False  
        converter.body_width = 0
        converter.unicode_snob = True
        
        markdown_content = converter.handle(html_content).strip()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
    
    # 辅助方法
    def _get_authorization(self, date_str):
        """生成鉴权信息"""
        signature_origin = f"host: {self.config['HOST']}\ndate: {date_str}\n{self.config['REQUEST_LINE']}"
        signature_sha = hmac.new(
            self.config['API_SECRET'].encode("utf-8"),
            signature_origin.encode("utf-8"),
            hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode("utf-8")
        
        authorization_origin = (
            f'api_key="{self.config["API_KEY"]}",algorithm="hmac-sha256",'
            f'headers="host date request-line",signature="{signature}"'
        )
        return base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
    
    def _build_body(self, image_path):
        """构造请求体"""
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")
            
        return {
            "header": {"app_id": self.config['APPID'], "status": 0},
            "parameter": {
                "ocr": {
                    "result_option": "normal",
                    "result_format": "json,markdown", 
                    "output_type": "one_shot",
                    "exif_option": "0",
                    "markdown_element_option": "watermark=0,page_header=0,page_footer=0,page_number=0,graph=0",
                    "sed_element_option": "watermark=0,page_header=0,page_footer=0,page_number=0,graph=0",
                    "rotation_min_angle": 5,
                    "result": {"encoding": "utf8", "compress": "raw", "format": "plain"}
                }
            },
            "payload": {
                "image": {"encoding": "jpg", "image": img_base64, "status": 0, "seq": 0}
            }
        }
    
    def _extract_and_save_images(self, parsed_json, page_image, page_num, base_name):
        """提取并保存图片"""
        images_dir = f"images_{base_name}"
        os.makedirs(images_dir, exist_ok=True)
        
        img_width, img_height = page_image.size
        image_refs = {}
        
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
                        y_pos = coord[0]["y"]
                        
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
                            
                        except Exception as e:
                            print(f"图片保存失败: {e}")
                
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        find_images(value)
            elif isinstance(obj, list):
                for item in obj:
                    find_images(item)
        
        find_images(parsed_json)
        return image_refs
    
    def _insert_images_to_markdown(self, markdown_doc, image_refs, parsed_json):
        """将图片插入到markdown中"""
        if not image_refs:
            return markdown_doc
            
        text_to_images = {}
        head_images = []
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
    
    def _check_pandoc_installed(self):
        """检查pandoc是否安装"""
        try:
            subprocess.run(["pandoc", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False
    
    def _fetch_from_url(self, url):
        """从URL获取HTML内容"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    
    def _read_html_file(self, file_path):
        """读取本地HTML文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("无法解码HTML文件")


# 便捷函数
def process_document(input_path, output_dir="outputs"):
    """
    便捷函数：处理单个文档
    input_path: 输入文件路径或URL
    output_dir: 输出目录
    返回: 输出文件路径
    """
    processor = DocumentProcessor()
    return processor.process(input_path, output_dir)