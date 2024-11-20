from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QMessageBox, QListWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys
import json
import re
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

class ScrapingWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, concurso, parent=None):
        super().__init__(parent)
        self.concurso = concurso

        @property
        def concurso(self):
            return self._concurso

        @concurso.setter
        def concurso(self, value):
            self._concurso = value

    def extract_winners_data(self, page, premio_number):
        winners = []
        rows = page.locator(
            f"h1:has-text('Ganhadores do concurso {self.concurso} no {premio_number}º Prêmio') ~ table tr"
        ).all()
        
        for row in rows[1:]:  # Skip header
            cells = row.locator("td").all()
            if len(cells) >= 2:
                cartela = cells[0].inner_text().strip()
                localizacao = cells[1].inner_text().strip()
                winners.append({
                    "cartela": cartela,
                    "localizacao": localizacao
                })
        return winners

    def extract_balls(self, page):
        page.wait_for_selector("#jsAlert1_popupBody", timeout=5000)
        result_div = page.locator("#jsAlert1_popupBody")
        content = result_div.inner_html()
        ordem_sorteio_match = re.search(
            r'Bolas Chamadas - Ordem de sorteio.*?</td>(.*?)Bolas Chamadas - Ordenadas', 
            content, re.DOTALL
        )
        if ordem_sorteio_match:
            ordem_sorteio_html = ordem_sorteio_match.group(1)
            numeros = re.findall(r'>(\d{2})<', ordem_sorteio_html)
        else:
            raise Exception("Não foi possível encontrar a sequência de bolas na ordem do sorteio")
        return numeros

    def run(self):
        try:
            print(f"Valor do concurso no run: {self.concurso}")
            with sync_playwright() as playwright:
                self.progress.emit("Iniciando navegador...")
                browser = playwright.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                self.progress.emit("Acessando site...")
                page.goto("https://www.totolec.com.br/show/")
                # page.wait_for_selector("a:has-text('138')", timeout=10000)
                # page.get_by_role("link", name="138").click()
                # Localizar e clicar no link correto baseado no concurso
                self.progress.emit(f"Procurando pelo link do concurso {self.concurso}...")
                page.locator(f"a:has(p:has-text('{self.concurso}'))").click()
                self.progress.emit("Carregando dados do concurso...")
                page.wait_for_timeout(5000)  # Aguarde para garantir que os dados carreguem

                result_data = {
                    "data_extracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "numero_concurso": self.concurso,
                    "premios": {}
                }

                for premio in range(1, 4):  # Processando prêmios 1, 2, 3
                    self.progress.emit(f"Processando {premio}º Prêmio...")
                    premio_link = page.get_by_role("link", 
                        name=f"Ganhadores do concurso {self.concurso} no {premio}º Prêmio"
                    )
                    if premio_link.is_visible():
                        premio_link.click()
                        page.wait_for_load_state("networkidle")
                    else:
                        print(f"Erro Link do {premio}º Prêmio não encontrado")
                    # page.wait_for_timeout(2000)

                    winners = self.extract_winners_data(page, premio)
                    page.get_by_role("link", name="Confira as bolas chamadas").first.click()
                    numeros = self.extract_balls(page)
                    result_data["premios"][f"premio_{premio}"] = {
                        "ganhadores": winners,
                        "bolas_chamadas": numeros,
                        "quantidade_bolas": len(numeros)
                    }
                    page.locator("input[value='Fechar']").click()
                    page.wait_for_timeout(1000)

                context.close()
                browser.close()
                self.finished.emit(result_data)

        except Exception as e:
            self.error.emit(str(e))

class SearchWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Buscar Resultados Totolec")
        self.setFixedSize(900, 800)
        self.setStyleSheet("background-color: #f0f0f0;")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        title = QLabel("Busca de Resultados Totolec - Todos os Prêmios")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.concurso_input = QTextEdit()
        self.concurso_input.setPlaceholderText("Digite o número do concurso")
        self.concurso_input.setFixedHeight(50)
        self.concurso_input.setStyleSheet("font-size: 16px; margin: 10px;")
        layout.addWidget(self.concurso_input)

        self.search_button = QPushButton("Iniciar Busca Completa")
        self.search_button.setStyleSheet("""
            background-color: #4169E1; color: white; font-size: 16px; margin: 10px; padding: 15px; 
            border-radius: 8px;
        """)
        self.search_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.search_button)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: white; font-family: monospace; font-size: 14px;")
        layout.addWidget(self.log_area)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet("font-size: 14px; margin: 10px;")
        layout.addWidget(self.history_list)

        self.worker = None

        self.load_history()

    def start_scraping(self):
        concurso = self.concurso_input.toPlainText().strip()
        print(f"Valor do concurso: {concurso}")
        if not concurso.isdigit():
            QMessageBox.warning(self, "Erro de Entrada", "Por favor, insira um número de concurso válido.")
            return

        self.search_button.setEnabled(False)
        self.log_area.clear()
        self.log_area.append(f"Iniciando busca para o concurso {concurso}...")
        self.worker = ScrapingWorker(concurso)
        self.worker.progress.connect(self.update_log)
        self.worker.finished.connect(self.handle_results)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def update_log(self, message):
        self.log_area.append(message)

    def handle_results(self, result_data):
        try:
            filename = f"concurso_{result_data['numero_concurso']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)

            self.log_area.append(f"Busca concluída! Arquivo salvo: {filename}")

            self.save_history(result_data)
            self.update_history_list(result_data)

        except Exception as e:
            self.handle_error(f"Erro ao salvar resultados: {str(e)}")

        finally:
            self.search_button.setEnabled(True)

    def handle_error(self, error_message):
        self.log_area.append(f"ERRO: {error_message}")
        self.search_button.setEnabled(True)
        QMessageBox.critical(self, "Erro", f"Ocorreu um erro: {error_message}")

    def save_history(self, result_data):
        history_file = "historico.json"
        try:
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            else:
                history = []

            history.append(result_data)
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.log_area.append(f"ERRO ao salvar histórico: {str(e)}")

    def load_history(self):
        history_file = "historico.json"
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            for item in history:
                self.history_list.addItem(f"Concurso {item['numero_concurso']} - {item['data_extracao']}")

    def update_history_list(self, result_data):
        self.history_list.addItem(f"Concurso {result_data['numero_concurso']} - {result_data['data_extracao']}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SearchWindow()
    window.show()
    sys.exit(app.exec_())
