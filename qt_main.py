import sys
import os
import json
import multiprocessing
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog,
    QLabel, QTextEdit, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from main import process_folder, augment_folder, tree_folder
from qg.graph_class import KnowledgeGraph, KnowledgeQuestionGenerator

class QtLogger(QObject):
    log_signal = pyqtSignal(str)

    def write(self, msg):
        msg = str(msg).strip()
        if msg:
            self.log_signal.emit(msg)

    def flush(self):
        pass


class PipelineThread(QThread):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, input_path, output_path, state_path, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.state_path = state_path

    def log(self, msg):
        self.log_signal.emit(str(msg))

    def run(self):
        try:
            state = {}
            if os.path.exists(self.state_path):
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)

            if not state.get('preprocess', False):
                self.log("🔧 正在预处理原始文件...")
                process_folder(self.input_path, self.output_path)
                state['preprocess'] = True
                with open(self.state_path, 'w') as f:
                    json.dump(state, f, indent=2)
            else:
                self.log("✅ 已完成预处理，跳过")

            if not state.get('augment', False):
                self.log("🧠 正在增广文本...")
                augment_folder(self.output_path)
                state['augment'] = True
                with open(self.state_path, 'w') as f:
                    json.dump(state, f, indent=2)
            else:
                self.log("✅ 已完成增广，跳过")

            if not state.get('tree', False):
                self.log("🌳 正在构建知识树结构...")
                tree_folder(self.output_path, self.output_path)
                state['tree'] = True
                with open(self.state_path, 'w') as f:
                    json.dump(state, f, indent=2)
            else:
                self.log("✅ 已构建知识树，跳过")

            if not state.get('qa', False):
                self.log("📚 正在生成问答对...")
                self.generate_qa(os.path.join(self.output_path, "graph"))
                state['qa'] = True
                with open(self.state_path, 'w') as f:
                    json.dump(state, f, indent=2)
            else:
                self.log("✅ 已生成问答对，跳过")

            self.log("🎉 全部流程完成！")
        except Exception as e:
            self.log(f"❌ 运行出错: {str(e)}")
        self.finished.emit()

    def generate_qa(self, graph_path):
        kg = KnowledgeGraph()
        kg.load_knowledge_graph(graph_path)
        concepts = list(kg.graph.nodes)
        if not concepts:
            self.log("⚠️ 知识图谱为空，跳过问答生成")
            return
        concept = concepts[0]
        level = "中等"

        generator = KnowledgeQuestionGenerator(
            kg,
            appid="2d1bc910",
            api_key="a1df9334fd048ded0c9304ccf12c20d1",
            api_secret="YzZjODMwNmNjNmRiMDVjOGI4MjcxZDVi"
        )
        generator.generate_and_save(concept=concept, level=level)
        self.log("✅ 问答对生成完成")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduSpark - 一键处理")
        self.resize(600, 400)

        #下面这些也应该设置为可以调整的项目：
        self.input_path = ""
        self.output_path = "./outputs2"
        self.state_path = "./state.json"

        layout = QVBoxLayout()

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)

        self.btn_select_input = QPushButton("📂 选择输入文件夹")
        self.btn_select_input.clicked.connect(self.select_input)

        self.btn_process = QPushButton("🛠 一键处理")
        self.btn_process.clicked.connect(self.run_pipeline)

        layout.addWidget(self.btn_select_input)
        layout.addWidget(self.btn_process)
        layout.addWidget(self.progress)
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def select_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if path:
            self.input_path = path
            self.log_area.append(f"📥 已选择输入路径: {path}")

    def run_pipeline(self):
        if not self.input_path:
            QMessageBox.warning(self, "错误", "请先选择输入文件夹")
            return

        self.log_area.append("🚀 开始处理流程...")
        self.progress.setVisible(True)

        self.thread = PipelineThread(
            input_path=self.input_path,
            output_path=self.output_path,
            state_path=self.state_path
        )
        self.thread.log_signal.connect(self.log_area.append)
        self.thread.finished.connect(self.on_finish)
        self.thread.start()

    def on_finish(self):
        self.progress.setVisible(False)
        QMessageBox.information(self, "完成", "所有任务已完成！")


if __name__ == '__main__':
    from PyQt5.QtCore import QObject
    multiprocessing.freeze_support()  # for Windows
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())