目前主要推进的代码在processtext.py，调用的是通用文档识别（大模型）的api。

在代码里修改最下面函数入口的文件路径，处理pdf/png/jpg的文件类型，在代码目录输出后缀output.md的markdown文件，同时命令行输出原始的返回内容。

processtext.py的环境相关：

与python有关的依赖已写进requirements.txt 可用 pip install -r requirements.txt 进行下载  

conda install -c conda-forge poppler

示例是 CSfile.pdf-->CSfile.md

docx转md，调用pandoc，需要安装pandoc，conda install -c conda-forge pandoc，提取出的图片会保存再media文件夹下。

doc转md，需要doc先转成docx，要使用libreoffice，这是一个大型应用，不能用conda安装也无法打包进程序，所以还是建议用户用WPS打开doc再另存为docx