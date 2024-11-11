from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QComboBox, QProgressBar, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import sys
import os
from pathlib import Path
from src.utils.pdf_converter import PDFConverter
from src.api.ocr_service import OCRService

class ProcessingThread(QThread):
    """处理线程，避免GUI卡死"""
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, pdf_path, output_path, api_key, model):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.api_key = api_key
        self.model = model
        self.pdf_converter = PDFConverter()
        self.ocr_service = OCRService()

    def run(self):
        try:
            # 创建临时目录
            temp_dir = Path(self.pdf_path).parent / "temp_images"
            
            # 转换PDF
            self.progress_updated.emit(10, "正在转换PDF...")
            image_paths = self.pdf_converter.convert_pdf(self.pdf_path, temp_dir)
            
            # OCR处理
            self.progress_updated.emit(30, "正在进行OCR识别...")
            results = self.ocr_service.process_images(
                image_paths,
                self.api_key,
                self.model
            )
            
            # 保存结果
            self.progress_updated.emit(90, "正在保存结果...")
            self.ocr_service.save_results(results, self.output_path)
            
            # 清理临时文件
            self.pdf_converter.cleanup_temp_files(image_paths)
            if temp_dir.exists():
                temp_dir.rmdir()
            
            self.finished.emit(True, "处理完成")
            
        except Exception as e:
            self.finished.emit(False, str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF OCR 工具")
        self.setMinimumWidth(600)
        self.setMinimumHeight(300)
        self._setup_ui()

    def _setup_ui(self):
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # PDF文件选择
        pdf_layout = QHBoxLayout()
        self.pdf_path_edit = QLineEdit()
        self.pdf_path_edit.setPlaceholderText("选择PDF文件...")
        pdf_button = QPushButton("浏览")
        pdf_button.clicked.connect(self._select_pdf)
        pdf_layout.addWidget(QLabel("PDF文件:"))
        pdf_layout.addWidget(self.pdf_path_edit)
        pdf_layout.addWidget(pdf_button)
        layout.addLayout(pdf_layout)

        # API Key输入
        api_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("输入API Key...")
        api_layout.addWidget(QLabel("API Key:"))
        api_layout.addWidget(self.api_key_edit)
        layout.addLayout(api_layout)

        # 模型选择
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems(["qwen-vl-plus-0809", "qwen-vl-max-0809"])
        model_layout.addWidget(QLabel("选择模型:"))
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # 输出路径选择
        output_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择输出位置...")
        output_button = QPushButton("浏览")
        output_button.clicked.connect(self._select_output)
        output_layout.addWidget(QLabel("输出位置:"))
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(output_button)
        layout.addLayout(output_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # 开始按钮
        self.start_button = QPushButton("开始处理")
        self.start_button.clicked.connect(self._start_processing)
        layout.addWidget(self.start_button)

    def _select_pdf(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf)"
        )
        if filename:
            self.pdf_path_edit.setText(filename)
            # 自动设置输出路径
            output_path = str(Path(filename).with_suffix('.md'))
            self.output_path_edit.setText(output_path)

    def _select_output(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "选择保存位置",
            "",
            "Markdown文件 (*.md)"
        )
        if filename:
            self.output_path_edit.setText(filename)

    def _validate_inputs(self):
        if not self.pdf_path_edit.text():
            QMessageBox.warning(self, "错误", "请选择PDF文件")
            return False
        if not self.api_key_edit.text():
            QMessageBox.warning(self, "错误", "请输入API Key")
            return False
        if not self.output_path_edit.text():
            QMessageBox.warning(self, "错误", "请选择输出位置")
            return False
        return True

    def _start_processing(self):
        if not self._validate_inputs():
            return

        # 禁用开始按钮
        self.start_button.setEnabled(False)
        self.progress_bar.setValue(0)

        # 创建并启动处理线程
        self.processing_thread = ProcessingThread(
            self.pdf_path_edit.text(),
            self.output_path_edit.text(),
            self.api_key_edit.text(),
            self.model_combo.currentText()
        )
        self.processing_thread.progress_updated.connect(self._update_progress)
        self.processing_thread.finished.connect(self._process_finished)
        self.processing_thread.start()

    def _update_progress(self, value, status):
        self.progress_bar.setValue(value)
        self.status_label.setText(status)

    def _process_finished(self, success, message):
        self.start_button.setEnabled(True)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            # 检查是否生成了输出文件
            if os.path.exists(self.output_path_edit.text()):
                QMessageBox.information(self, "完成", "文件处理完成！")
            else:
                QMessageBox.warning(self, "警告", "文件可能未完全处理，请检查输出文件。")
        else:
            # 如果错误信息包含临时文件清理的警告，但文件已经处理完成
            if "Directory not empty" in message and os.path.exists(self.output_path_edit.text()):
                QMessageBox.information(self, "完成", "文件处理完成！\n(清理临时文件时出现警告，但不影响结果)")
            else:
                QMessageBox.critical(self, "错误", f"处理失败：{message}")
        
        self.status_label.setText("就绪" if success else "处理失败")