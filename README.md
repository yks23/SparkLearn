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
预处理插图提取要求python版本为：3.10  
相关依赖安装见requirement.txt  