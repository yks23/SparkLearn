- 两个文件：`annotator.py`和`annotator_simple.py`
- 输入：原始文件处理得到的md文件
- 输出：经过批注、加入知识卡片、进行知识扩展和易化学习之后的md文件
- 两个文件的区别：`annotator.py`是用大模型一步步地进行段落结构识别、段落难度评分、加入知识卡片、加入知识扩展、加入易化学习内容；`annotator_simple.py`是只用一轮对话完成上述所有过程
- 目前，`annotator_simple.py`的**效果更好**一些；`annotator.py`**速度非常慢**，有时候会出现乱码，但是能对整个批注过程进行**逐步控制**，按需选用即可
- 使用示例见`example.py`：在项目根目录下运行
    ```bash
    python sider/example.py 
    ```

