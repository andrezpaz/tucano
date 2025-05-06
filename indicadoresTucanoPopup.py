from pynput import keyboard
import subprocess
import time
import os
import signal
import requests
from pynput.mouse import Controller

def get_idle_time():
    try:
        resposta = requests.get("https://cim.bazei.com.br:8000/tucano/config/idle-time", timeout=5)
        dados = resposta.json()
        return int(dados.get("idle_time_seconds", 60))  # default: 60s
    except Exception as e:
        print("Erro ao obter tempo de inatividade do servidor:", e)
        return 60  # fallback padrão

# Tempo de inatividade para abrir o popup (em segundos)
IDLE_TIME_THRESHOLD = get_idle_time() # obtem atraves da consulta no servidor

URL = ""
CHROMIUM_COMMAND = ["chromium-browser",
                    "--user-data-dir=/tmp/chromium-popup",  # <-- cria perfil temporário
                    "--no-default-browser-check",
                    "--no-first-run",
                    "--start-fullscreen",
                    "--app=" + URL]

popup_process = None
last_activity_time = time.time()

mouse_controller = Controller()
last_mouse_position = mouse_controller.position

def on_keyboard_activity(key):
    global last_activity_time
    last_activity_time = time.time()

def open_popup():
    global popup_process
    popup_process = subprocess.Popen(CHROMIUM_COMMAND)
    print("Popup aberto.")

def close_popup():
    global popup_process
    if popup_process:
        os.kill(popup_process.pid, signal.SIGTERM)
        popup_process = None
        print("Popup fechado.")

def monitor_idle():
    global popup_process
    global last_mouse_position
    global last_activity_time

    while True:
        current_position = mouse_controller.position
        if current_position != last_mouse_position:
            last_activity_time = time.time()
            last_mouse_position = current_position

        idle_time = time.time() - last_activity_time

        if idle_time > IDLE_TIME_THRESHOLD and not popup_process:
            open_popup()

        elif idle_time < 2 and popup_process:
            close_popup()

        time.sleep(0.5)

if __name__ == "__main__":
    # Detecta eventos de teclado
    keyboard_listener = keyboard.Listener(on_press=on_keyboard_activity)
    keyboard_listener.start()

    monitor_idle()