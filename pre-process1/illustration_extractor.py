import layoutparser as lp
import cv2
import json
import os
from PIL import Image
from pathlib import Path
import fitz
from datetime import datetime

class FigureTextExtractor:
    def __init__(self, confidence=0.7):
        """初始化图文提取器"""
        self.model = lp.Detectron2LayoutModel(
            config_path='lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config',
            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", confidence],
            label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
        )
    
    def extract_figures_with_positions(self, file_path, output_dir="figures"):
        """提取图片并生成位置映射"""
        Path(output_dir).mkdir(exist_ok=True)
        
        if file_path.lower().endswith('.pdf'):
            return self._extract_from_pdf(file_path, output_dir)
        else:
            return self._extract_from_image(file_path, output_dir)
    
    def _extract_from_pdf(self, pdf_path, output_dir):
        """从PDF提取"""
        pdf = fitz.open(pdf_path)
        all_figures = []
        
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            import numpy as np
            nparr = np.frombuffer(img_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            page_figures = self._extract_figures_from_image(
                image_rgb, page_num, output_dir,
                page.rect.width, page.rect.height, scale=2.0
            )
            all_figures.extend(page_figures)
        
        pdf.close()
        self._save_figure_data(all_figures, output_dir)
        return all_figures
    
    def _extract_from_image(self, image_path, output_dir):
        """从图片提取"""
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        figures = self._extract_figures_from_image(
            image_rgb, 0, output_dir,
            image.shape[1], image.shape[0], scale=1.0
        )
        
        self._save_figure_data(figures, output_dir)
        return figures
    
    def _extract_figures_from_image(self, image, page_num, output_dir, page_width, page_height, scale):
        """核心提取逻辑"""
        layout = self.model.detect(image)
        figures = []
        fig_count = 0
        
        for block in layout:
            if block.type != "Figure":
                continue
                
            fig_count += 1
            x1, y1, x2, y2 = int(block.block.x_1), int(block.block.y_1), \
                            int(block.block.x_2), int(block.block.y_2)
            
            # 转换回原始坐标（与OCR API坐标系统一致）
            if scale != 1.0:
                orig_x1, orig_y1 = x1 / scale, y1 / scale
                orig_x2, orig_y2 = x2 / scale, y2 / scale
            else:
                orig_x1, orig_y1, orig_x2, orig_y2 = x1, y1, x2, y2
            
            # 保存图片
            cropped = image[y1:y2, x1:x2]
            filename = f"fig_p{page_num}_{fig_count}.png"
            filepath = os.path.join(output_dir, filename)
            Image.fromarray(cropped).save(filepath)
            
            figures.append({
                "id": f"fig_p{page_num}_{fig_count}",
                "filename": filename,
                "page": page_num,
                "bbox": {
                    "top_left": {"x": int(orig_x1), "y": int(orig_y1)},
                    "right_bottom": {"x": int(orig_x2), "y": int(orig_y2)}
                },
                "center_y": int((orig_y1 + orig_y2) / 2),  # 用于确定插入位置
                "anchor_tag": f"[FIGURE_{fig_count}_PAGE_{page_num}]"
            })
        
        return figures
    
    def _save_figure_data(self, figures, output_dir):
        """保存图片数据"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_figures": len(figures),
            "figures": figures
        }
        
        with open(os.path.join(output_dir, "figures.json"), 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def merge_text_with_figures(ocr_json, figures_json):
    """
    将OCR文本与图片信息合并
    
    Args:
        ocr_json: OCR API返回的JSON数据
        figures_json: 图片提取器生成的figures.json路径
        
    Returns:
        str: 包含图片锚点的文本
    """
    # 加载图片数据
    with open(figures_json, 'r') as f:
        figure_data = json.load(f)
    
    figures = figure_data['figures']
    
    # 按页面组织图片
    figures_by_page = {}
    for fig in figures:
        page = fig['page']
        if page not in figures_by_page:
            figures_by_page[page] = []
        figures_by_page[page].append(fig)
    
    # 处理文本
    result_text = ""
    
    for block_idx, block in enumerate(ocr_json['data']['block']):
        if block['type'] != 'text':
            continue
            
        # 处理每一行文本
        for line in block['line']:
            line_text = ""
            line_y = None
            
            # 提取行的Y坐标（如果有位置信息）
            if 'location' in line:
                line_y = line['location']['top_left']['y']
            
            # 组合单词
            for word in line['word']:
                line_text += word['content'] + " "
            
            line_text = line_text.strip()
            
            # 检查是否需要在此行前插入图片
            if line_y is not None and 0 in figures_by_page:  # 假设单页文档
                for fig in figures_by_page[0]:
                    # 如果图片中心在当前行之前，且还没被插入
                    if fig['center_y'] < line_y and not fig.get('inserted', False):
                        result_text += f"\n{fig['anchor_tag']}\n"
                        fig['inserted'] = True
            
            result_text += line_text + "\n"
    
    # 添加剩余未插入的图片
    for page_figs in figures_by_page.values():
        for fig in page_figs:
            if not fig.get('inserted', False):
                result_text += f"\n{fig['anchor_tag']}\n"
    
    return result_text

def process_document_with_text_api(file_path, ocr_result, output_dir=None):
    """
    完整的文档处理流程
    
    Args:
        file_path: 原始文档路径
        ocr_result: OCR API的返回结果（JSON）
        output_dir: 输出目录
        
    Returns:
        tuple: (图片列表, 合并后的文本)
    """
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"extracted_{timestamp}"
    
    # 1. 提取图片
    extractor = FigureTextExtractor()
    figures = extractor.extract_figures_with_positions(file_path, output_dir)
    
    # 2. 合并文本和图片
    figures_json_path = os.path.join(output_dir, "figures.json")
    merged_text = merge_text_with_figures(ocr_result, figures_json_path)
    
    # 3. 保存最终文本
    with open(os.path.join(output_dir, "final_text.txt"), 'w', encoding='utf-8') as f:
        f.write(merged_text)
    
    return figures, merged_text

def create_final_document(text_with_anchors, figures_json_path, output_path="final_document.md"):
    """
    生成最终的文档（Markdown格式）
    
    Args:
        text_with_anchors: 包含锚点的文本
        figures_json_path: 图片信息JSON文件路径
        output_path: 输出文件路径
    """
    # 加载图片信息
    with open(figures_json_path, 'r') as f:
        figure_data = json.load(f)
    
    # 创建锚点到图片的映射
    anchor_map = {}
    for fig in figure_data['figures']:
        anchor_map[fig['anchor_tag']] = fig['filename']
    
    # 替换锚点为Markdown图片标签
    final_text = text_with_anchors
    for anchor, filename in anchor_map.items():
        final_text = final_text.replace(anchor, f"\n![Figure]({filename})\n")
    
    # 保存最终文档
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)
    
    print(f"最终文档已保存到: {output_path}")
    return final_text

# 使用示例
if __name__ == "__main__":
    # 模拟OCR API结果（你需要替换为实际的API返回）
    sample_ocr_result = {
        "code": "0",
        "data": {
            "block": [
                {
                    "line": [
                        {
                            "confidence": 1,
                            "word": [{"content": "这是"}],
                            "location": {"right_bottom": {"y": 50, "x": 100}, "top_left": {"y": 20, "x": 10}}
                        },
                        {
                            "confidence": 1,
                            "word": [{"content": "第二段文本"}],
                            "location": {"right_bottom": {"y": 200, "x": 300}, "top_left": {"y": 170, "x": 10}}
                        }
                    ],
                    "type": "text"
                }
            ]
        }
    }
    
    # 处理文档
    document_path = "test_document.pdf"  # 替换为你的文档
    
    try:
        figures, merged_text = process_document_with_text_api(
            document_path, sample_ocr_result
        )
        
        print(f"提取了 {len(figures)} 张图片")
        print("合并后的文本:")
        print(merged_text)
        
        # 生成最终文档
        create_final_document(
            merged_text, 
            "extracted_*/figures.json",  # 替换为实际路径
            "final_document.md"
        )
        
    except Exception as e:
        print(f"处理失败: {e}")