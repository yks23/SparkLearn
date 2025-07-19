import sys
import os
import json
import multiprocessing
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog,
    QLabel, QTextEdit, QProgressBar, QMessageBox, QHBoxLayout,
    QCheckBox, QGroupBox, QGridLayout
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
    progress_update = pyqtSignal(int)  # 添加进度更新信号

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
            # 加载或初始化状态
            state = {}
            if os.path.exists(self.state_path):
                try:
                    with open(self.state_path, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                except Exception as e:
                    self.log(f"⚠️ 状态文件加载失败: {str(e)}")
                    state = {}

            # 步骤名称映射
            step_names = {
                'preprocess': "🔧 预处理原始文件",
                'augment': "🧠 增广文本",
                'tree': "🌳 构建知识树结构",
                'qa': "📚 生成问答对"
            }
            
            # 步骤处理函数
            steps = {
                'preprocess': lambda: process_folder(self.input_path, self.output_path),
                'augment': lambda: augment_folder(self.output_path),
                'tree': lambda: tree_folder(self.output_path,  os.path.join(self.output_path, "tree")),
                'qa': lambda: self.generate_qa(os.path.join(self.output_path, "tree", "graph"))
            }
            
            # 按顺序执行选中的步骤
            step_order = ['preprocess', 'augment', 'tree', 'qa']
            completed_steps = 0
            total_steps = len(self.selected_steps)
            
            for step in step_order:
                if step in self.selected_steps:
                    step_name = step_names[step]
                    self.log(f"⏳ 正在执行: {step_name}...")
                    
                    # 执行步骤
                    steps[step]()
                    
                    # 更新状态
                    state[step] = True
                    with open(self.state_path, 'w') as f:
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
        generator.generate_and_save(concept=concept, level=level,output_path=self.output_path+"/questions")
        self.log("✅ 问答对生成完成")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduSpark - 处理流程控制")
        self.resize(700, 600)

        # 初始化路径和状态
        self.input_path = ""
        self.output_path = ""
        self.state_path = ""
        self.state = {}

        # 创建UI
        self.create_ui()
        
        # 初始化步骤选择框
        self.update_step_checks()

    def create_ui(self):
        main_layout = QVBoxLayout()
        
        # 输入文件夹选择
        input_group = QGroupBox("输入设置")
        input_layout = QVBoxLayout()
        
        self.input_label = QLabel("未选择输入文件夹")
        btn_select_input = QPushButton("📂 选择输入文件夹")
        btn_select_input.clicked.connect(self.select_input)
        
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(btn_select_input)
        input_group.setLayout(input_layout)
        
        # 输出文件夹选择
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()
        
        self.output_label = QLabel("未选择输出文件夹")
        self.state_label = QLabel("状态文件: 未加载")
        
        btn_select_output = QPushButton("📂 选择输出文件夹")
        btn_select_output.clicked.connect(self.select_output)
        btn_load_state = QPushButton("🔄 加载状态")
        btn_load_state.clicked.connect(self.load_state)
        
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.state_label)
        output_layout.addWidget(btn_select_output)
        output_layout.addWidget(btn_load_state)
        output_group.setLayout(output_layout)
        
        # 步骤选择
        steps_group = QGroupBox("处理步骤选择")
        steps_layout = QGridLayout()
        
        self.step_checks = {
            'preprocess': QCheckBox("🔧 预处理原始文件"),
            'augment': QCheckBox("🧠 增广文本"),
            'tree': QCheckBox("🌳 构建知识树结构"),
            'qa': QCheckBox("📚 生成问答对")
        }
        
        # 添加复选框
        row = 0
        for key, check in self.step_checks.items():
            steps_layout.addWidget(check, row, 0)
            row += 1
        
        steps_group.setLayout(steps_layout)
        
        # 操作按钮
        btn_run = QPushButton("🚀 执行选中的步骤")
        btn_run.clicked.connect(self.run_pipeline)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        self.progress.setValue(0)
        
        # 日志区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        
        # 添加到主布局
        main_layout.addWidget(input_group)
        main_layout.addWidget(output_group)
        main_layout.addWidget(steps_group)
        main_layout.addWidget(btn_run)
        main_layout.addWidget(self.progress)
        main_layout.addWidget(self.log_area)

        self.setLayout(main_layout)
    
    def select_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if path:
            self.input_path = path
            self.input_label.setText(f"输入文件夹: {path}")
            self.log_area.append(f"📥 已选择输入路径: {path}")
    
    def select_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if path:
            self.output_path = path
            self.state_path = os.path.join(path, "state.json")
            self.output_label.setText(f"输出文件夹: {path}")
            self.log_area.append(f"📤 已选择输出路径: {path}")
            self.log_area.append(f"📄 状态文件位置: {self.state_path}")
            
            # 自动尝试加载状态
            self.load_state()
    
    def load_state(self):
        if not self.output_path:
            QMessageBox.warning(self, "错误", "请先选择输出文件夹")
            return
            
        if not os.path.exists(self.state_path):
            self.state = {}
            self.state_label.setText("状态文件: 不存在 (将创建新文件)")
            self.log_area.append("⚠️ 状态文件不存在，将创建新文件")
        else:
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                self.state_label.setText("状态文件: 已加载")
                self.log_area.append("✅ 状态文件加载成功")
            except Exception as e:
                self.state = {}
                self.state_label.setText(f"状态文件: 加载失败 ({str(e)})")
                self.log_area.append(f"❌ 状态文件加载失败: {str(e)}")
        
        # 更新步骤选择框状态
        self.update_step_checks()
    
    def update_step_checks(self):
        for step, check in self.step_checks.items():
            # 移除之前的标记
            text = check.text()
            if text.startswith("✅已完成 ") or text.startswith("❌未完成 "):
                text = text[5:]

            if self.state.get(step, False):
                check.setText(f"✅已完成 {text}")
                check.setChecked(False)
            else:
                check.setText(f"❌未完成 {text}")
                check.setChecked(True)
    
    def get_selected_steps(self):
        return [step for step, check in self.step_checks.items() if check.isChecked()]
    
    def run_pipeline(self):
        if not self.input_path:
            QMessageBox.warning(self, "错误", "请先选择输入文件夹")
            return
        if not self.output_path:
            QMessageBox.warning(self, "错误", "请先选择输出文件夹")
            return
            
        selected_steps = self.get_selected_steps()
        if not selected_steps:
            QMessageBox.warning(self, "错误", "请至少选择一个处理步骤")
            return
            
        self.log_area.append("🚀 开始处理流程...")
        self.log_area.append(f"📋 选中的步骤: {', '.join(selected_steps)}")
        self.progress.setVisible(True)
        self.progress.setValue(0)

        self.thread = PipelineThread(
            input_path=self.input_path,
            output_path=self.output_path,
            state_path=self.state_path,
            selected_steps=selected_steps
        )
        self.thread.log_signal.connect(self.log_area.append)
        self.thread.finished.connect(self.on_finish)
        self.thread.progress_update.connect(self.progress.setValue)
        self.thread.start()
    
    def on_finish(self):
        self.progress.setVisible(False)
        self.load_state()  # 重新加载状态以更新UI
        QMessageBox.information(self, "完成", "所选步骤处理完成！")


if __name__ == '__main__':
    multiprocessing.freeze_support()  # for Windows
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())