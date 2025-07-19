# qa_selector_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton

class QASelectorDialog(QDialog):
    def __init__(self, concepts: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择知识点与难度")
        self.selected_concept = None
        self.selected_level = "easy"

        layout = QVBoxLayout()

        self.concept_box = QComboBox()
        self.concept_box.addItem("全部知识点")
        self.concept_box.addItems(concepts[:100])  # 防止太多
        layout.addWidget(QLabel("选择知识点："))
        layout.addWidget(self.concept_box)

        self.level_box = QComboBox()
        self.level_box.addItems(["easy", "medium", "hard"])
        layout.addWidget(QLabel("选择难度："))
        layout.addWidget(self.level_box)

        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def get_selection(self):
        concept = self.concept_box.currentText()
        if concept == "全部知识点":
            concept = None
        level = self.level_box.currentText()
        return concept, level

