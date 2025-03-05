import subprocess
import json
import os
import struct
import shutil

class DBCDWrapper:
    # Типы сжатия
    COMPRESSION_NONE = 0
    COMPRESSION_IMMEDIATE = 1
    COMPRESSION_COMMON = 2
    COMPRESSION_PALLET = 3
    COMPRESSION_PALLET_ARRAY = 4
    COMPRESSION_SIGNED_IMMEDIATE = 5
    COMPRESSION_BIT_PACKED = 8
    COMPRESSION_COMMON_2 = 16
    COMPRESSION_ARRAY_2 = 18
    COMPRESSION_SPARSE = 5
    COMPRESSION_BITPACKED = 32
    COMPRESSION_BITPACKED_SIGNED = 33
    COMPRESSION_BITPACKED_INDEXED = 34
    COMPRESSION_BITPACKED_INDEXED_ARRAY = 35

    def __init__(self, file_path):
        self.file_path = file_path
        self._validate_file()
        self.file_type = os.path.splitext(file_path)[1].lower()
        self.header = None
        self.records = []
        self.string_block = []
        self.field_count = 0  # Добавляем поле для хранения количества полей
        self.pallet_data = {}
        self.common_data = {}
        self.sparse_data = {}
        self.bitpacked_data = {}
    
    def _validate_file(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Файл {self.file_path} не найден")
        if not self.file_path.lower().endswith(('.dbc', '.db2')):
            raise ValueError("Файл должен иметь расширение .dbc или .db2")
    
    def _read_dbc_header(self):
        with open(self.file_path, 'rb') as f:
            # Читаем сигнатуру (4 байта)
            signature = f.read(4).decode('ascii')
            # Читаем количество записей (4 байта)
            record_count = struct.unpack('<I', f.read(4))[0]
            # Читаем количество полей (4 байта)
            field_count = struct.unpack('<I', f.read(4))[0]
            # Читаем размер записи (4 байта)
            record_size = struct.unpack('<I', f.read(4))[0]
            # Читаем размер строки (4 байта)
            string_size = struct.unpack('<I', f.read(4))[0]
            
            return {
                "signature": signature,
                "record_count": record_count,
                "field_count": field_count,
                "record_size": record_size,
                "string_size": string_size
            }
    
    def _read_db2_header(self, file):
        # Читаем сигнатуру и версию
        signature = file.read(4).decode('utf-8')
        version = struct.unpack('<I', file.read(4))[0]
        
        # Читаем имя таблицы (128 байт)
        schema_string = file.read(128).decode('utf-8').rstrip('\0')
        
        # Читаем основные поля заголовка
        record_count = struct.unpack('<I', file.read(4))[0]
        field_count = struct.unpack('<I', file.read(4))[0]
        record_size = struct.unpack('<I', file.read(4))[0]
        string_table_size = struct.unpack('<I', file.read(4))[0]
        
        # Читаем хеши и другие поля
        table_hash = struct.unpack('<I', file.read(4))[0]
        layout_hash = struct.unpack('<I', file.read(4))[0]
        min_id = struct.unpack('<I', file.read(4))[0]
        max_id = struct.unpack('<I', file.read(4))[0]
        locale = struct.unpack('<I', file.read(4))[0]
        flags = struct.unpack('<H', file.read(2))[0]
        id_index = struct.unpack('<H', file.read(2))[0]
        total_field_count = struct.unpack('<I', file.read(4))[0]
        bitpacked_data_offset = struct.unpack('<I', file.read(4))[0]
        lookup_column_count = struct.unpack('<I', file.read(4))[0]
        field_storage_info_size = struct.unpack('<I', file.read(4))[0]
        common_data_size = struct.unpack('<I', file.read(4))[0]
        pallet_data_size = struct.unpack('<I', file.read(4))[0]
        sections_count = struct.unpack('<I', file.read(4))[0]

        # Если есть секции, читаем первую секцию
        section_header = None
        if sections_count > 0:
            tact_key_lookup = struct.unpack('<Q', file.read(8))[0]
            file_offset = struct.unpack('<I', file.read(4))[0]
            num_records = struct.unpack('<I', file.read(4))[0]
            string_table_size = struct.unpack('<I', file.read(4))[0]
            offset_records_end = struct.unpack('<I', file.read(4))[0]
            index_data_size = struct.unpack('<I', file.read(4))[0]
            parent_lookup_size = struct.unpack('<I', file.read(4))[0]
            offset_map_id_count = struct.unpack('<I', file.read(4))[0]
            copy_table_count = struct.unpack('<I', file.read(4))[0]
            section_header = {
                'tact_key_lookup': tact_key_lookup,
                'file_offset': file_offset,
                'num_records': num_records,
                'string_table_size': string_table_size,
                'offset_records_end': offset_records_end,
                'index_data_size': index_data_size,
                'parent_lookup_size': parent_lookup_size,
                'offset_map_id_count': offset_map_id_count,
                'copy_table_count': copy_table_count
            }
        
        print(f"Сигнатура файла: {signature}")
        print(f"Версия: {version}")
        print(f"Схема: {schema_string}")
        print(f"Количество записей: {record_count}")
        print(f"Количество полей: {field_count}")
        print(f"Размер записи: {record_size} байт")
        print(f"Размер строковой таблицы: {string_table_size} байт")
        print(f"Хеш таблицы: 0x{table_hash:08x}")
        print(f"Хеш макета: 0x{layout_hash:08x}")
        print(f"Диапазон ID: {min_id} - {max_id}")
        print(f"Локаль: {locale}")
        print(f"Флаги: 0x{flags:04x}")
        print(f"Индекс ID: {id_index}")
        print(f"Всего полей: {total_field_count}")
        print(f"Смещение упакованных данных: {bitpacked_data_offset}")
        print(f"Количество полей для поиска: {lookup_column_count}")
        print(f"Размер информации о хранении полей: {field_storage_info_size}")
        print(f"Размер общих данных: {common_data_size}")
        print(f"Размер данных палитры: {pallet_data_size}")
        print(f"Количество секций: {sections_count}")
        
        if section_header:
            print(f"\nИнформация о секции:")
            print(f"TACT ключ: 0x{section_header['tact_key_lookup']:016x}")
            print(f"Смещение файла: {section_header['file_offset']}")
            print(f"Количество записей: {section_header['num_records']}")
            print(f"Размер строковой таблицы: {section_header['string_table_size']}")
            print(f"Смещение конца записей: {section_header['offset_records_end']}")
            print(f"Размер индексных данных: {section_header['index_data_size']}")
            print(f"Размер родительского поиска: {section_header['parent_lookup_size']}")
            print(f"Количество ID в карте смещений: {section_header['offset_map_id_count']}")
            print(f"Количество копируемых таблиц: {section_header['copy_table_count']}")
        
        return {
            'signature': signature,
            'version': version,
            'schema_string': schema_string,
            'record_count': record_count,
            'field_count': field_count,
            'record_size': record_size,
            'string_table_size': string_table_size,
            'table_hash': table_hash,
            'layout_hash': layout_hash,
            'min_id': min_id,
            'max_id': max_id,
            'locale': locale,
            'flags': flags,
            'id_index': id_index,
            'total_field_count': total_field_count,
            'bitpacked_data_offset': bitpacked_data_offset,
            'lookup_column_count': lookup_column_count,
            'field_storage_info_size': field_storage_info_size,
            'common_data_size': common_data_size,
            'pallet_data_size': pallet_data_size,
            'sections_count': sections_count,
            'section_header': section_header
        }
    
    def _read_field_info(self, file):
        field_info = []
        # Читаем метаданные полей
        for i in range(self.header['field_count']):
            field = {}
            # Читаем смещение и размер поля
            field['offset'] = struct.unpack('<H', file.read(2))[0]
            field['size'] = struct.unpack('<H', file.read(2))[0]
            # Читаем дополнительную информацию
            field['additional_data_size'] = struct.unpack('<I', file.read(4))[0]
            field['compression_type'] = struct.unpack('<I', file.read(4))[0]
            field['packed_offset'] = struct.unpack('<I', file.read(4))[0]
            field['cell_size'] = struct.unpack('<I', file.read(4))[0]
            field['cardinality'] = struct.unpack('<I', file.read(4))[0]

            # Валидация и корректировка значений
            if field['size'] == 0 or field['size'] > 32:
                field['size'] = 4  # Устанавливаем стандартный размер
            
            if field['offset'] > 1000:  # Слишком большое смещение
                field['offset'] = i * 4  # Устанавливаем последовательное смещение
            
            if field['compression_type'] > 35:  # Неверный тип сжатия
                field['compression_type'] = self.COMPRESSION_NONE
            
            if field['additional_data_size'] > 1000000:  # Слишком большой размер доп. данных
                field['additional_data_size'] = 0
            
            if field['cell_size'] > 32:  # Слишком большой размер ячейки
                field['cell_size'] = 0

            field_info.append(field)
            print(f"Поле {i}:")
            print(f"  Смещение: {field['offset']} (исходное)")
            print(f"  Размер: {field['size']} байт")
            print(f"  Тип сжатия: {field['compression_type']}")
            if field['compression_type'] in [self.COMPRESSION_PALLET, self.COMPRESSION_PALLET_ARRAY]:
                print(f"  Размер палитры: {field['additional_data_size'] // 4}")
            elif field['compression_type'] in [self.COMPRESSION_COMMON, self.COMPRESSION_COMMON_2]:
                print(f"  Размер общих данных: {field['additional_data_size'] // 8}")
            elif field['compression_type'] in [self.COMPRESSION_IMMEDIATE, self.COMPRESSION_SIGNED_IMMEDIATE]:
                print(f"  Значение: {field['packed_offset']}")
            
        return field_info

    def _read_field_structure(self):
        """Читает структуру полей для WDC5"""
        with open(self.file_path, 'rb') as f:
            # Пропускаем заголовок
            f.seek(8)  # Сигнатура и версия
            # Пропускаем имя таблицы
            while f.read(1) != b'\0':
                pass
            # Пропускаем основные поля заголовка
            f.seek(64, 1)  # 16 полей по 4 байта
            
            # Читаем информацию о структуре полей
            field_info = []
            for _ in range(self.header['total_field_count']):
                field_offset = struct.unpack('<H', f.read(2))[0]
                field_size = struct.unpack('<H', f.read(2))[0]
                field_flags = struct.unpack('<I', f.read(4))[0]
                field_info.append({
                    'offset': field_offset,
                    'size': field_size,
                    'flags': field_flags
                })
            return field_info

    def _read_records(self, f):
        """Читает записи из файла"""
        print("\nНачинаю чтение записей...")
        print(f"Ожидаемое количество записей: {self.header['record_count']}")
        print(f"Количество полей: {self.header['field_count']}")
        
        # Инициализация структур данных для различных типов сжатия
        pallet_data = {}
        common_data = {}
        sparse_data = {}
        bitpacked_data = {}
        records = []

        try:
            # Проверка и корректировка информации о полях
            for i in range(self.header['field_count']):
                field = self.field_info[i]
                # Если размер поля 0, устанавливаем минимальный размер
                if field['size'] == 0:
                    field['size'] = 4
                # Если смещение слишком большое, корректируем его
                if field['offset'] > self.header['record_size']:
                    field['offset'] = i * 4
                # Проверяем тип сжатия
                if field['compression_type'] > 35:
                    field['compression_type'] = self.COMPRESSION_NONE

            # Чтение данных палитры
            print("\nЧтение данных палитры...")
            for i in range(self.header['field_count']):
                if self.field_info[i]['compression_type'] in [self.COMPRESSION_PALLET, self.COMPRESSION_PALLET_ARRAY]:
                    pallet_size = max(0, min(self.field_info[i]['additional_data_size'] // 4, 1000000))
                    print(f"Поле {i}: Тип сжатия PALLET, размер палитры: {pallet_size}")
                    pallet_data[i] = []
                    for _ in range(pallet_size):
                        try:
                            value = int.from_bytes(f.read(4), byteorder='little', signed=False)
                            pallet_data[i].append(value)
                        except Exception as e:
                            print(f"Ошибка чтения палитры для поля {i}: {str(e)}")
                            break

            # Чтение общих данных
            print("\nЧтение общих данных...")
            for i in range(self.header['field_count']):
                if self.field_info[i]['compression_type'] in [self.COMPRESSION_COMMON, self.COMPRESSION_COMMON_2]:
                    common_size = max(0, min(self.field_info[i]['additional_data_size'] // 8, 1000000))
                    print(f"Поле {i}: Тип сжатия COMMON, размер общих данных: {common_size}")
                    common_data[i] = {}
                    for _ in range(common_size):
                        try:
                            key = int.from_bytes(f.read(4), byteorder='little', signed=False)
                            value = int.from_bytes(f.read(4), byteorder='little', signed=False)
                            common_data[i][key] = value
                        except Exception as e:
                            print(f"Ошибка чтения общих данных для поля {i}: {str(e)}")
                            break

            # Чтение записей
            print("\nЧтение записей...")
            current_position = f.tell()
            print(f"Текущая позиция в файле: {current_position}")
            
            for record_idx in range(self.header['record_count']):
                record = []
                for field_idx in range(self.header['field_count']):
                    field = self.field_info[field_idx]
                    compression_type = field['compression_type']
                    
                    try:
                        if compression_type == self.COMPRESSION_NONE:
                            value = int.from_bytes(f.read(field['size']), byteorder='little', signed=False)
                        
                        elif compression_type in [self.COMPRESSION_IMMEDIATE, self.COMPRESSION_SIGNED_IMMEDIATE]:
                            value = field['packed_offset']
                        
                        elif compression_type in [self.COMPRESSION_COMMON, self.COMPRESSION_COMMON_2]:
                            key = int.from_bytes(f.read(field['size']), byteorder='little', signed=False)
                            value = common_data[field_idx].get(key, 0)
                        
                        elif compression_type in [self.COMPRESSION_PALLET, self.COMPRESSION_PALLET_ARRAY]:
                            index = int.from_bytes(f.read(field['size']), byteorder='little', signed=False)
                            value = pallet_data[field_idx][index] if field_idx in pallet_data and index < len(pallet_data[field_idx]) else 0
                        
                        elif compression_type in [self.COMPRESSION_BIT_PACKED, self.COMPRESSION_ARRAY_2]:
                            value = int.from_bytes(f.read(field['size']), byteorder='little', signed=False)
                            if field['cell_size'] > 0:
                                value &= (1 << field['cell_size']) - 1
                        
                        else:
                            value = int.from_bytes(f.read(field['size']), byteorder='little', signed=False)
                            
                        record.append(value)
                        
                    except Exception as e:
                        print(f"\nОшибка при чтении записи {record_idx}, поле {field_idx}:")
                        print(f"Тип сжатия: {compression_type}")
                        print(f"Размер поля: {field['size']}")
                        print(f"Ошибка: {str(e)}")
                        value = 0
                        record.append(value)
                
                records.append(record)
                if (record_idx + 1) % 50000 == 0:
                    print(f"Прочитано записей: {record_idx + 1}")
                    current_position = f.tell()
                    print(f"Текущая позиция в файле: {current_position}")
            
            print(f"\nВсего прочитано записей: {len(records)}")
            print(f"Размер первой записи: {len(records[0]) if records else 0} полей")
            print(f"Конечная позиция в файле: {f.tell()}")
            return records
        
        except Exception as e:
            print(f"\nКритическая ошибка при чтении записей: {str(e)}")
            return []

    def _read_bits(self, f, bit_width):
        """Чтение указанного количества бит из файла"""
        if bit_width == 0:
            return 0
            
        # Чтение минимального необходимого количества байт
        bytes_needed = (bit_width + 7) // 8
        data = f.read(bytes_needed)
        if not data:
            return 0
            
        # Преобразование байтов в целое число
        value = int.from_bytes(data, byteorder='little')
        
        # Маскирование лишних бит
        mask = (1 << bit_width) - 1
        return value & mask

    def _read_string_block(self):
        if self.file_type == '.dbc':
            with open(self.file_path, 'rb') as f:
                # Пропускаем заголовок и записи
                f.seek(20 + self.header['record_count'] * self.header['record_size'])
                # Читаем строковый блок
                string_data = f.read(self.header['string_size'])
                self.string_block = string_data.decode('utf-8').split('\0')
    
    def _validate_header(self, header):
        # Проверяем сигнатуру
        VALID_DBC_SIGNATURES = ['WDBC', 'WDB2', 'WCH2', 'WDB5', 'WDC5']
        if header['signature'] not in VALID_DBC_SIGNATURES:
            raise ValueError(f"Неверная сигнатура файла: {header['signature']}")
            
        print(f"Сигнатура файла: {header['signature']}")
        if 'schema_string' in header:
            print(f"Схема: {header['schema_string']}")
        print(f"Количество записей: {header['record_count']}")
        print(f"Размер записи: {header['record_size']} байт")
        
        if header['signature'] == 'WDC5':
            print(f"Хеш таблицы: 0x{header['table_hash']:08X}")
            print(f"Хеш макета: 0x{header['layout_hash']:08X}")
            print(f"Диапазон ID: {header['min_id']} - {header['max_id']}")
            print(f"Локаль: {header['locale']}")
            print(f"Флаги: 0x{header['flags']:04X}")
            print(f"Индекс ID: {header['id_index']}")
            print(f"Всего полей: {header['total_field_count']}")
            print(f"Смещение упакованных данных: {header['bitpacked_data_offset']}")
            print(f"Количество полей для поиска: {header['lookup_column_count']}")
            print(f"Размер информации о хранении полей: {header['field_storage_info_size']}")
            print(f"Размер общих данных: {header['common_data_size']}")
            print(f"Размер данных палитры: {header['pallet_data_size']}")
            print(f"Количество секций: {header['sections_count']}")
            
            if header['section_header']:
                print(f"\nИнформация о секции:")
                print(f"TACT ключ: 0x{header['section_header']['tact_key_lookup']:016X}")
                print(f"Смещение файла: {header['section_header']['file_offset']}")
                print(f"Количество записей: {header['section_header']['num_records']}")
                print(f"Размер строковой таблицы: {header['section_header']['string_table_size']}")
                print(f"Смещение конца записей: {header['section_header']['offset_records_end']}")
                print(f"Размер индексных данных: {header['section_header']['index_data_size']}")
                print(f"Размер родительского поиска: {header['section_header']['parent_lookup_size']}")
                print(f"Количество ID в карте смещений: {header['section_header']['offset_map_id_count']}")
                print(f"Количество копируемых таблиц: {header['section_header']['copy_table_count']}")
            
        return True  # Заголовок валиден

    def read_file(self):
        try:
            print(f"\nНачинаю чтение файла: {self.file_path}")
            print(f"Определен тип файла: {self.file_type.upper()[1:]}")
            
            if self.file_type == '.dbc':
                self.header = self._read_dbc_header()
                file_type = "DBC"
            else:  # .db2
                with open(self.file_path, 'rb') as f:
                    print("\nЧтение заголовка файла...")
                    self.header = self._read_db2_header(f)
                    
                    if not self._validate_header(self.header):
                        raise ValueError("Ошибка при валидации заголовка")
                    print("Заголовок прошел валидацию")
                    
                    print("\nЧтение информации о полях...")
                    self.field_info = self._read_field_info(f)
                    
                    if self.header['section_header']:
                        print(f"\nПереход к началу секции данных: {self.header['section_header']['file_offset']}")
                        f.seek(self.header['section_header']['file_offset'])
                    
                    print("\nЧтение записей...")
                    self.records = self._read_records(f)
                    print(f"Прочитано записей: {len(self.records)}")
                    
                file_type = "DB2"
            
            return {
                "status": "success",
                "message": f"{file_type} файл успешно прочитан",
                "file": self.file_path,
                "type": file_type,
                "header": self.header,
                "records": self.records,
                "string_block": self.string_block if self.file_type == '.dbc' else None
            }
        except Exception as e:
            print(f"Ошибка при чтении файла: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def save_file(self, new_file_path=None):
        try:
            if new_file_path is None:
                new_file_path = self.file_path
            
            # Создаем резервную копию
            backup_path = self.file_path + '.bak'
            shutil.copy2(self.file_path, backup_path)
            
            with open(new_file_path, 'wb') as f:
                # Записываем заголовок
                if self.file_type == '.dbc':
                    f.write(self.header['signature'].encode('ascii'))
                    f.write(struct.pack('<I', self.header['record_count']))
                    f.write(struct.pack('<I', self.header['field_count']))
                    f.write(struct.pack('<I', self.header['record_size']))
                    f.write(struct.pack('<I', self.header['string_size']))
                else:  # .db2
                    f.write(self.header['signature'].encode('ascii'))
                    f.write(struct.pack('<I', self.header['version']))
                    f.write(struct.pack('<I', self.header['record_count']))
                    f.write(struct.pack('<I', self.header['record_size']))
                
                # Записываем записи
                for record in self.records:
                    for value in record:
                        f.write(struct.pack('<I', value))
                
                # Записываем строковый блок для DBC
                if self.file_type == '.dbc' and self.string_block:
                    string_data = '\0'.join(self.string_block)
                    f.write(string_data.encode('utf-8'))
            
            return {
                "status": "success",
                "message": f"Файл успешно сохранен: {new_file_path}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def update_record(self, record_index, field_index, new_value):
        if 0 <= record_index < len(self.records) and 0 <= field_index < len(self.records[0]):
            self.records[record_index][field_index] = new_value
            return True
        return False
    
    def update_string(self, string_index, new_value):
        if self.file_type == '.dbc' and 0 <= string_index < len(self.string_block):
            self.string_block[string_index] = new_value
            return True
        return False

    def read_db2_file(self):
        """Читает DB2 файл и возвращает его содержимое"""
        try:
            with open(self.file_path, 'rb') as f:
                # Читаем заголовок
                self.header = self._read_db2_header(f)
                
                # Читаем информацию о полях
                self.field_info = self._read_field_info(f)
                
                # Если есть секции, переходим к началу записей
                if self.header['section_header']:
                    f.seek(self.header['section_header']['file_offset'])
                
                # Читаем записи
                self.records = self._read_records(f)
                
                return {
                    'status': 'success',
                    'type': 'DB2',
                    'message': f"Файл успешно прочитан. Найдено {len(self.records)} записей.",
                    'file': self.file_path,
                    'header': self.header,
                    'records': self.records,
                    'string_block': self.string_block
                }
        except Exception as e:
            return {
                'status': 'error',
                'type': 'DB2',
                'message': f"Ошибка при чтении файла: {str(e)}",
                'file': self.file_path,
                'header': None,
                'records': [],
                'string_block': []
            } 