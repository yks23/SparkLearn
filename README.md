# EduSpark
## 项目结构
- data:
    - 包含各种原材料教材
- pre-process
    - 预处理部分
    - 暴露接口类似pdf2txt，word2txt。可以给定输入文件路径/输出文件路径，完成格式转化
- sider
    - 插入补充知识
    - 接收预定义的txt格式，向其中插入额外内容
- KG-generator
    - 生成帮忙理解知识点之间关系的知识图谱
    - 接收预定义的txt格式，输出知识图谱（图片/网站）
- QA-generator
    - 跟前面步骤的人交流需要什么样的输入和信息
    - 生成各种题目及其解答

## 环境要求

python版本为：3.11.7  
相关依赖安装见requirement.txt  
```bash
conda create --name eduspark python=3.11.7 
conda activate eduspark
pip install -r requirements.txt
```
ppt相关处理需要sudo apt install libreoffice-core libreoffice-common  
sudo apt install libreoffice-impress  
conda install -c conda-forge poppler  
PDF处理依赖
conda install -c conda-forge poppler
DOCX转换依赖
conda install -c conda-forge pandoc

## 目前pipeline

1. 静态过程
用户填写基本的配置，然后运行主程序即可

- 包含是哪种类型的：multi-笔记（文件夹）/ 一本书 / pdf / 图片 / 网页
    - 书：结构在内部
    - 文件夹结构：叶子节点是图片/网页/pdf

dataroot
    - raw
    - processed
        - ...
    - kg
    - QA

- 基本过程：
    - 是否需要sider
    - 是否需要图谱
    - 是否需要问题

对象：Task manager

1. preprocess  -> 文本
2. sider -> 补充后的文本
3. kg生成 -> 图谱--重在可视化（有无API何以生成静态图片）
4. qg生成 -> 生成question.pdf和answer.pdf

2. 带有前端
灵活、可交互。上述流程是高度可定制（容易出问题的）

3. AGENT with ABILITY.

## 第一部分只用文书材料

## GUI
1. 选择输入文件/输入文件夹
2. 选择输出文件夹
   - 如果此文件夹里面有state.json，会加载对应的处理状态（在下方的“处理步骤”中反映出来）
3. 选择需要执行的步骤（一般全选就行），点击“执行选中步骤”
   - 只要输出文件夹里存在tree/graph/graph.png，右边的图片框会自动加载
4. 执行完前三步或者state.json里前三步为`true`后，选择知识点、难度的选择框和`生成题目`按钮会亮起
   - 题目会输出到输出文件夹/questions下
 