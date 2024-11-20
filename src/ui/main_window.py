# Conteúdo do arquivo src/ui/main_window.py:
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLabel, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import subprocess
import os
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu Principal")
        self.setFixedSize(800, 700)
        self.setStyleSheet("background-color: #90EE90;")  # Verde claro
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignHCenter)
        
        # Título
        title_label = QLabel("Menu Principal")
        title_label.setFont(QFont('Arial', 24, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                border: 2px solid black;
                padding: 10px;
                background-color: #90EE90;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Grid para os botões
        button_grid = QWidget()
        grid_layout = QGridLayout(button_grid)
        main_layout.addWidget(button_grid)
        
        # Estilo dos botões
        button_style = """
            QPushButton {
                background-color: #4169E1;
                border: 3px solid #000080;
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
                min-width: 200px;
                min-height: 80px;
            }
            QPushButton:hover {
                background-color: #000080;
                color: white;
            }
        """
        
        # Criação dos botões
        buttons = [
            ("Buscar\nResultados", self.run_search_script, 0, 0),
            ("Analisar\nCartelas", self.run_analyze_script, 0, 1),
            ("Opção 3", self.run_option3_script, 1, 0),
            ("Opção 4", self.run_option4_script, 1, 1)
        ]
        
        for text, slot, row, col in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(slot)
            grid_layout.addWidget(btn, row, col)
        
        # Botão Fechar
        close_button = QPushButton("Fechar")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #00008B;
                color: white;
                border: 2px solid black;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #FF0000;
            }
        """)
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button)
        
    def run_script(self, script_name):
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 'scripts', script_name)
        try:
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path])
            else:
                print(f"Script não encontrado: {script_path}")
        except Exception as e:
            print(f"Erro ao executar o script: {str(e)}")
    
    def run_search_script(self):
        self.run_script('search_site.py')
    
    def run_analyze_script(self):
        self.run_script('analise_jogos.py')
    
    def run_option3_script(self):
        self.run_script('option_3.py')
    
    def run_option4_script(self):
        self.run_script('option_4.py')