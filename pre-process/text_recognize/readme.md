# 文档转换工具

将各种格式的文件转换为Markdown格式的工具。目前主要代码在 `processtext.py`，调用通用文档识别（大模型）API，支持多种文件格式转换为Markdown。

## 支持格式
- 图片: JPG, PNG
- 文档: PDF, DOCX, HTML
- 网页: HTML文件或URL

## 安装依赖

### Python依赖
```bash
pip install -r requirements.txt
```

### 系统依赖
```bash
# PDF处理依赖
conda install -c conda-forge poppler

# DOCX转换依赖
conda install -c conda-forge pandoc
```

### 特殊说明
- **DOC文件**: 需要先转换为DOCX格式。建议使用WPS或Office打开DOC文件，另存为DOCX格式后再处理
- **图片转换**: 需要配置讯飞API密钥

## 使用方法

```bash
python processtext.py <文件路径或URL>
```

### 示例
```bash
# 处理PDF文件
python processtext.py example.pdf

# 处理图片文件
python processtext.py image.jpg

# 处理Word文档
python processtext.py document.docx

# 处理HTML文件
python processtext.py webpage.html

# 处理网页URL
python processtext.py https://example.com
```

## 输出
- 所有输出文件保存到 `outputs/` 文件夹
- 输出文件名格式: `原文件名_output.md`
- 示例: `CSfile.pdf` → `CSfile_output.md`
- DOCX转换时，提取的图片保存在 `media_文件名/` 文件夹下
