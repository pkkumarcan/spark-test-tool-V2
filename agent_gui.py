#!/usr/bin/env python3
"""
Agent Visual Feedback Loop GUI
A Python desktop application that serves as a visual feedback loop for local multimodal coding agents.
Uses PyQt6, PyQt6-WebEngine, and httpx to communicate with a local Ollama instance.
"""

import sys
import os
import re
import json
import base64
import httpx
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QUrl, QTimer, QSize, QByteArray, QBuffer, QIODevice
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QPlainTextEdit, QPushButton, QLineEdit, QLabel, QTextEdit, QMessageBox,
    QGroupBox, QFormLayout, QStatusBar, QComboBox, QHBoxLayout
)
from PyQt6.QtGui import (
    QFont, QPixmap, QImage, QTextCursor, QPainter, QColor, QTextFormat
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

# --- Styling & Colors (Catppuccin Mocha Palette) ---
STYLE_SHEET = """
QMainWindow {
    background-color: #1e1e2e;
}
QWidget {
    color: #cdd6f4;
    font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
    font-size: 13px;
}
QSplitter::handle {
    background-color: #313244;
}
QSplitter::handle:hover {
    background-color: #cba6f7;
}
QPlainTextEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 2px;
}
QTextEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 6px;
}
QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #cba6f7;
}
QLineEdit:focus {
    border: 1px solid #cba6f7;
}
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px;
    min-width: 150px;
}
QComboBox:focus {
    border: 1px solid #cba6f7;
}
QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    color: #cdd6f4;
    selection-background-color: #cba6f7;
    selection-color: #11111b;
    border: 1px solid #313244;
}
QPushButton {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: bold;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
}
QPushButton:hover {
    background-color: #b4befe;
}
QPushButton:pressed {
    background-color: #74c7ec;
}
QPushButton:disabled {
    background-color: #45475a;
    color: #585b70;
}
QPushButton#btn_autofix {
    background-color: #a6e3a1;
    color: #11111b;
}
QPushButton#btn_autofix:hover {
    background-color: #94e2d5;
}
QPushButton#btn_autofix:pressed {
    background-color: #89dceb;
}
QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 3px 0 3px;
    color: #bac2de;
}
QStatusBar {
    background-color: #11111b;
    color: #a6adc8;
}
"""

DEFAULT_HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Agent Test Page</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0c20 0%, #15102a 50%, #241442 100%);
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        .container {
            text-align: center;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 40px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 90%;
        }
        h1 {
            color: #cba6f7;
            margin-bottom: 10px;
            font-size: 2.5rem;
            text-shadow: 0 0 10px rgba(203, 166, 247, 0.5);
        }
        p {
            color: #cdd6f4;
            font-size: 1.1rem;
            line-height: 1.6;
        }
        .btn {
            background-color: #a6e3a1;
            color: #11111b;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
            box-shadow: 0 4px 15px rgba(166, 227, 161, 0.4);
        }
        .btn:hover {
            background-color: #89b4fa;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(137, 180, 250, 0.6);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hello from Gemma 4!</h1>
        <p>This is a starting template. Edit the code in the left panel or type a prompt and click <b>Agent Auto-Fix</b> to let the visual agent modify this view.</p>
        <button class="btn">Click Me</button>
    </div>
</body>
</html>
"""

DEFAULT_SYSTEM_PROMPT = """You are an expert Frontend Web Developer coding agent.
Your objective is to modify the provided HTML/CSS/JS code to satisfy the user's goal, correcting any visual defects shown in the screenshot.

Instructions:
1. Review the current code and the screenshot of its rendering.
2. Produce updated, clean, and fully functional HTML.
3. Keep all external script links or assets intact unless asked to change them.
4. You MUST output the complete updated HTML document.
5. Do NOT include explanations, comments, or chat about the changes.
6. Return the updated code wrapped in a single ```html ... ``` code block.
"""

def extract_html(response_text: str) -> str:
    """Robust helper to extract HTML code blocks from a model's response."""
    # Look for ```html ... ```
    match = re.search(r"```html\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Look for any ``` ... ```
    match = re.search(r"```\s*(.*?)\s*```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
        
    # Check if there are HTML markers in the text
    if "<html" in response_text.lower() or "<!doctype" in response_text.lower():
        start_idx = re.search(r"(<!doctype|<html)", response_text, re.IGNORECASE)
        end_idx = response_text.lower().rfind("</html>")
        if start_idx and end_idx != -1:
            return response_text[start_idx.start():end_idx + 7].strip()
            
    return response_text.strip()


# --- Line Number Gutter Widget ---
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


# --- Monospace Code Editor with Line Numbers ---
class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        
        # Configure Monospace Font
        font = QFont("Fira Code", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Tab settings (4 spaces)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = 1
        max_val = max(1, self.blockCount())
        while max_val >= 10:
            max_val /= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#181825")) # Gutter bg
        
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                # If current block is active, highlight its number
                if blockNumber == self.textCursor().blockNumber():
                    painter.setPen(QColor("#cba6f7")) # Lavender
                else:
                    painter.setPen(QColor("#585b70")) # Muted grey
                
                painter.drawText(0, top, self.lineNumberArea.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor("#313244")
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)


# --- Asynchronous Worker Thread for Ollama calls ---
class OllamaWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    log_signal = pyqtSignal(str)

    def __init__(self, api_url, model_name, system_prompt, user_goal, html_code, base64_image):
        super().__init__()
        self.api_url = api_url.rstrip('/')
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.user_goal = user_goal
        self.html_code = html_code
        self.base64_image = base64_image

    def run(self):
        try:
            self.log_signal.emit("Connecting to Ollama API...")
            chat_url = f"{self.api_url}/api/chat"
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"User Goal: {self.user_goal}\n\nHere is the current HTML code:\n{self.html_code}\n\nReview the provided screenshot (representing the visual render of the current code) and apply the changes to fulfill the goal.",
                        "images": [self.base64_image]
                    }
                ],
                "stream": False
            }
            
            self.log_signal.emit(f"Sending request to model '{self.model_name}'...")
            
            headers = {"Content-Type": "application/json"}
            with httpx.Client(timeout=180.0) as client:
                response = client.post(chat_url, json=payload, headers=headers)
                
            if response.status_code != 200:
                self.error.emit(f"Ollama returned status code {response.status_code}: {response.text}")
                return
                
            data = response.json()
            message_content = data.get("message", {}).get("content", "")
            
            if not message_content:
                self.error.emit("Received empty content from Ollama model.")
                return
                
            self.finished.emit(message_content)
            
        except httpx.ConnectError:
            self.error.emit(f"Could not connect to Ollama at {self.api_url}. Is Ollama running?")
        except Exception as e:
            self.error.emit(f"Error during Ollama call: {str(e)}")


# --- Main Application Window ---
class AgentVisualLoopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Agent Visual Feedback Loop")
        self.resize(1280, 800)
        self.setStyleSheet(STYLE_SHEET)
        
        # Debounce timer for auto-rendering
        self.render_timer = QTimer(self)
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.render_preview)
        
        self.init_ui()
        self.load_starter_code()
        
        # Poll models on startup
        QTimer.singleShot(100, self.fetch_models)

    def init_ui(self):
        # Central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # Main vertical layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 1. Splitter for Editor & Previewer
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel (Editor)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        lbl_editor = QLabel("Source Code Editor (HTML/CSS/JS)")
        lbl_editor.setStyleSheet("font-weight: bold; color: #bac2de;")
        self.editor = CodeEditor()
        self.editor.textChanged.connect(self.on_text_changed)
        left_layout.addWidget(lbl_editor)
        left_layout.addWidget(self.editor)
        splitter.addWidget(left_widget)
        
        # Right Panel (Web View)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        lbl_preview = QLabel("Live Web Preview (QWebEngineView)")
        lbl_preview.setStyleSheet("font-weight: bold; color: #bac2de;")
        self.web_view = QWebEngineView()
        right_layout.addWidget(lbl_preview)
        right_layout.addWidget(self.web_view)
        splitter.addWidget(right_widget)
        
        # Adjust default sizes (50/50 split)
        splitter.setSizes([640, 640])
        main_layout.addWidget(splitter, stretch=3)
        
        # 2. Goal Input Section
        goal_group = QGroupBox("Define Agent Goal / Instructions")
        goal_layout = QVBoxLayout(goal_group)
        self.txt_goal = QTextEdit()
        self.txt_goal.setPlaceholderText("Describe the modifications you want the AI agent to make (e.g., 'Change the button color to vibrant blue, align the box to the center, and make the background dark dark blue')...")
        self.txt_goal.setMaximumHeight(80)
        goal_layout.addWidget(self.txt_goal)
        main_layout.addWidget(goal_group)
        
        # 3. Settings & Commands Bar
        settings_group = QGroupBox("Configuration & Execution")
        settings_layout = QHBoxLayout(settings_group)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        
        # Forms layout for inputs
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        self.txt_url = QLineEdit()
        self.txt_url.setText("http://localhost:11434")
        self.txt_url.setToolTip("URL to your local Ollama server")
        
        # Combo box for model selection
        model_hbox = QHBoxLayout()
        self.cb_model = QComboBox()
        self.cb_model.setEditable(True)
        self.cb_model.setToolTip("Select or type the name of the Ollama model")
        
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(40)
        btn_refresh.setToolTip("Refresh models list from Ollama")
        btn_refresh.clicked.connect(self.fetch_models)
        
        model_hbox.addWidget(self.cb_model)
        model_hbox.addWidget(btn_refresh)
        
        form_layout.addRow(QLabel("Ollama API URL:"), self.txt_url)
        form_layout.addRow(QLabel("Ollama Model:"), model_hbox)
        settings_layout.addWidget(form_widget, stretch=1)
        
        # Commands layout for buttons
        buttons_widget = QWidget()
        buttons_layout = QVBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)
        
        self.btn_render = QPushButton("Render Preview")
        self.btn_render.clicked.connect(self.render_preview)
        
        self.btn_autofix = QPushButton("Agent Auto-Fix")
        self.btn_autofix.setObjectName("btn_autofix")
        self.btn_autofix.setToolTip("Capture screenshot, send current code + screenshot to AI, and apply fix")
        self.btn_autofix.clicked.connect(self.trigger_autofix)
        
        self.btn_clear_logs = QPushButton("Clear Output Console")
        self.btn_clear_logs.clicked.connect(self.clear_logs)
        
        buttons_layout.addWidget(self.btn_render)
        buttons_layout.addWidget(self.btn_autofix)
        buttons_layout.addWidget(self.btn_clear_logs)
        settings_layout.addWidget(buttons_widget, stretch=1)
        
        main_layout.addWidget(settings_group)
        
        # 4. Output / Logs Console
        logs_group = QGroupBox("System Output Console")
        logs_layout = QVBoxLayout(logs_group)
        self.txt_logs = QPlainTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setMaximumHeight(120)
        logs_layout.addWidget(self.txt_logs)
        main_layout.addWidget(logs_group)
        
        # 5. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def load_starter_code(self):
        self.editor.setPlainText(DEFAULT_HTML_CONTENT)
        self.render_preview()

    def on_text_changed(self):
        # Debounce writing and rendering
        self.render_timer.start(500)

    def render_preview(self):
        code = self.editor.toPlainText()
        try:
            temp_path = os.path.abspath("temp_render.html")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Force QWebEngineView to load and display the local HTML file
            file_url = QUrl.fromLocalFile(temp_path)
            self.web_view.setUrl(file_url)
            self.log("Preview rendered and written to 'temp_render.html'.")
        except Exception as e:
            self.log(f"Error rendering preview: {str(e)}")

    def log(self, text):
        self.txt_logs.appendPlainText(text)
        # Scroll to bottom
        self.txt_logs.moveCursor(QTextCursor.MoveOperation.End)

    def clear_logs(self):
        self.txt_logs.clear()

    def fetch_models(self):
        api_url = self.txt_url.text().strip()
        self.log(f"Fetching models from {api_url}/api/tags...")
        try:
            response = httpx.get(f"{api_url}/api/tags", timeout=2.0)
            if response.status_code == 200:
                models_data = response.json().get("models", [])
                model_names = [m.get("name") for m in models_data]
                
                # Keep track of current text
                current_sel = self.cb_model.currentText()
                
                self.cb_model.clear()
                self.cb_model.addItems(model_names)
                
                # Re-select previous choice or default
                if current_sel in model_names:
                    self.cb_model.setCurrentText(current_sel)
                elif "gemma:4" in model_names:
                    self.cb_model.setCurrentText("gemma:4")
                elif model_names:
                    self.cb_model.setCurrentIndex(0)
                else:
                    self.cb_model.setCurrentText("gemma:4")
                    
                self.log(f"Found {len(model_names)} models: {', '.join(model_names)}")
            else:
                self.log(f"Error fetching models: status code {response.status_code}")
                self.populate_fallback_models()
        except Exception as e:
            self.log(f"Could not reach Ollama to load models: {str(e)}")
            self.populate_fallback_models()

    def populate_fallback_models(self):
        if self.cb_model.count() == 0:
            self.cb_model.addItems(["gemma:4", "gemma2", "llava", "minicpm-v"])
            self.cb_model.setCurrentText("gemma:4")

    def set_controls_enabled(self, enabled):
        self.editor.setEnabled(enabled)
        self.txt_goal.setEnabled(enabled)
        self.btn_render.setEnabled(enabled)
        self.btn_autofix.setEnabled(enabled)
        self.txt_url.setEnabled(enabled)
        self.cb_model.setEnabled(enabled)

    def trigger_autofix(self):
        goal = self.txt_goal.toPlainText().strip()
        if not goal:
            QMessageBox.warning(self, "Missing Goal", "Please enter instructions in the 'Define Agent Goal' section.")
            return

        self.set_controls_enabled(False)
        self.log("\n--- Starting Agent Auto-Fix ---")
        self.status_bar.showMessage("Capturing screenshot of preview...")
        
        # 1. Grab screenshot of only the QWebEngineView widget
        try:
            # Grab the widget's content
            pixmap = self.web_view.grab()
            
            # Save screenshot to disk (for verification and debug)
            screenshot_path = os.path.abspath("vision_frame.png")
            pixmap.save(screenshot_path, "PNG")
            self.log(f"Screenshot saved to {screenshot_path}")
            
            # Convert pixmap directly in-memory to base64 encoding
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")
            img_base64 = base64.b64encode(byte_array.data()).decode("utf-8")
        except Exception as e:
            self.log(f"Failed to capture screenshot: {str(e)}")
            self.set_controls_enabled(True)
            self.status_bar.showMessage("Capture failed.")
            return

        # 2. Get parameters
        api_url = self.txt_url.text().strip()
        model_name = self.cb_model.currentText().strip()
        current_code = self.editor.toPlainText()

        self.log(f"Preparing to send payload to local model: {model_name}")
        self.status_bar.showMessage("Running Ollama Agent...")

        # 3. Create worker thread to keep main GUI thread responsive
        self.worker = OllamaWorker(
            api_url=api_url,
            model_name=model_name,
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            user_goal=goal,
            html_code=current_code,
            base64_image=img_base64
        )
        
        self.worker.log_signal.connect(self.log)
        self.worker.finished.connect(self.on_autofix_finished)
        self.worker.error.connect(self.on_autofix_error)
        self.worker.start()

    def on_autofix_finished(self, response_text):
        self.log("Received response from AI Agent.")
        new_html = extract_html(response_text)
        
        if new_html:
            self.log("Applying updated HTML to Editor.")
            # Set the editor content
            self.editor.setPlainText(new_html)
            # Re-render
            self.render_preview()
            self.status_bar.showMessage("Auto-fix applied successfully.")
        else:
            self.log("Failed to extract code blocks from response. Dumping raw response below:")
            self.log(response_text)
            self.status_bar.showMessage("Parsing failed.")
            
        self.set_controls_enabled(True)

    def on_autofix_error(self, error_msg):
        self.log(f"Agent Error: {error_msg}")
        QMessageBox.critical(self, "Agent Communication Error", error_msg)
        self.status_bar.showMessage("Auto-fix failed.")
        self.set_controls_enabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AgentVisualLoopApp()
    window.show()
    sys.exit(app.exec())
