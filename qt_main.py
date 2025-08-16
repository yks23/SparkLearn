# qt_main.py  ——  已删除“打开处理后文本”按钮
import sys
import os
import json
import multiprocessing
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
    QLabel, QTextEdit, QProgressBar, QMessageBox, QCheckBox, QGroupBox,
    QGridLayout, QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QUrl
from PyQt5.QtGui import QPixmap, QDesktopServices
from main import process_folder, augment_folder, tree_folder
from qg.graph_class import KnowledgeGraph, KnowledgeQuestionGenerator
from config import APISecret, APIKEY, APPID

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
    progress_update = pyqtSignal(int)
    kg_ready = pyqtSignal(str)

    def __init__(self, input_path, output_path, state_path, selected_steps, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.state_path = state_path
        self.selected_steps = selected_steps

    def log(self, msg):
        self.log_signal.emit(str(msg))

    def run(self):
        try:
            state = {}
            if os.path.exists(self.state_path):
                try:
                    with open(self.state_path, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                except Exception as e:
                    self.log(f"⚠️ 状态文件加载失败: {str(e)}")
                    state = {}

            step_names = {
                'preprocess': "🔧 预处理原始文件",
                'augment': "🧠 增广文本",
                'tree': "🌳 构建知识树结构"
            }

            steps = {
                'preprocess': lambda: process_folder(self.input_path, self.output_path),
                'augment': lambda: augment_folder(self.output_path),
                'tree': lambda: self.run_tree_step()
            }

            step_order = ['preprocess', 'augment', 'tree']
            completed_steps = 0
            total_steps = len(self.selected_steps)

            for step in step_order:
                if step in self.selected_steps:
                    step_name = step_names[step]
                    self.log(f"⏳ 正在执行: {step_name}...")
                    steps[step]()
                    state[step] = True
                    with open(self.state_path, 'w', encoding='utf-8') as f:
                        json.dump(state, f, indent=2)
                    self.log(f"✅ 完成: {step_name}")
                    completed_steps += 1
                    self.progress_update.emit(int(100 * completed_steps / total_steps))
                else:
                    if state.get(step, False):
                        self.log(f"⏭️ 跳过已完成的步骤: {step_names[step]}")

            self.log("🎉 全部流程完成！")
        except Exception as e:
            import traceback
            self.log(f"❌ 运行出错: {str(e)}\n{traceback.format_exc()}")
        finally:
            self.finished.emit()

    def run_tree_step(self):
        tree_output = os.path.join(self.output_path, "tree")
        tree_folder(self.output_path, tree_output)
        graph_dir = os.path.join(tree_output, "graph")
        os.makedirs(graph_dir, exist_ok=True)
        kg = KnowledgeGraph()
        kg.load_knowledge_graph(graph_dir)
        graph_png = os.path.join(graph_dir, "graph.png")
        kg.visualize(graph_png)
        self.log(f"知识图谱已构建并可视化在: {graph_png}")
        self.kg_ready.emit(graph_dir)


class QAGenerationThread(QThread):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, graph_path, concept, difficulty, output_path, parent=None):
        super().__init__(parent)
        self.graph_path = graph_path
        self.concept = concept
        self.difficulty = difficulty
        self.output_path = output_path

    def run(self):
        try:
            self.log_signal.emit(f"⏳ 正在生成问答对，使用知识图谱: {self.graph_path}")
            self.log_signal.emit(f"🔧 知识点: {self.concept}, 难度: {self.difficulty}")

            kg = KnowledgeGraph()
            kg.load_knowledge_graph(self.graph_path)
            self.log_signal.emit(f"✅ 知识图谱加载完成，共 {len(kg.graph.nodes)} 个节点")

            generator = KnowledgeQuestionGenerator(
                kg,
                appid=APPID,
                api_key=APIKEY,
                api_secret=APISecret
            )

            qa_output_path = os.path.join(self.output_path, "qa")
            os.makedirs(qa_output_path, exist_ok=True)
            generator.generate_and_save(
                output_path=qa_output_path,
                concept=self.concept,
                level=self.difficulty.lower()
            )

            self.log_signal.emit(f"✅ 问答对已生成在: {qa_output_path}")
            self.finished.emit(True)
        except Exception as e:
            self.log_signal.emit(f"❌ 生成问答对失败: {str(e)}")
            self.finished.emit(False)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SparkLearn")
        self.resize(1200, 850)

        self.input_path = ""
        self.output_path = ""
        self.state_path = ""
        self.state = {}
        self.graph_path = ""
        self.init_ui()
        self.update_step_checks()
        self.update_button_states()

    # ---------- UI ----------
    def init_ui(self):
        main = QHBoxLayout(self)

        # 左栏
        left = QVBoxLayout()

        # 输入
        in_group = QGroupBox("输入设置")
        in_box = QVBoxLayout()
        self.input_label = QLabel("未选择输入")
        btn_file = QPushButton("📄 选择输入文件")
        btn_folder = QPushButton("📂 选择输入文件夹")
        btn_file.clicked.connect(lambda: self.select_input(file_mode=True))
        btn_folder.clicked.connect(lambda: self.select_input(file_mode=False))
        in_box.addWidget(self.input_label)
        in_box.addWidget(btn_file)
        in_box.addWidget(btn_folder)
        in_group.setLayout(in_box)

        # 输出
        out_group = QGroupBox("输出设置")
        out_box = QVBoxLayout()
        self.output_label = QLabel("未选择输出文件夹")
        self.state_label = QLabel("状态文件: 未加载")
        btn_out = QPushButton("📁 选择输出文件夹")
        btn_out.clicked.connect(self.select_output)
        btn_load = QPushButton("🔄 加载状态")
        btn_load.clicked.connect(self.load_state)
        out_box.addWidget(self.output_label)
        out_box.addWidget(self.state_label)
        out_box.addWidget(btn_out)
        out_box.addWidget(btn_load)
        out_group.setLayout(out_box)

        # 步骤
        step_group = QGroupBox("处理步骤")
        step_grid = QGridLayout()
        self.step_checks = {
            'preprocess': QCheckBox("🔧 预处理原始文件"),
            'augment': QCheckBox("🧠 增广文本"),
            'tree': QCheckBox("🌳 构建知识树结构")
        }
        for r, (k, chk) in enumerate(self.step_checks.items()):
            step_grid.addWidget(chk, r, 0)
        step_group.setLayout(step_grid)

        # 运行按钮 + 进度
        self.btn_run = QPushButton("🚀 执行选中的步骤")
        self.btn_run.clicked.connect(self.run_pipeline)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)

        # 题目生成
        qa_group = QGroupBox("题目生成")
        qa_grid = QGridLayout()
        qa_grid.addWidget(QLabel("知识点:"), 0, 0)
        self.concept_combo = QComboBox()
        self.concept_combo.setEnabled(False)
        qa_grid.addWidget(self.concept_combo, 0, 1)
        qa_grid.addWidget(QLabel("难度:"), 1, 0)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["简单", "中等", "困难"])
        self.difficulty_combo.setEnabled(False)
        qa_grid.addWidget(self.difficulty_combo, 1, 1)
        self.btn_generate_qa = QPushButton("📝 生成题目")
        self.btn_generate_qa.setEnabled(False)
        self.btn_generate_qa.clicked.connect(self.generate_qa)
        qa_grid.addWidget(self.btn_generate_qa, 2, 0, 1, 2)
        qa_group.setLayout(qa_grid)

        # 浏览按钮（仅保留“打开输出根目录”）
        browse_box = QHBoxLayout()
        self.btn_open_out = QPushButton("📂 打开输出根目录")
        self.btn_open_out.clicked.connect(lambda: self.open_path(self.output_path))
        browse_box.addWidget(self.btn_open_out)

        # 日志
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # 组装左栏
        left.addWidget(in_group)
        left.addWidget(out_group)
        left.addWidget(step_group)
        left.addWidget(self.btn_run)
        left.addWidget(self.progress)
        left.addWidget(qa_group)
        left.addLayout(browse_box)
        left.addWidget(self.log_area, stretch=1)

        # 右栏：知识图谱预览
        right = QVBoxLayout()
        right.addWidget(QLabel("知识图谱预览"))
        self.kg_label = QLabel("暂无图谱")
        self.kg_label.setAlignment(Qt.AlignCenter)
        self.kg_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.kg_label.setMinimumWidth(500)
        self.kg_label.setStyleSheet("border:1px solid #aaa;")
        right.addWidget(self.kg_label, stretch=1)

        main.addLayout(left, 1)
        main.addLayout(right, 1)

    # ---------- 功能 ----------
    def select_input(self, file_mode=True):
        if file_mode:
            path, _ = QFileDialog.getOpenFileName(self, "选择输入文件")
        else:
            path = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if path:
            self.input_path = path
            self.input_label.setText(f"输入路径: {path}")

    def select_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if path:
            self.output_path = path
            self.state_path = os.path.join(path, "state.json")
            self.output_label.setText(f"输出文件夹: {path}")
            self.load_state()
            self.start_load_kg_if_ready()

    def load_state(self):
        if not self.output_path:
            return
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                    self.state_label.setText("状态文件: 已加载")
            else:
                self.state = {}
                self.state_label.setText("状态文件: 不存在")
        except Exception as e:
            self.state = {}
            self.state_label.setText(f"状态文件: 加载失败 ({e})")
        self.update_step_checks()
        self.update_button_states()
        self.start_load_kg_if_ready()

    def start_load_kg_if_ready(self):
        """同步加载/补图，日志输出"""
        graph_dir = os.path.join(self.output_path, "tree", "graph")
        if not (self.state.get('tree', False) and os.path.isdir(graph_dir)):
            return

        graph_png = os.path.join(graph_dir, "graph.png")
        try:
            self.log_area.append("⏳ 检查知识图谱…")
            kg = KnowledgeGraph()
            kg.load_knowledge_graph(graph_dir)

            if not os.path.isfile(graph_png):
                self.log_area.append("🖼️ 缺少 graph.png，正在生成…")
                kg.visualize(graph_png)
                self.log_area.append("✅ 图谱图片已生成")

            self.display_kg(graph_png)
            self.graph_path = graph_dir
            self.load_knowledge_graph()
            self.update_button_states()
        except Exception as e:
            self.log_area.append(f"❌ 加载图谱失败: {e}")

    def update_step_checks(self):
        for step, chk in self.step_checks.items():
            text = chk.text()
            if text.startswith("✅") or text.startswith("❌"):
                text = text[5:]
            if self.state.get(step, False):
                chk.setText(f"✅已完成 {text}")
                chk.setChecked(False)
            else:
                chk.setText(f"❌未完成 {text}")
                chk.setChecked(True)

    def update_button_states(self):
        tree_done = self.state.get('tree', False)
        has_concepts = self.concept_combo.count() > 0
        self.btn_generate_qa.setEnabled(tree_done and has_concepts)

    def get_selected_steps(self):
        return [k for k, chk in self.step_checks.items() if chk.isChecked()]

    def run_pipeline(self):
        if not self.input_path or not self.output_path:
            QMessageBox.warning(self, "错误", "请先选择输入和输出路径")
            return
        steps = self.get_selected_steps()
        if not steps:
            QMessageBox.warning(self, "错误", "请至少选择一个处理步骤")
            return
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.thread = PipelineThread(self.input_path, self.output_path, self.state_path, steps)
        self.thread.log_signal.connect(self.log_area.append)
        self.thread.progress_update.connect(self.progress.setValue)
        self.thread.kg_ready.connect(self.on_kg_ready)
        self.thread.finished.connect(self.on_finish)
        self.thread.start()

    def on_kg_ready(self, graph_path):
        self.graph_path = graph_path
        graph_png = os.path.join(graph_path, "graph.png")
        self.display_kg(graph_png)
        self.start_load_kg_if_ready()

    def display_kg(self, img_path):
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            self.kg_label.setPixmap(pixmap.scaled(
                self.kg_label.width(), self.kg_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.kg_label.setText("图谱文件不存在")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'graph_path') and self.graph_path:
            graph_png = os.path.join(self.graph_path, "graph.png")
            self.display_kg(graph_png)

    def generate_qa(self):
        if not self.graph_path:
            QMessageBox.warning(self, "错误", "知识图谱尚未准备好")
            return
        concept = self.concept_combo.currentText()
        difficulty = self.difficulty_combo.currentText()
        if not concept:
            QMessageBox.warning(self, "错误", "请选择一个知识点")
            return
        self.concept_combo.setEnabled(False)
        self.difficulty_combo.setEnabled(False)
        self.btn_generate_qa.setEnabled(False)
        self.qa_thread = QAGenerationThread(
            self.graph_path, concept, difficulty, self.output_path)
        self.qa_thread.log_signal.connect(self.log_area.append)
        self.qa_thread.finished.connect(self.on_qa_finished)
        self.qa_thread.start()

    def on_qa_finished(self, success):
        self.concept_combo.setEnabled(True)
        self.difficulty_combo.setEnabled(True)
        self.btn_generate_qa.setEnabled(True)
        if success:
            QMessageBox.information(self, "完成", "题目生成成功！")
        else:
            QMessageBox.warning(self, "错误", "题目生成失败，请查看日志")

    def on_finish(self):
        self.progress.setVisible(False)
        self.load_state()
        QMessageBox.information(self, "完成", "所选步骤处理完成！")

    def open_path(self, path):
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "错误", f"路径不存在:\n{path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def load_knowledge_graph(self):
        """填充知识点并解锁控件"""
        try:
            kg = KnowledgeGraph()
            kg.load_knowledge_graph(self.graph_path)
            concepts = list(kg.graph.nodes)
            self.concept_combo.clear()
            self.concept_combo.addItems(concepts)
            self.concept_combo.setEnabled(True)
            self.difficulty_combo.setEnabled(True)
            self.log_area.append(f"📚 已加载 {len(concepts)} 个知识点")
        except Exception as e:
            self.log_area.append(f"❌ 加载知识点失败: {e}")


if __name__ == '__main__':
    # 设置环境变量来解决Qt插件问题
    os.environ['QT_QPA_PLATFORM'] = 'cocoa'  # macOS专用
    os.environ['QT_MAC_WANTS_LAYER'] = '1'
    
    # 禁用Qt插件的警告
    os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'
    
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())