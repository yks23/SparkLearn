from document_converter import DocumentProcessor, process_document

# 方式1：直接使用便捷函数
def example_1():
    """使用便捷函数转换文件"""
    
    try:
        output_path = process_document('pre_process/text_recognize/example/wangyuan.pdf', 'my_outputs')
        print(f"转换完成，输出文件：{output_path}")
    except Exception as e:
        print(f"转换失败：{e}")

# 方式2：使用类实例
def example_2():
    """使用类实例进行转换"""
    
    # 创建转换器
    converter = DocumentProcessor()
    
    # 转换多个文件
    files = ['doc1.pdf', 'doc2.docx', 'doc3.html']
    
    for file_path in files:
        try:
            output_path = converter.process(file_path)
            print(f"转换完成：{file_path} -> {output_path}")
        except Exception as e:
            print(f"转换失败 {file_path}：{e}")

# 方式3：处理URL
def example_3():
    """转换网页URL"""
    
    converter = DocumentProcessor()
    
    try:
        output_path = converter.process('https://example.com')
        print(f"网页转换完成：{output_path}")
    except Exception as e:
        print(f"网页转换失败：{e}")

# 方式4：批量处理
def batch_convert(file_list):
    """批量转换文件"""
    
    converter = DocumentProcessor()
    results = []
    
    for file_path in file_list:
        try:
            output_path = converter.process(file_path)
            results.append({'input': file_path, 'output': output_path, 'status': 'success'})
        except Exception as e:
            results.append({'input': file_path, 'error': str(e), 'status': 'failed'})
    
    return results

if __name__ == "__main__":
    # 运行示例
    example_1()