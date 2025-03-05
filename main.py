import sys
sys.set_int_max_str_digits(100000)  # Увеличиваем лимит до 100000 цифр
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QFileDialog, QLabel, QTextEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QHBoxLayout, QMessageBox,
                             QSpinBox, QLineEdit, QSplitter, QTabWidget, QProgressDialog)
from PySide6.QtCore import Qt, QTimer
from dbcd_wrapper import DBCDWrapper

class DBCDViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DBCD Viewer Задрот_софт_ЭДИЩЕН")
        self.setGeometry(100, 100, 1200, 800)
        
        # Создаем центральный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Создаем горизонтальный layout для кнопок
        button_layout = QHBoxLayout()
        
        # Добавляем кнопки
        self.open_button = QPushButton("Открыть файл")
        self.open_button.clicked.connect(self.open_file)
        button_layout.addWidget(self.open_button)
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_file)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        self.save_as_button = QPushButton("Сохранить как...")
        self.save_as_button.clicked.connect(self.save_file_as)
        self.save_as_button.setEnabled(False)
        button_layout.addWidget(self.save_as_button)

        # Добавляем поле поиска
        self.search_layout = QHBoxLayout()
        self.search_label = QLabel("Поиск:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.search_records)
        self.search_layout.addWidget(self.search_label)
        self.search_layout.addWidget(self.search_input)
        
        layout.addLayout(button_layout)
        layout.addLayout(self.search_layout)
        
        # Создаем разделитель для верхней и нижней части
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Создаем вкладки
        self.tab_widget = QTabWidget()
        
        # Вкладка с информацией о файле
        file_info_widget = QWidget()
        file_info_layout = QVBoxLayout(file_info_widget)
        
        # Добавляем метку для отображения типа файла
        self.file_type_label = QLabel("Тип файла: Не выбран")
        file_info_layout.addWidget(self.file_type_label)
        
        # Добавляем таблицу для отображения заголовка
        self.header_table = QTableWidget()
        self.header_table.setColumnCount(2)
        self.header_table.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self.header_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        file_info_layout.addWidget(self.header_table)
        
        self.tab_widget.addTab(file_info_widget, "Информация о файле")
        
        # Вкладка с записями
        records_widget = QWidget()
        records_layout = QVBoxLayout(records_widget)
        
        # Добавляем таблицу для отображения записей
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(0)
        self.records_table.setRowCount(0)
        self.records_table.itemChanged.connect(self.on_record_changed)
        records_layout.addWidget(self.records_table)
        
        self.tab_widget.addTab(records_widget, "Записи")
        
        # Вкладка со строками (только для DBC)
        strings_widget = QWidget()
        strings_layout = QVBoxLayout(strings_widget)
        
        self.strings_table = QTableWidget()
        self.strings_table.setColumnCount(2)
        self.strings_table.setHorizontalHeaderLabels(["Индекс", "Строка"])
        self.strings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.strings_table.itemChanged.connect(self.on_string_changed)
        strings_layout.addWidget(self.strings_table)
        
        self.tab_widget.addTab(strings_widget, "Строки")
        
        splitter.addWidget(self.tab_widget)
        
        # Добавляем текстовое поле для отображения дополнительной информации
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setMaximumHeight(100)
        splitter.addWidget(self.text_area)
        
        layout.addWidget(splitter)
        
        self.dbcd = None
        self.current_file = None
        self.original_records = None

    def open_file(self):
        # Сбрасываем интерфейс перед загрузкой нового файла
        self.reset_interface()
        
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            "",
            "DBC/DB2 Files (*.dbc *.db2);;All Files (*)"
        )
        
        if file_name:
            try:
                # Создаем и показываем прогресс-диалог
                progress = QProgressDialog("Загрузка файла...", None, 0, 0, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.setWindowTitle("Пожалуйста, подождите")
                progress.setCancelButton(None)  # Убираем кнопку отмены
                progress.setMinimumDuration(0)  # Показывать сразу
                progress.show()
                
                # Обновляем интерфейс
                QApplication.processEvents()
                
                self.dbcd = DBCDWrapper(file_name)
                result = self.dbcd.read_file()
                
                # Закрываем прогресс-диалог
                progress.close()
                
                if result['status'] == 'success':
                    self.current_file = file_name
                    self.save_button.setEnabled(True)
                    self.save_as_button.setEnabled(True)
                    
                    # Сохраняем оригинальные записи для поиска
                    self.original_records = result['records'].copy()
                    
                    # Обновляем информацию о типе файла
                    self.file_type_label.setText(f"Тип файла: {result['type']}")
                    
                    # Обновляем таблицу заголовка
                    self.update_header_table(result['header'])
                    
                    # Обновляем таблицу записей
                    self.update_records_table(result['records'])
                    
                    # Обновляем таблицу строк для DBC
                    if result['type'] == 'DBC' and result['string_block']:
                        self.update_strings_table(result['string_block'])
                        self.tab_widget.setTabEnabled(2, True)  # Включаем вкладку строк
                    else:
                        self.tab_widget.setTabEnabled(2, False)  # Отключаем вкладку строк
                    
                    # Обновляем текстовое поле
                    self.text_area.setText(f"Статус: {result['status']}\nСообщение: {result['message']}\nФайл: {result['file']}")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке файла: {str(e)}")
                self.reset_interface()

    def update_header_table(self, header):
        self.header_table.setRowCount(len(header))
        for i, (key, value) in enumerate(header.items()):
            if isinstance(value, dict):
                # Для вложенных словарей создаем отдельные строки
                for sub_key, sub_value in value.items():
                    self.header_table.insertRow(self.header_table.rowCount())
                    self.header_table.setItem(self.header_table.rowCount()-1, 0, 
                                            QTableWidgetItem(f"{key} - {sub_key}"))
                    self.header_table.setItem(self.header_table.rowCount()-1, 1, 
                                            QTableWidgetItem(str(sub_value)))
            else:
                self.header_table.setItem(i, 0, QTableWidgetItem(key))
                self.header_table.setItem(i, 1, QTableWidgetItem(str(value)))

    def update_records_table(self, records):
        if not records:
            self.records_table.setRowCount(0)
            self.records_table.setColumnCount(0)
            return

        self.records_table.setRowCount(len(records))
        self.records_table.setColumnCount(len(records[0]))
        
        # Устанавливаем заголовки столбцов
        headers = [f"Поле {i}" for i in range(len(records[0]))]
        self.records_table.setHorizontalHeaderLabels(headers)
        
        # Заполняем таблицу данными
        for i, record in enumerate(records):
            for j, value in enumerate(record):
                try:
                    # Для больших чисел используем шестнадцатеричный формат
                    if isinstance(value, int) and (value > 1000000000 or value < -1000000000):
                        display_value = f"0x{value:X}"
                    else:
                        display_value = str(value)
                    
                    item = QTableWidgetItem(display_value)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    self.records_table.setItem(i, j, item)
                except Exception as e:
                    print(f"Ошибка при установке значения [{i}, {j}]: {str(e)}")
                    item = QTableWidgetItem("ERROR")
                    self.records_table.setItem(i, j, item)

    def update_strings_table(self, strings):
        self.strings_table.setRowCount(len(strings))
        for i, string in enumerate(strings):
            self.strings_table.setItem(i, 0, QTableWidgetItem(str(i)))
            item = QTableWidgetItem(string)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.strings_table.setItem(i, 1, item)

    def reset_interface(self):
        self.header_table.setRowCount(0)
        self.records_table.setRowCount(0)
        self.strings_table.setRowCount(0)
        self.file_type_label.setText("Тип файла: Не выбран")
        self.save_button.setEnabled(False)
        self.save_as_button.setEnabled(False)
        self.text_area.clear()
        self.search_input.clear()  # Очищаем поле поиска
        self.current_file = None
        self.original_records = None

    def save_file(self):
        if self.current_file and self.dbcd:
            result = self.dbcd.save_file()
            if result['status'] == 'success':
                QMessageBox.information(self, "Успех", result['message'])
            else:
                QMessageBox.critical(self, "Ошибка", result['message'])

    def save_file_as(self):
        if self.current_file and self.dbcd:
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить файл как...",
                self.current_file,
                "DBC/DB2 Files (*.dbc *.db2);;All Files (*)"
            )
            if file_name:
                result = self.dbcd.save_file(file_name)
                if result['status'] == 'success':
                    QMessageBox.information(self, "Успех", result['message'])
                else:
                    QMessageBox.critical(self, "Ошибка", result['message'])

    def on_record_changed(self, item):
        if self.dbcd:
            row = item.row()
            col = item.column()
            try:
                text = item.text()
                # Проверяем, является ли значение шестнадцатеричным
                if text.startswith("0x"):
                    new_value = int(text[2:], 16)
                else:
                    new_value = int(text)
                    
                if self.dbcd.update_record(row, col, new_value):
                    self.text_area.setText(f"Запись [{row}, {col}] обновлена: {text}")
                else:
                    QMessageBox.warning(self, "Предупреждение", "Неверный индекс записи или поля")
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Введите корректное число (десятичное или шестнадцатеричное с префиксом 0x)")
                # Восстанавливаем оригинальное значение
                original_value = self.dbcd.records[row][col]
                if isinstance(original_value, int) and (original_value > 1000000000 or original_value < -1000000000):
                    display_value = f"0x{original_value:X}"
                else:
                    display_value = str(original_value)
                item.setText(display_value)

    def on_string_changed(self, item):
        if self.dbcd and self.dbcd.file_type == '.dbc':
            row = item.row()
            new_value = item.text()
            if self.dbcd.update_string(row, new_value):
                self.text_area.setText(f"Строка [{row}] обновлена: {new_value}")
            else:
                QMessageBox.warning(self, "Предупреждение", "Неверный индекс строки")

    def search_records(self):
        if not self.original_records:
            return

        search_text = self.search_input.text().lower()
        if not search_text:
            self.update_records_table(self.original_records)
            return

        filtered_records = []
        for record in self.original_records:
            record_str = ' '.join(str(x) for x in record).lower()
            if search_text in record_str:
                filtered_records.append(record)

        self.update_records_table(filtered_records)

def main():
    app = QApplication(sys.argv)
    window = DBCDViewer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 