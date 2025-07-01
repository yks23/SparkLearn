# 集成测试脚本
# test_integration.py

import cv2
import numpy as np
import json
from illustration_extractor import FigureTextExtractor, merge_text_with_figures, create_final_document
import os

def create_test_document():
    """创建一个测试文档图片"""
    # 创建白色背景 800x600
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # 添加标题 (Y: 30-60)
    cv2.putText(img, "Test Document Title", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
    
    # 添加第一段文本 (Y: 80-120)
    cv2.putText(img, "This is the first paragraph of text.", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(img, "It contains multiple lines.", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # 添加图片区域1 (Y: 150-250)
    cv2.rectangle(img, (100, 150), (400, 250), (255, 0, 0), 3)
    cv2.putText(img, "FIGURE 1", (180, 205), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # 添加第二段文本 (Y: 280-320)
    cv2.putText(img, "This is the second paragraph.", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(img, "It should appear after Figure 1.", (50, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # 添加图片区域2 (Y: 350-450)
    cv2.rectangle(img, (450, 350), (750, 450), (0, 255, 0), 3)
    cv2.putText(img, "FIGURE 2", (530, 405), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # 添加第三段文本 (Y: 480-520)
    cv2.putText(img, "This is the final paragraph.", (50, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(img, "It should appear after Figure 2.", (50, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # 保存图片
    cv2.imwrite("test_document.jpg", img)
    print("✅ 创建测试文档: test_document.jpg")
    return "test_document.jpg"

def create_mock_ocr_result():
    """创建模拟的OCR API结果"""
    mock_result = {
        "code": "0",
        "data": {
            "block": [
                {
                    "line": [
                        {
                            "confidence": 1,
                            "word": [
                                {"content": "Test", "location": {"top_left": {"x": 50, "y": 30}, "right_bottom": {"x": 90, "y": 60}}},
                                {"content": "Document", "location": {"top_left": {"x": 95, "y": 30}, "right_bottom": {"x": 180, "y": 60}}},
                                {"content": "Title", "location": {"top_left": {"x": 185, "y": 30}, "right_bottom": {"x": 230, "y": 60}}}
                            ],
                            "location": {"top_left": {"x": 50, "y": 30}, "right_bottom": {"x": 230, "y": 60}}
                        }
                    ],
                    "type": "text"
                },
                {
                    "line": [
                        {
                            "confidence": 1,
                            "word": [
                                {"content": "This", "location": {"top_left": {"x": 50, "y": 80}, "right_bottom": {"x": 80, "y": 100}}},
                                {"content": "is", "location": {"top_left": {"x": 85, "y": 80}, "right_bottom": {"x": 100, "y": 100}}},
                                {"content": "the", "location": {"top_left": {"x": 105, "y": 80}, "right_bottom": {"x": 125, "y": 100}}},
                                {"content": "first", "location": {"top_left": {"x": 130, "y": 80}, "right_bottom": {"x": 160, "y": 100}}},
                                {"content": "paragraph", "location": {"top_left": {"x": 165, "y": 80}, "right_bottom": {"x": 220, "y": 100}}}
                            ],
                            "location": {"top_left": {"x": 50, "y": 80}, "right_bottom": {"x": 220, "y": 100}}
                        },
                        {
                            "confidence": 1,
                            "word": [
                                {"content": "It", "location": {"top_left": {"x": 50, "y": 105}, "right_bottom": {"x": 65, "y": 125}}},
                                {"content": "contains", "location": {"top_left": {"x": 70, "y": 105}, "right_bottom": {"x": 120, "y": 125}}},
                                {"content": "multiple", "location": {"top_left": {"x": 125, "y": 105}, "right_bottom": {"x": 175, "y": 125}}},
                                {"content": "lines", "location": {"top_left": {"x": 180, "y": 105}, "right_bottom": {"x": 210, "y": 125}}}
                            ],
                            "location": {"top_left": {"x": 50, "y": 105}, "right_bottom": {"x": 210, "y": 125}}
                        }
                    ],
                    "type": "text"
                },
                {
                    "line": [
                        {
                            "confidence": 1,
                            "word": [
                                {"content": "This", "location": {"top_left": {"x": 50, "y": 280}, "right_bottom": {"x": 80, "y": 300}}},
                                {"content": "is", "location": {"top_left": {"x": 85, "y": 280}, "right_bottom": {"x": 100, "y": 300}}},
                                {"content": "the", "location": {"top_left": {"x": 105, "y": 280}, "right_bottom": {"x": 125, "y": 300}}},
                                {"content": "second", "location": {"top_left": {"x": 130, "y": 280}, "right_bottom": {"x": 170, "y": 300}}},
                                {"content": "paragraph", "location": {"top_left": {"x": 175, "y": 280}, "right_bottom": {"x": 240, "y": 300}}}
                            ],
                            "location": {"top_left": {"x": 50, "y": 280}, "right_bottom": {"x": 240, "y": 300}}
                        },
                        {
                            "confidence": 1,
                            "word": [
                                {"content": "It", "location": {"top_left": {"x": 50, "y": 305}, "right_bottom": {"x": 65, "y": 325}}},
                                {"content": "should", "location": {"top_left": {"x": 70, "y": 305}, "right_bottom": {"x": 110, "y": 325}}},
                                {"content": "appear", "location": {"top_left": {"x": 115, "y": 305}, "right_bottom": {"x": 155, "y": 325}}},
                                {"content": "after", "location": {"top_left": {"x": 160, "y": 305}, "right_bottom": {"x": 190, "y": 325}}},
                                {"content": "Figure", "location": {"top_left": {"x": 195, "y": 305}, "right_bottom": {"x": 230, "y": 325}}},
                                {"content": "1", "location": {"top_left": {"x": 235, "y": 305}, "right_bottom": {"x": 245, "y": 325}}}
                            ],
                            "location": {"top_left": {"x": 50, "y": 305}, "right_bottom": {"x": 245, "y": 325}}
                        }
                    ],
                    "type": "text"
                },
                {
                    "line": [
                        {
                            "confidence": 1,
                            "word": [
                                {"content": "This", "location": {"top_left": {"x": 50, "y": 480}, "right_bottom": {"x": 80, "y": 500}}},
                                {"content": "is", "location": {"top_left": {"x": 85, "y": 480}, "right_bottom": {"x": 100, "y": 500}}},
                                {"content": "the", "location": {"top_left": {"x": 105, "y": 480}, "right_bottom": {"x": 125, "y": 500}}},
                                {"content": "final", "location": {"top_left": {"x": 130, "y": 480}, "right_bottom": {"x": 160, "y": 500}}},
                                {"content": "paragraph", "location": {"top_left": {"x": 165, "y": 480}, "right_bottom": {"x": 220, "y": 500}}}
                            ],
                            "location": {"top_left": {"x": 50, "y": 480}, "right_bottom": {"x": 220, "y": 500}}
                        },
                        {
                            "confidence": 1,
                            "word": [
                                {"content": "It", "location": {"top_left": {"x": 50, "y": 505}, "right_bottom": {"x": 65, "y": 525}}},
                                {"content": "should", "location": {"top_left": {"x": 70, "y": 505}, "right_bottom": {"x": 110, "y": 525}}},
                                {"content": "appear", "location": {"top_left": {"x": 115, "y": 505}, "right_bottom": {"x": 155, "y": 525}}},
                                {"content": "after", "location": {"top_left": {"x": 160, "y": 505}, "right_bottom": {"x": 190, "y": 525}}},
                                {"content": "Figure", "location": {"top_left": {"x": 195, "y": 505}, "right_bottom": {"x": 230, "y": 525}}},
                                {"content": "2", "location": {"top_left": {"x": 235, "y": 505}, "right_bottom": {"x": 245, "y": 525}}}
                            ],
                            "location": {"top_left": {"x": 50, "y": 505}, "right_bottom": {"x": 245, "y": 525}}
                        }
                    ],
                    "type": "text"
                }
            ]
        },
        "sid": "test12345",
        "desc": "success"
    }
    
    # 保存模拟结果
    with open("mock_ocr_result.json", 'w', encoding='utf-8') as f:
        json.dump(mock_result, f, indent=2, ensure_ascii=False)
    
    print("✅ 创建模拟OCR结果: mock_ocr_result.json")
    return mock_result

def run_integration_test():
    """运行完整的集成测试"""
    print("=" * 60)
    print("集成测试开始")
    print("=" * 60)
    
    # 1. 创建测试文档
    print("\n1. 创建测试文档...")
    doc_path = create_test_document()
    
    # 2. 创建模拟OCR结果
    print("\n2. 创建模拟OCR结果...")
    ocr_result = create_mock_ocr_result()
    
    # 3. 提取图片
    print("\n3. 提取图片...")
    extractor = FigureTextExtractor(confidence=0.5)  # 降低阈值用于测试
    figures = extractor.extract_figures_with_positions(doc_path, "test_output")
    
    print(f"   提取到 {len(figures)} 张图片:")
    for fig in figures:
        print(f"   - {fig['filename']}: Y坐标 {fig['center_y']}")
    
    # 4. 合并文本和图片
    print("\n4. 合并文本和图片...")
    merged_text = merge_text_with_figures(ocr_result, "test_output/figures.json")
    
    # 5. 保存结果
    print("\n5. 保存结果...")
    with open("test_output/merged_text.txt", 'w', encoding='utf-8') as f:
        f.write(merged_text)
    
    # 6. 生成最终文档
    print("\n6. 生成最终文档...")
    final_doc = create_final_document(
        merged_text, 
        "test_output/figures.json", 
        "test_output/final_document.md"
    )
    
    # 7. 显示结果
    print("\n" + "=" * 60)
    print("测试结果:")
    print("=" * 60)
    print("合并后的文本:")
    print("-" * 30)
    print(merged_text)
    print("-" * 30)
    
    print(f"\n文件输出:")
    print(f"- 测试文档: {doc_path}")
    print(f"- 图片目录: test_output/")
    print(f"- 图片信息: test_output/figures.json")
    print(f"- 合并文本: test_output/merged_text.txt")
    print(f"- 最终文档: test_output/final_document.md")
    
    # 8. 验证结果
    print(f"\n验证:")
    expected_order = ["标题", "第一段", "图片1", "第二段", "图片2", "第三段"]
    if "[FIGURE_1_PAGE_0]" in merged_text and "[FIGURE_2_PAGE_0]" in merged_text:
        print("✅ 图片锚点成功插入到文本中")
    else:
        print("❌ 图片锚点插入失败")
    
    # 检查插入顺序
    text_lines = merged_text.split('\n')
    figure1_line = -1
    figure2_line = -1
    
    for i, line in enumerate(text_lines):
        if "FIGURE_1" in line:
            figure1_line = i
        elif "FIGURE_2" in line:
            figure2_line = i
    
    if figure1_line < figure2_line and figure1_line > 0:
        print("✅ 图片插入顺序正确")
    else:
        print("❌ 图片插入顺序可能有问题")
    
    return merged_text, figures

def show_usage_example():
    """显示实际使用示例"""
    print("\n" + "=" * 60)
    print("实际使用示例:")
    print("=" * 60)
    
    example_code = '''
# 在你的实际项目中使用:

from figure_text_extractor import FigureTextExtractor, merge_text_with_figures

# 1. 提取图片
extractor = FigureTextExtractor()
figures = extractor.extract_figures_with_positions("your_document.pdf", "output")

# 2. 获取OCR结果（调用你们的文本API）
ocr_result = your_text_api.extract_text("your_document.pdf")

# 3. 合并文本和图片
merged_text = merge_text_with_figures(ocr_result, "output/figures.json")

# 4. 生成最终文档
create_final_document(merged_text, "output/figures.json", "final.md")

print("完成！图片已精确插入到文本中")
    '''
    
    print(example_code)

if __name__ == "__main__":
    try:
        # 运行集成测试
        merged_text, figures = run_integration_test()
        
        # 显示使用示例
        show_usage_example()
        
        print("\n🎉 集成测试完成！")
        print("请检查 test_output/ 目录中的结果文件")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()