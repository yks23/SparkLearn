import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog,
    QLabel, QTextEdit, QProgressBar, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from main import process_folder, augment_folder, tree_folder, generate_QA
from qa_selector_dialog import QASelectorDialog
from qg.graph_class import KnowledgeGraph  # 你自己写的类
from main import generate_QA  # 确保 generate_QA 支持 concept, level 参数

def handle_qa_ready(self, graph_path, output_path):
    # 加载图谱
    kg = KnowledgeGraph()
    kg.load_knowledge_graph(graph_path)
    concepts = list(kg.graph.nodes)

    # 弹出选择窗口
    dialog = QASelectorDialog(concepts, self)
    if dialog.exec_():
        concept, level = dialog.get_selection()
        self.log(f"🎯 用户选择：知识点={concept or '全部'}，难度={level}")
        generate_QA(graph_path, output_path, concept=concept, level=level)
        self.log("✅ 问答生成完成")
    else:
        self.log("❌ 用户取消了问答生成")

    self.pipeline_thread.finished.emit()  # 👈 手动发出完成信号

class FullPipelineThread(QThread):
    finished = pyqtSignal()
    log = pyqtSignal(str)
    qa_ready = pyqtSignal(str, str)  # 👈 新增信号，用于通知主线程准备好生成问答
    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.state_path = os.path.join(self.output_path, 'state.json')

    def run(self):
        file_path = self.input_path
        output_path = self.output_path
        processed_path = os.path.join(output_path, os.path.basename(file_path))

        if os.path.exists(self.state_path):
            with open(self.state_path, 'r') as f:
                try:
                    state_file = json.load(f)
                except:
                    state_file = {}
        else:
            state_file = {}

        if state_file.get('preprocess', False):
            self.log.emit("已处理过，跳过预处理")
        else:
            self.log.emit("开始预处理...")
            process_folder(file_path, output_path)
            state_file['preprocess'] = True
            with open(self.state_path, 'w') as f:
                json.dump(state_file, f, indent=4)
            self.log.emit("✅ 预处理完成")

        if state_file.get('augment', False):
            self.log.emit("已增广过，跳过增广")
        else:
            self.log.emit("开始知识补充...")
            augment_folder(processed_path)
            state_file['augment'] = True
            with open(self.state_path, 'w') as f:
                json.dump(state_file, f, indent=4)
            self.log.emit("✅ 知识补充完成")

        tree_output = os.path.join(output_path, 'tree')
        if state_file.get('tree', False):
            self.log.emit("已生成树形结构，跳过")
        else:
            self.log.emit("开始结构梳理...")
            tree_folder(processed_path, tree_output)
            state_file['tree'] = True
            with open(self.state_path, 'w') as f:
                json.dump(state_file, f, indent=4)
            self.log.emit("✅ 结构梳理完成")

        graph_input = os.path.join(tree_output, 'graph')
        qa_output = os.path.join(output_path, 'qa')
        if state_file.get('qa', False):
            self.log.emit("已生成问答对，跳过")
        else:
            self.log.emit("开始生成问答...")
            self.log.emit("等待用户选择知识点和难度...")
            self.qa_ready.emit(graph_input, qa_output)  # 👈 发出信号，不直接生成
            return  # 👈 等主线程调用 generate_QA 后再手动 emit finished

        self.finished.emit()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduSpark 一键处理")
        self.resize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.output_path = None

        self.output_label = QLabel("输出路径：默认（桌面/EduSpark/...）")
        layout.addWidget(self.output_label)

        self.set_output_button = QPushButton("修改输出路径")
        self.set_output_button.clicked.connect(self.select_output_path)
        layout.addWidget(self.set_output_button)

        self.select_input_button = QPushButton("选择输入文件夹")
        self.select_input_button.clicked.connect(self.select_input_path)
        layout.addWidget(self.select_input_button)

        self.run_button = QPushButton("一键运行全流程")
        self.run_button.clicked.connect(self.run_full_pipeline)
        layout.addWidget(self.run_button)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        layout.addWidget(self.output_display)

        self.setLayout(layout)
        self.input_path = None

    def select_input_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if folder:
            self.input_path = folder
            self.log(f"已选择输入: {folder}")

    def select_output_path(self):
        selected_dir = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if selected_dir:
            self.output_path = selected_dir
            self.output_label.setText(f"输出路径：{selected_dir}")
        else:
            self.output_label.setText("输出路径：默认（桌面/EduSpark/...）")
            self.output_path = None

    def get_default_output_path(self, input_path):
        from pathlib import Path
        desktop = Path.home() / "Desktop"
        base_name = os.path.basename(input_path)
        return str(desktop / "EduSpark" / base_name)

    def run_full_pipeline(self):
        if not self.input_path:
            QMessageBox.warning(self, "未选择输入", "请先选择输入文件夹")
            return

        output_path = self.output_path or self.get_default_output_path(self.input_path)
        os.makedirs(output_path, exist_ok=True)

        self.log(f"🔧 正在处理: {self.input_path}")
        self.log(f"📂 输出路径: {output_path}")
        self.progress.show()

        self.pipeline_thread = FullPipelineThread(self.input_path, output_path)
        self.pipeline_thread.log.connect(self.log)
        self.pipeline_thread.finished.connect(lambda: self.progress.hide())
        self.pipeline_thread.finished.connect(lambda: self.log("✅ 所有流程完成"))
        self.pipeline_thread.qa_ready.connect(self.handle_qa_ready)  # 👈 绑定槽函数
        self.pipeline_thread.start()

    def log(self, text):
        self.output_display.append(text)

    def handle_qa_ready(self, graph_input, qa_output):
        dialog = QASelectionDialog(graph_input, qa_output)
        if dialog.exec_() == QDialog.Accepted:
            concept, level = dialog.get_selection()
            self.log(f"🔍 选择的知识点: {concept}, 难度: {level}")
            self.pipeline_thread.start_qa_generation(concept, level)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())