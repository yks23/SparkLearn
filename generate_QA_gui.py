# generate_QA_gui.py
import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from qg.graph_class import KnowledgeGraph, KnowledgeQuestionGenerator

from PyQt5.QtCore import QObject

class QtLogger(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def write(self, msg):
        msg = str(msg).strip()
        if msg:
            self.log_signal.emit(msg)

    def flush(self):
        pass


class QAWorker(QThread):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, kg, concept=None, level=None, parent=None):
        super().__init__(parent)
        self.kg = kg
        self.concept = concept
        self.level = level

    def run(self):
        try:
            generator = KnowledgeQuestionGenerator(
                self.kg,
                appid="2d1bc910",
                api_key="a1df9334fd048ded0c9304ccf12c20d1",
                api_secret="YzZjODMwNmNjNmRiMDVjOGI4MjcxZDVi"
            )
            generator.generate_and_save(concept=self.concept, level=self.level)
            self.log_signal.emit("✅ 题目生成完成")
        except Exception as e:
            self.log_signal.emit(f"❌ 错误: {str(e)}")
        self.finished.emit()



class QAWindow(QWidget):
    def __init__(self, graph_path, output_path, auto_close=True):
        super().__init__()
        self.graph_path = graph_path
        self.output_path = output_path
        self.auto_close = auto_close

        self.setWindowTitle("生成问答对")
        self.resize(800, 500)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.text_area)
        self.setLayout(layout)

        # 设置日志系统
        self.logger = QtLogger()
        self.logger.log_signal.connect(self.append_log)
        sys.stdout = self.logger
        sys.stderr = self.logger

        # ✅ 延迟启动：等 UI 完全 show 后再运行主流程
        QTimer.singleShot(100, self.start_interaction)

    def append_log(self, msg):
        self.text_area.append(str(msg))

    def start_interaction(self):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox

        # 加载知识图谱
        self.kg = KnowledgeGraph()
        self.kg.load_knowledge_graph(self.graph_path)

        # 用户选择知识点
        concepts = list(self.kg.graph.nodes)
        if not concepts:
            QMessageBox.warning(self, "错误", "知识图谱为空")
            self.close()
            return

        concept, ok = QInputDialog.getItem(self, "选择知识点", "请选择一个知识点", concepts, 0, False)
        if not ok:
            self.close()
            return

        levels = ["简单", "中等", "困难"]
        level, ok = QInputDialog.getItem(self, "选择难度", "请选择难度", levels, 1, False)
        if not ok:
            self.close()
            return

        self.start_worker(concept, level)

    def start_worker(self, concept, level):
        self.worker = QAWorker(self.kg, concept=concept, level=level)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished.connect(lambda: QTimer.singleShot(2000, self.close) if self.auto_close else None)
        self.worker.start()



def launch_QA_gui(graph_path, output_path):
    app = QApplication(sys.argv)
    window = QAWindow(graph_path, output_path)
    window.show()
    app.exec_()
