import cv2
import os
import fitz  # PyMuPDF
from pathlib import Path

def extract_images_simple(image_path, output_dir="output"):
    """原始的图像提取函数"""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # *反转二值化
    _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    
    # 查找轮廓
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    os.makedirs(output_dir, exist_ok=True)
    count = 0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        # 关键：过滤掉太大的区域（避免整张图）
        if 5000 < area < img.shape[0] * img.shape[1] * 0.5:  # 面积不能超过图像50%
            x, y, w, h = cv2.boundingRect(contour)
            
            # 避免边缘区域
            margin = 20
            if x > margin and y > margin and x+w < img.shape[1]-margin and y+h < img.shape[0]-margin:
                aspect_ratio = w / h
                if 0.5 < aspect_ratio < 3:  # 长宽比合理
                    count += 1
                    cropped = img[y:y+h, x:x+w]
                    cv2.imwrite(f"{output_dir}/fig_{count}.png", cropped)
                    print(f"提取图像 {count}: {w}x{h}")
    
    print(f"完成！共 {count} 张")
    return count

def batch_extract_images(input_dir, output_base_dir="batch_output"):
    """批量处理图片文件夹"""
    input_path = Path(input_dir)
    supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    
    # 确保基础输出目录存在
    Path(output_base_dir).mkdir(parents=True, exist_ok=True)
    
    total_extracted = 0
    processed_files = 0
    
    for img_file in input_path.glob('*'):
        if img_file.suffix.lower() in supported_formats:
            print(f"\n处理文件: {img_file.name}")
            
            # 为每个图像创建单独的输出目录
            output_dir = Path(output_base_dir) / img_file.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                count = extract_images_simple(str(img_file), str(output_dir))
                total_extracted += count
                processed_files += 1
                print(f"{img_file.name}: 提取了 {count} 张图像")
            except Exception as e:
                print(f"处理 {img_file.name} 时出错: {e}")
    
    print(f"\n批量处理完成！")
    print(f"处理了 {processed_files} 个文件，共提取 {total_extracted} 张图像")

def pdf_to_images_and_extract(pdf_path, output_base_dir="pdf_output"):
    """处理PDF：先转换为图片，再提取图像"""
    pdf_path = Path(pdf_path)
    output_base_dir = Path(output_base_dir)
    
    # 创建输出目录
    pdf_output_dir = output_base_dir / pdf_path.stem
    pdf_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建临时目录存放PDF页面图片
    temp_dir = pdf_output_dir / "temp_pages"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # 打开PDF
        doc = fitz.open(str(pdf_path))
        print(f"PDF共有 {len(doc)} 页")
        
        total_extracted = 0
        
        # 处理每一页
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # 将页面转换为图像 (300 DPI)
            mat = fitz.Matrix(300/72, 300/72)  # 300 DPI
            pix = page.get_pixmap(matrix=mat)
            
            # 保存页面图片
            page_img_path = temp_dir / f"page_{page_num + 1}.png"
            pix.save(str(page_img_path))
            
            print(f"处理第 {page_num + 1} 页...")
            
            # 为每一页创建输出目录
            page_output_dir = pdf_output_dir / f"page_{page_num + 1}"
            page_output_dir.mkdir(exist_ok=True)
            
            try:
                # 提取图像
                count = extract_images_simple(str(page_img_path), str(page_output_dir))
                total_extracted += count
                print(f"第 {page_num + 1} 页提取了 {count} 张图像")
            except Exception as e:
                print(f"处理第 {page_num + 1} 页时出错: {e}")
        
        doc.close()
        
        # 可选：删除临时页面图片
        # import shutil
        # shutil.rmtree(temp_dir)
        
        print(f"\nPDF处理完成！共提取 {total_extracted} 张图像")
        return total_extracted
        
    except Exception as e:
        print(f"处理PDF时出错: {e}")
        return 0

# 使用示例
if __name__ == "__main__":
    # 原始单文件处理
    # extract_images_simple("test5.png")
    
    # 批量处理图片文件夹
    # batch_extract_images("test_images/")
    
    # 处理PDF
    pdf_to_images_and_extract("test.pdf")