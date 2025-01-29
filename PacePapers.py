import json
import os
import ctypes
import time
import hashlib
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def set_wallpaper(image_path):
    log_message(f"Setting wallpaper to: {image_path}")
    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)

def get_file_hash(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_contents = file.read()
            return hashlib.md5(file_contents).hexdigest()
    except Exception as e:
        log_message(f"Error reading file {file_path}: {e}")
        return None

json_file_path = r"C:\Users\super\speedrunigt\latest_world.json"
wpstateout_file_path = r"E:\multimc\MultiMC\instances\Instance 1\.minecraft\wpstateout.txt"
events_log_path = None
wallpapers = {}
current_wallpaper = None
previous_log_hash = None
observer = None
dark_mode = True

def log_message(message):
    console_output.insert(tk.END, message + "\n")
    console_output.yview(tk.END)

class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == json_file_path:
            log_message(f"Detected change in {json_file_path}. Processing...")
            process_latest_world()

def process_latest_world():
    global current_wallpaper, previous_log_hash, events_log_path
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            world_path = data.get("world_path")
            if not world_path:
                log_message("World path not found in the JSON file.")
                return
        events_log_path = os.path.join(world_path, "speedrunigt", "events.log")
        if os.path.exists(wpstateout_file_path):
            with open(wpstateout_file_path, 'r') as wpstate_file:
                wpstate_contents = wpstate_file.read()
                if "wall" in wpstate_contents or "waiting" in wpstate_contents:
                    if "default" in wallpapers:
                        set_wallpaper(wallpapers["default"])
                        current_wallpaper = wallpapers["default"]
                        log_message("Wallpaper changed to default due to wpstateout condition.")
                        return
        current_log_hash = get_file_hash(events_log_path)
        if current_log_hash != previous_log_hash:
            previous_log_hash = current_log_hash
            with open(events_log_path, 'r') as log_file:
                log_contents = log_file.read()
            text_to_wallpaper = [
                ("common.leave_world", "default"),
                ("credits", "credits"),
                ("enter_end", "end"),
                ("enter_stronghold", "stronghold"),
                ("first_portal", "first portal"),
                ("enter_fortress", "fortress"),
                ("enter_bastion", "bastion"),
                ("enter_nether", "nether"),
            ]
            for key, wallpaper_key in text_to_wallpaper:
                if key in log_contents and wallpaper_key in wallpapers:
                    set_wallpaper(wallpapers[wallpaper_key])
                    current_wallpaper = wallpapers[wallpaper_key]
                    log_message(f"Wallpaper changed to: {wallpaper_key}")
                    break
            else:
                log_message("No matching text found in events.log.")
    except Exception as e:
        log_message(f"An error occurred: {e}")

def start_monitoring():
    global observer
    if observer is None:
        event_handler = FileChangeHandler()
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(json_file_path), recursive=False)
        observer.start()
        log_message("Monitoring started...")
        threading.Thread(target=keep_running, daemon=True).start()

def keep_running():
    try:
        while observer.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        stop_monitoring()

def stop_monitoring():
    global observer, current_wallpaper
    if observer:
        observer.stop()
        observer.join()
        observer = None
        log_message("Monitoring stopped.")
    if "default" in wallpapers:
        set_wallpaper(wallpapers["default"])
        current_wallpaper = wallpapers["default"]
        log_message("Wallpaper reset to default.")

def select_wallpaper(key, label):
    filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.png;*.bmp")])
    if filepath:
        wallpapers[key] = filepath
        label.config(text=os.path.basename(filepath))
        log_message(f"Selected {key}: {filepath}")

def toggle_theme():
    global dark_mode
    dark_mode = not dark_mode
    bg_color = "#2E2E2E" if dark_mode else "#FFFFFF"
    fg_color = "white" if dark_mode else "black"
    root.configure(bg=bg_color)
    main_frame.configure(bg=bg_color)
    wallpaper_frame.configure(bg=bg_color)
    console_output.configure(bg="#1E1E1E" if dark_mode else "#F0F0F0", fg=fg_color)

root = tk.Tk()
root.title("Pace Wallpapers")
root.geometry("500x600")
root.configure(bg='#2E2E2E')

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

main_frame = tk.Frame(notebook, bg='#2E2E2E')
wallpaper_frame = tk.Frame(notebook, bg='#2E2E2E')
notebook.add(main_frame, text='Main')
notebook.add(wallpaper_frame, text='Wallpapers')

theme_button = tk.Button(main_frame, text="Toggle Theme", command=toggle_theme, bg="#444", fg="white")
theme_button.pack(pady=10)

start_button = tk.Button(main_frame, text="Start", command=start_monitoring, width=10, bg="#444", fg="white")
start_button.pack(pady=10)
stop_button = tk.Button(main_frame, text="Stop", command=stop_monitoring, width=10, bg="#444", fg="white")
stop_button.pack(pady=10)

wallpaper_buttons = [
    ("Default", "default"),
    ("Nether", "nether"),
    ("Bastion", "bastion"),
    ("Fortress", "fortress"),
    ("First Portal", "first portal"),
    ("Stronghold", "stronghold"),
    ("End", "end"),
    ("Credits", "credits"),
]

for text, key in wallpaper_buttons:
    frame = tk.Frame(wallpaper_frame, bg='#2E2E2E')
    frame.pack(pady=5)
    label = tk.Label(frame, text="None", fg="white", bg="#2E2E2E")
    label.pack(side=tk.RIGHT, padx=5)
    tk.Button(frame, text=text, command=lambda k=key, l=label: select_wallpaper(k, l), width=15, bg="#555", fg="white").pack(side=tk.LEFT)

console_output = scrolledtext.ScrolledText(main_frame, width=60, height=10, state='normal', bg="#1E1E1E", fg="white")
console_output.pack(pady=10)

root.mainloop()


