#!/usr/bin/env python3
import requests
import html2text
from pathlib import Path
from urllib.parse import urlparse
import sys


def html_to_markdown(input_source, **options):
    """
    将HTML转换为Markdown格式
    
    Args:
        input_source (str): 网页URL或本地HTML文件路径
        **options: html2text的配置选项
    
    Returns:
        str: Markdown格式的文本
        
    Raises:
        requests.RequestException: 网络请求失败
        FileNotFoundError: 文件不存在
        UnicodeDecodeError: 文件编码问题
    """
    
    # 判断输入是URL还是文件路径
    if input_source.startswith(('http://', 'https://')):
        html_content = _fetch_from_url(input_source)
    else:
        html_content = _read_from_file(input_source)
    
    # 配置HTML2Text转换器
    converter = html2text.HTML2Text()
    
    # 设置默认选项
    default_options = {
        'ignore_links': False,
        'ignore_images': False,
        'ignore_emphasis': False,
        'body_width': 0,  # 不限制行宽
        'unicode_snob': True,  # 使用Unicode字符
        'escape_snob': True,   # 转义特殊字符
    }
    
    # 应用用户自定义选项
    for key, value in {**default_options, **options}.items():
        setattr(converter, key, value)
    
    return converter.handle(html_content).strip()


def _fetch_from_url(url):
    """从URL获取HTML内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding  # 自动检测编码
    return response.text


def _read_from_file(file_path):
    """从本地文件读取HTML内容"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 尝试多种编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
    
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    
    raise UnicodeDecodeError("无法解码文件，请检查文件编码")


def save_markdown(content, output_path):
    """保存Markdown内容到文件"""
    Path(output_path).write_text(content, encoding='utf-8')
    print(f"✅ Markdown文件已保存: {output_path}")


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python html_to_md.py <URL或文件路径> [输出文件路径]")
        sys.exit(1)
    
    input_source = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        print(f"🔄 正在转换: {input_source}")
        
        # 转换HTML为Markdown
        markdown_content = html_to_markdown(input_source)
        
        if output_path:
            save_markdown(markdown_content, output_path)
        else:
            print("=" * 50)
            print(markdown_content)
            print("=" * 50)
            
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        sys.exit(1)


# 使用示例
if __name__ == "__main__":
    # 方式1: 命令行使用
    if len(sys.argv) > 1:
        main()
    else:
        # 方式2: 直接调用函数
        examples = [
            # "https://example.com",
            # "sample.html"
        ]
        
        for example in examples:
            try:
                result = html_to_markdown(example)
                print(f"\n转换结果 ({example}):")
                print("-" * 40)
                print(result[:200] + "..." if len(result) > 200 else result)
            except Exception as e:
                print(f"转换 {example} 失败: {e}")

        # 自定义选项示例
        custom_options = {
            'ignore_links': True,     # 忽略链接
            'ignore_images': True,    # 忽略图片
            'body_width': 80,         # 限制行宽
        }
        
        print("\n使用示例:")
        print("# 基本用法")
        print("markdown = html_to_markdown('https://example.com')")
        print("markdown = html_to_markdown('page.html')")
        print("\n# 自定义选项")
        print("markdown = html_to_markdown('https://example.com', ignore_links=True)")
        print("\n# 命令行用法")
        print("python html_to_md.py https://example.com output.md")
        print("python html_to_md.py input.html output.md")