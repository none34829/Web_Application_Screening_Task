import sys
from pathlib import Path

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

DEFAULT_API = "http://127.0.0.1:8000/api"
MAX_TABLE_ROWS = 500


class EquipmentVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Equipment Visualizer")
        self.resize(1100, 800)

        self.latest_dataset = None
        self.history = []

        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        self.setCentralWidget(container)

        layout.addWidget(self._build_auth_panel())
        layout.addWidget(self._build_actions_panel())
        layout.addWidget(self._build_summary_panel())
        layout.addWidget(self._build_chart_panel())
        layout.addWidget(self._build_history_panel())
        layout.addWidget(self._build_table())

    def _build_auth_panel(self):
        panel = QWidget()
        layout = QGridLayout()
        panel.setLayout(layout)

        self.api_input = QLineEdit(DEFAULT_API)
        self.username_input = QLineEdit("demo")
        self.password_input = QLineEdit("demo123")
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addWidget(QLabel("API Base URL"), 0, 0)
        layout.addWidget(self.api_input, 0, 1)
        layout.addWidget(QLabel("Username"), 1, 0)
        layout.addWidget(self.username_input, 1, 1)
        layout.addWidget(QLabel("Password"), 2, 0)
        layout.addWidget(self.password_input, 2, 1)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.load_data)
        layout.addWidget(self.connect_button, 0, 2, 3, 1)

        self.status_label = QLabel("Waiting to connect...")
        layout.addWidget(self.status_label, 3, 0, 1, 3)
        return panel

    def _build_actions_panel(self):
        panel = QWidget()
        layout = QHBoxLayout()
        panel.setLayout(layout)

        self.upload_button = QPushButton("Upload CSV")
        self.upload_button.clicked.connect(self.upload_csv)

        self.pdf_button = QPushButton("Download PDF for selection/latest")
        self.pdf_button.clicked.connect(self.download_pdf)

        layout.addWidget(self.upload_button)
        layout.addWidget(self.pdf_button)
        layout.addStretch()
        return panel

    def _build_summary_panel(self):
        panel = QWidget()
        layout = QGridLayout()
        panel.setLayout(layout)

        self.summary_labels = {}
        summary_items = [
            ("total_equipment", "Total Equipment"),
            ("avg_flowrate", "Avg Flowrate"),
            ("avg_pressure", "Avg Pressure"),
            ("avg_temperature", "Avg Temperature"),
        ]
        for index, (key, label_text) in enumerate(summary_items):
            label = QLabel("--")
            label.setStyleSheet("font-size: 24px; font-weight: bold;")
            caption = QLabel(label_text)
            caption.setStyleSheet("color: #475569;")
            wrapper = QVBoxLayout()
            wrapper_widget = QWidget()
            wrapper_widget.setLayout(wrapper)
            wrapper.addWidget(caption)
            wrapper.addWidget(label)
            layout.addWidget(wrapper_widget, 0, index)
            self.summary_labels[key] = label

        return panel

    def _build_chart_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        layout.addWidget(QLabel("Equipment Type Distribution"))
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        return panel

    def _build_history_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        layout.addWidget(QLabel("Last 5 Uploads"))
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)
        return panel

    def _build_table(self):
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        return self.table

    def _auth(self):
        return self.username_input.text().strip(), self.password_input.text().strip()

    def _base_url(self):
        return self.api_input.text().rstrip("/")

    def _request(self, method, path, **kwargs):
        url = f"{self._base_url()}/{path.lstrip('/')}"
        response = requests.request(method, url, auth=self._auth(), timeout=60, **kwargs)
        if response.status_code == 404:
            return response
        response.raise_for_status()
        return response

    def load_data(self):
        self.status_label.setText("Loading data from backend...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            history_response = self._request("GET", "datasets/history/")
            self.history = history_response.json()
            self._populate_history()

            latest_response = self._request("GET", "datasets/latest/")
            if latest_response.status_code == 404:
                self.latest_dataset = None
                self._clear_summary()
                self._clear_chart()
                self._clear_table()
                self.status_label.setText("Connected. Upload data to get started.")
            else:
                self.latest_dataset = latest_response.json()
                self._update_summary(self.latest_dataset.get("summary"))
                self._update_chart(self.latest_dataset.get("summary", {}).get("type_distribution"))
                self._populate_table(self.latest_dataset.get("data", []))
                self.status_label.setText("Latest dataset synced successfully.")
        except requests.HTTPError as exc:
            self.status_label.setText(f"Error: {exc.response.text}")
            QMessageBox.critical(self, "Request failed", exc.response.text)
        except requests.RequestException as exc:
            self.status_label.setText(str(exc))
            QMessageBox.critical(self, "Network error", str(exc))
        finally:
            QApplication.restoreOverrideCursor()

    def upload_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV file", "", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            with open(file_path, "rb") as csv_file:
                response = self._request(
                    "POST",
                    "upload/",
                    files={"file": (Path(file_path).name, csv_file, "text/csv")},
                )
            self.status_label.setText(f"Uploaded {Path(file_path).name}")
            self.latest_dataset = response.json()
            self._update_summary(self.latest_dataset.get("summary"))
            self._update_chart(self.latest_dataset.get("summary", {}).get("type_distribution"))
            self._populate_table(self.latest_dataset.get("data", []))
            self.load_data()
        except requests.HTTPError as exc:
            QMessageBox.critical(
                self, "Upload failed", exc.response.json().get("detail", exc.response.text)
            )
        except requests.RequestException as exc:
            QMessageBox.critical(self, "Network error", str(exc))

    def download_pdf(self):
        dataset = self._selected_dataset() or self.latest_dataset
        if not dataset:
            QMessageBox.information(self, "No dataset", "Connect and select a dataset first.")
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", f"equipment-report-{dataset['file_name']}.pdf", "PDF Files (*.pdf)"
        )
        if not save_path:
            return
        try:
            response = self._request("GET", f"datasets/{dataset['id']}/pdf/", stream=True)
            with open(save_path, "wb") as pdf_file:
                pdf_file.write(response.content)
            self.status_label.setText(f"PDF saved to {save_path}")
        except requests.RequestException as exc:
            QMessageBox.critical(self, "Download failed", str(exc))

    def _selected_dataset(self):
        item = self.history_list.currentItem()
        if not item:
            return None
        return item.data(Qt.UserRole)

    def _populate_history(self):
        self.history_list.clear()
        for dataset in self.history:
            summary = dataset.get("summary") or {}
            count = summary.get("total_equipment", 0)
            label = f"{dataset['file_name']} • {count} rows • {dataset['uploaded_at']}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, dataset)
            self.history_list.addItem(item)

    def _update_summary(self, summary):
        if not summary:
            self._clear_summary()
            return
        for key, label in self.summary_labels.items():
            value = summary.get(key, "--")
            label.setText(str(value))

    def _clear_summary(self):
        for label in self.summary_labels.values():
            label.setText("--")

    def _update_chart(self, distribution):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if distribution:
            labels = list(distribution.keys())
            values = list(distribution.values())
            ax.bar(labels, values, color="#0ea5e9")
            ax.set_ylabel("Count")
            ax.set_xticklabels(labels, rotation=20, ha="right")
            ax.set_title("Equipment Types")
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
        self.canvas.draw()

    def _clear_chart(self):
        self.figure.clear()
        self.canvas.draw()

    def _populate_table(self, records):
        self.table.clear()
        if not records:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        headers = list(records[0].keys())
        limited_records = records[:MAX_TABLE_ROWS]

        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(limited_records))
        self.table.setHorizontalHeaderLabels(headers)

        for row_index, row in enumerate(limited_records):
            for col_index, header in enumerate(headers):
                value = row.get(header, "")
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_index, col_index, item)
        self.table.resizeColumnsToContents()

    def _clear_table(self):
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)


def main():
    app = QApplication(sys.argv)
    window = EquipmentVisualizer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
