import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog,
    QLabel, QTextEdit, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# === 以下是你提供的原始逻辑 ===
from pre_process.text_recognize.processtext import process_input
from sider.annotator_simple import SimplifiedAnnotator
from qg.graph_class import KnowledgeGraph, KnowledgeQuestionGenerator

# === 封装线程类：避免UI卡顿 ===
class PreprocessThread(QThread):
    finished = pyqtSignal()
    log = pyqtSignal(str)

    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        def process_folder(input_path, output_path):
            if not os.path.isdir(input_path):
                process_input(input_path, output_path)
                self.log.emit(f"已处理文件: {input_path}")
            else:
                sub_folders = os.listdir(input_path)
                new_output_path = os.path.join(output_path, os.path.basename(input_path))
                os.makedirs(new_output_path, exist_ok=True)
                for sub_folder in sub_folders:
                    sub_folder_path = os.path.join(input_path, sub_folder)
                    process_folder(sub_folder_path, new_output_path)  # ✅ 递归调用

        process_folder(self.input_path, self.output_path)
        self.finished.emit()


class SiderThread(QThread):
    finished = pyqtSignal()
    log = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        annotator = SimplifiedAnnotator()
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        annotator.process(content, self.file_path)
        self.log.emit(f"Sider 补充完成: {self.file_path}")
        self.finished.emit()

class KGThread(QThread):
    finished = pyqtSignal()
    log = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        kg = KnowledgeGraph()
        kg.create_graph(self.file_path)
        self.log.emit(f"知识图谱已生成: {self.file_path}")
        self.finished.emit()

class QAThread(QThread):
    finished = pyqtSignal()
    log = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        qg = KnowledgeQuestionGenerator()
        qg.generate(self.file_path)
        self.log.emit(f"问题生成完成: {self.file_path}")
        self.finished.emit()

# === 主窗口界面 ===
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduSpark 工具箱")
        self.resize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.output_path = None  # 初始化默认输出路径

        # 显示当前输出目录
        self.output_label = QLabel("输出路径：默认（桌面/EduSpark/...）")
        layout.addWidget(self.output_label)

        # 设置输出路径按钮
        self.set_output_button = QPushButton("修改输出路径")
        self.set_output_button.clicked.connect(self.select_output_path)
        layout.addWidget(self.set_output_button)

        self.label = QLabel("请选择要执行的操作：")
        layout.addWidget(self.label)

        self.preprocess_button = QPushButton("预处理")
        self.preprocess_button.clicked.connect(self.run_preprocess)
        layout.addWidget(self.preprocess_button)

        self.sider_button = QPushButton("Sider（补充知识）")
        self.sider_button.clicked.connect(self.run_sider)
        layout.addWidget(self.sider_button)

        self.kg_button = QPushButton("KG-Generator")
        self.kg_button.clicked.connect(self.run_kg)
        layout.addWidget(self.kg_button)

        self.qa_button = QPushButton("QA-Generator")
        self.qa_button.clicked.connect(self.run_qa)
        layout.addWidget(self.qa_button)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 设置为0表示“无限进度条”模式
        self.progress.hide()
        layout.addWidget(self.progress)

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        layout.addWidget(self.output_display)

        self.setLayout(layout)

    def log(self, text):
        self.output_display.append(text)

    def show_progress(self, show=True):
        self.progress.setVisible(show)

    def get_default_output_path(self, input_path, category: str = "预处理"):
        from pathlib import Path
        desktop = Path.home() / "Desktop"
        base_name = os.path.basename(input_path)
        if '.' in base_name:
            base_name = os.path.splitext(base_name)[0]
        return str(desktop / "EduSpark" / base_name / category)



    def run_preprocess(self):
        file_path = QFileDialog.getExistingDirectory(self, "选择要处理的文件夹")
        if file_path:
            output_path = self.output_path or self.get_default_output_path(file_path, "预处理")
            os.makedirs(output_path, exist_ok=True)

            self.log(f"开始预处理: {file_path}")
            self.log(f"输出目录: {output_path}")
            self.show_progress(True)

            self.pre_thread = PreprocessThread(file_path, output_path)
            self.pre_thread.log.connect(self.log)
            self.pre_thread.finished.connect(lambda: self.show_progress(False))
            self.pre_thread.finished.connect(lambda: self.log("✅ 预处理完成"))
            self.pre_thread.start()



    def run_sider(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 Markdown 文件", filter="Markdown files (*.md)")
        if file_path:
            # output_path = self.output_path or self.get_default_output_path(file_path, "知识补充")
            # os.makedirs(output_path, exist_ok=True)

            self.log(f"开始执行 Sider: {file_path}")
            # self.log(f"输出目录: {output_path}")
            self.show_progress(True)

            self.sider_thread = SiderThread(file_path)
            self.sider_thread.log.connect(self.log)
            self.sider_thread.finished.connect(lambda: self.show_progress(False))
            self.sider_thread.finished.connect(lambda: self.log("✅ Sider 补充完成"))
            self.sider_thread.start()


    def run_kg(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 Markdown 文件", filter="Markdown files (*.md)")
        if file_path:
            output_path = self.output_path or self.get_default_output_path(file_path, "结构梳理")
            os.makedirs(output_path, exist_ok=True)

            self.log(f"开始生成知识图谱: {file_path}")
            self.log(f"输出目录: {output_path}")
            self.show_progress(True)

            self.kg_thread = KGThread(file_path)
            self.kg_thread.log.connect(self.log)
            self.kg_thread.finished.connect(lambda: self.show_progress(False))
            self.kg_thread.finished.connect(lambda: self.log("✅ 知识图谱生成完成"))
            self.kg_thread.start()


    def run_qa(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 Markdown 文件", filter="Markdown files (*.md)")
        if file_path:
            output_path = self.output_path or self.get_default_output_path(file_path, "生成问答")
            os.makedirs(output_path, exist_ok=True)

            self.log(f"开始生成 QA: {file_path}")
            self.log(f"输出目录: {output_path}")
            self.show_progress(True)

            self.qa_thread = QAThread(file_path)
            self.qa_thread.log.connect(self.log)
            self.qa_thread.finished.connect(lambda: self.show_progress(False))
            self.qa_thread.finished.connect(lambda: self.log("✅ QA 生成完成"))
            self.qa_thread.start()


    def select_output_path(self):
        selected_dir = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if selected_dir:
            self.output_path = selected_dir
            self.output_label.setText(f"输出路径：{selected_dir}")
        else:
            self.output_label.setText("输出路径：默认（桌面/EduSpark/...）")
            self.output_path = None



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
