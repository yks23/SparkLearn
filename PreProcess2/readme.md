目前主要推进的代码在processtext.py，调用的是通用文档识别（大模型）的api。

在代码里修改最下面函数入口的文件路径，处理pdf/png/jpg的文件类型，在代码目录输出后缀output.md的markdown文件，同时命令行输出原始的返回内容。

processtext.py的环境相关：

pip install pdf2image pillow

pip install requests

conda install -c conda-forge poppler

