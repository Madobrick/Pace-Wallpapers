import os
import sys
import json
import random
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ctypes
import threading
import time

# Function to change wallpaper via Windows API
def set_wallpaper(image_path):
    print(f"Attempting to change wallpaper to: {image_path}")
    if os.path.exists(image_path):
        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
        print(f"Wallpaper changed to: {image_path}")
    else:
        print(f"Wallpaper file not found: {image_path}")

# Priority list of keywords (highest priority first)
PRIORITY_KEYWORDS = [
    ("leave_world", 0),
    ("enter_end", 6),
    ("enter_stronghold", 5),
    ("first_portal", 4),
    ("enter_fortress", 3),
    ("enter_bastion", 2),
    ("enter_nether", 1)
]

# Mapping for wallpaper button names
WALLPAPER_NAMES = {
    0: "Default",
    1: "Nether",
    2: "Bastion",
    3: "Fortress",
    4: "First Portal",
    5: "Stronghold",
    6: "End",
    7: "Credits"
}

# Custom class to redirect stdout and stderr to a Tkinter Text widget
class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')

    def flush(self):
        pass

# GUI Application
class PaceWallpapersApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pace Wallpapers")
        self.root.geometry("600x550")
        
        # Theme flag; default to light
        self.dark_mode = False
        
        self.config_file = "config.json"
        self.latest_world_path = ""
        # No default events.log path; it will be set from latest_world.json.
        self.events_log_path = ""
        self.wallpapers = {i: "" for i in range(8)}
        self.current_wallpaper = ""  # Track the current wallpaper
        self.leave_world_handled = False  # Flag to avoid repeated handling of leave_world
        self.theme = "light"  # "light", "dark", or "orange"
        self.coins = 0  # Coin counter
        self.load_config()
        
        # Spoingus toggle state and storage for original theme
        self.spoingus_active = False
        self.original_theme = None
        
        self.style = ttk.Style()
        
        self.notebook = ttk.Notebook(root)
        self.main_frame = ttk.Frame(self.notebook)
        self.wallpapers_frame = ttk.Frame(self.notebook)
        self.log_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_frame, text="Main")
        self.notebook.add(self.wallpapers_frame, text="Wallpapers")
        self.notebook.add(self.log_frame, text="Log")
        self.notebook.pack(expand=True, fill="both")
        
        # Log Tab: A scrolled text widget for console output
        self.log_text = scrolledtext.ScrolledText(self.log_frame, state='disabled', wrap='word', height=15)
        self.log_text.pack(expand=True, fill="both", padx=5, pady=5)
        sys.stdout = ConsoleRedirector(self.log_text)
        sys.stderr = ConsoleRedirector(self.log_text)
        
        if self.theme == "dark":
            self.dark_mode = True
            self.set_dark_theme()
        elif self.theme == "orange":
            self.set_orange_theme()
        else:
            self.set_light_theme()
        
        # Main Tab Widgets
        main_top_frame = ttk.Frame(self.main_frame)
        main_top_frame.pack(pady=10, fill="x")
        ttk.Button(main_top_frame, text="Select latest_world.json", command=self.select_latest_world).pack(side="left", padx=5)
        self.json_path_label = ttk.Label(main_top_frame, text=self.latest_world_path if self.latest_world_path else "No JSON selected", width=40)
        self.json_path_label.pack(side="left", padx=5)
        
        # Renamed buttons: "Start" and "Stop"
        self.start_button = ttk.Button(self.main_frame, text="Start", command=self.start_monitoring)
        self.start_button.pack(pady=5)
        self.stop_button = ttk.Button(self.main_frame, text="Stop", command=self.stop_monitoring)
        self.stop_button.pack(pady=5)
        ttk.Button(self.main_frame, text="Toggle Dark Theme", command=self.toggle_theme).pack(pady=5)
        # Spoingus toggle button
        self.spoingus_button = ttk.Button(self.main_frame, text="Spoingus", command=self.spoingus_action)
        self.spoingus_button.pack(pady=5)
        # Gambling button (without background change)
        self.gambling_button = ttk.Button(self.main_frame, text="Gambling", command=self.gambling_action)
        self.gambling_button.pack(pady=5)
        # New "Random background" button
        self.random_bg_button = ttk.Button(self.main_frame, text="Random background", command=self.random_background)
        self.random_bg_button.pack(pady=5)
        
        # Bottom frame for coin counter and "buy nothing" button
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.pack(side="bottom", fill="x", pady=10)
        self.coin_label = ttk.Label(bottom_frame, text=f"Coins: {self.coins}")
        self.coin_label.pack(side="left", padx=10)
        self.buy_nothing_button = ttk.Button(bottom_frame, text="buy nothing - 1000 coins", command=self.buy_nothing_action)
        self.buy_nothing_button.pack(side="right", padx=10)
        
        # Wallpaper Selection Tab Widgets (renamed accordingly)
        self.wallpaper_labels = {}
        for i in range(8):
            frame = ttk.Frame(self.wallpapers_frame)
            frame.pack(pady=2, fill="x")
            ttk.Button(frame, text=f"Select {WALLPAPER_NAMES.get(i, 'Wallpaper ' + str(i))}", command=lambda n=i: self.select_wallpaper(n)).pack(side="left", padx=5)
            lbl = ttk.Label(frame, text=os.path.basename(self.wallpapers.get(i, "")) if self.wallpapers.get(i, "") else "None", width=40)
            lbl.pack(side="left", padx=5)
            self.wallpaper_labels[i] = lbl
        
        self.observer = Observer()
        self.latest_world_handler = LatestWorldHandler(self)
        self.events_handler = EventsLogHandler(self)
    
    def set_dark_theme(self):
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#333333")
        self.style.configure("TLabel", background="#333333", foreground="white")
        self.style.configure("TButton", background="#444444", foreground="white")
        self.style.configure("Vertical.TScrollbar", background="#444444")
        self.root.configure(background="#333333")
        self.log_text.configure(background="#222222", foreground="white", insertbackground="white")
        print("Dark theme activated.")

    def set_light_theme(self):
        self.style.theme_use("default")
        self.style.configure("TFrame", background="SystemButtonFace")
        self.style.configure("TLabel", background="SystemButtonFace", foreground="black")
        self.style.configure("TButton", background="SystemButtonFace", foreground="black")
        self.style.configure("Vertical.TScrollbar", background="SystemButtonFace")
        self.root.configure(background="SystemButtonFace")
        self.log_text.configure(background="white", foreground="black", insertbackground="black")
        print("Light theme activated.")
    
    def set_orange_theme(self):
        orange = "#E89149"
        self.style.theme_use("clam")
        self.style.configure("TFrame", background=orange)
        self.style.configure("TLabel", background=orange, foreground="black")
        self.style.configure("TButton", background=orange, foreground="black")
        self.style.configure("Vertical.TScrollbar", background=orange)
        self.root.configure(background=orange)
        self.log_text.configure(background=orange, foreground="black", insertbackground="black")
        print("Orange theme activated.")
    
    def toggle_theme(self):
        if self.dark_mode:
            self.set_light_theme()
            self.theme = "light"
        else:
            self.set_dark_theme()
            self.theme = "dark"
        self.dark_mode = not self.dark_mode
        self.save_config()
    
    def gambling_action(self):
        chance = random.random()
        if chance < 0.01:
            coins_won = 100
            print("Jackpot! You won 100 coins!")
        else:
            coins_won = random.randint(1, 3)
            print(f"You won {coins_won} coins.")
        self.coins += coins_won
        self.coin_label.config(text=f"Coins: {self.coins}")
        # Removed background change here.
        self.save_config()
    
    def random_background(self):
        random_color = "#" + "".join(random.choice("0123456789ABCDEF") for _ in range(6))
        print(f"Setting random background color: {random_color}")
        self.root.configure(background=random_color)
        self.style.configure("TFrame", background=random_color)
        self.style.configure("TLabel", background=random_color)
    
    def spoingus_action(self):
        if not self.spoingus_active:
            print("Spoingus button pressed; activating spoingus mode.")
            self.original_theme = self.theme  # Save current theme
            self.start_button.config(text="Spoingus")
            self.set_orange_theme()
            self.theme = "orange"
            self.spoingus_button.config(text="Unspoingus")
            self.spoingus_active = True
        else:
            print("Spoingus button pressed; deactivating spoingus mode.")
            self.start_button.config(text="Start")
            if self.original_theme == "dark":
                self.set_dark_theme()
                self.theme = "dark"
            else:
                self.set_light_theme()
                self.theme = "light"
            self.spoingus_button.config(text="Spoingus")
            self.spoingus_active = False
        self.save_config()
    
    def buy_nothing_action(self):
        if self.coins >= 1000:
            self.coins -= 1000
            print("You bought nothing for 1000 coins.")
        else:
            print("Not enough coins to buy nothing.")
        self.coin_label.config(text=f"Coins: {self.coins}")
        self.save_config()
    
    def select_latest_world(self):
        file_path = filedialog.askopenfilename(filetypes=[["JSON files", "*.json"]])
        if file_path:
            self.latest_world_path = file_path
            print(f"Selected latest_world.json: {file_path}")
            self.json_path_label.config(text=file_path)
            self.save_config()
    
    def start_monitoring(self):
        if not self.latest_world_path:
            print("Error: No latest_world.json selected.")
            return
        if not os.path.exists(self.latest_world_path):
            print("Error: latest_world.json does not exist.")
            return
        
        print(f"Starting monitoring latest_world.json at {self.latest_world_path}...")
        self.observer.unschedule_all()
        self.observer.schedule(self.latest_world_handler, os.path.dirname(self.latest_world_path), recursive=False)
        try:
            if not self.observer.is_alive():
                print("Observer not alive; starting observer.")
                self.observer.start()
            else:
                print("Observer is already running.")
        except Exception as e:
            print(f"Error starting observer: {e}")
        self.leave_world_handled = False
       
    def stop_monitoring(self):
        print("Stopping monitoring...")
        try:
            print("Setting wallpaper to Default before stopping monitoring.")
            set_wallpaper(self.wallpapers.get(0, ""))
            self.current_wallpaper = self.wallpapers.get(0, "")
            
            self.observer.unschedule_all()
            self.observer.stop()
            self.observer.join()
            self.observer = Observer()
            # Do not clear the JSON path
            self.events_log_path = ""
            self.save_config()
            print("Monitoring successfully stopped.")
        except Exception as e:
            print(f"Error stopping observer: {e}")
    
    def select_wallpaper(self, index):
        file_path = filedialog.askopenfilename(filetypes=[["Image files", "*.jpg;*.png;*.bmp"]])
        if file_path:
            self.wallpapers[index] = file_path
            self.wallpaper_labels[index].config(text=os.path.basename(file_path))
            print(f"Selected wallpaper {WALLPAPER_NAMES.get(index, index)}: {file_path}")
            self.save_config()
    
    def save_config(self):
        config = {
            "latest_world_path": self.latest_world_path,
            "wallpapers": self.wallpapers,
            "theme": self.theme,
            "coins": self.coins
        }
        with open(self.config_file, "w") as file:
            json.dump(config, file)
        print("Config saved.")
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as file:
                config = json.load(file)
                self.latest_world_path = config.get("latest_world_path", "")
                wallpapers = config.get("wallpapers", {})
                self.wallpapers = {int(k): v for k, v in wallpapers.items()} if wallpapers else {i: "" for i in range(8)}
                self.theme = config.get("theme", "light")
                self.coins = config.get("coins", 0)
            print("Config loaded.")
    
    def check_latest_world(self):
        if os.path.exists(self.latest_world_path):
            try:
                with open(self.latest_world_path, "r") as file:
                    data = json.load(file)
                    world_path = data.get("world_path", "")
                    if world_path:
                        new_events_log_path = os.path.normpath(os.path.join(world_path, "speedrunigt", "events.log"))
                        self.events_log_path = new_events_log_path
                        print(f"Checked latest_world.json: updated events.log path: {self.events_log_path}")
                    else:
                        print("No world_path found in latest_world.json")
            except Exception as e:
                print(f"Error checking latest_world.json: {e}")
        else:
            print("latest_world.json does not exist while checking.")
    
    def check_events_log(self):
        if os.path.exists(self.events_log_path):
            try:
                with open(self.events_log_path, "r") as file:
                    lines = file.readlines()
                    selected_priority = len(PRIORITY_KEYWORDS)
                    selected_event = None
                    selected_wallpaper = None
                    for line in lines:
                        for priority, (keyword, wallpaper_num) in enumerate(PRIORITY_KEYWORDS):
                            if keyword in line:
                                if priority < selected_priority:
                                    selected_priority = priority
                                    selected_event = keyword
                                    selected_wallpaper = wallpaper_num
                    if selected_event is not None:
                        print(f"Detected highest priority event: {selected_event}, changing wallpaper {selected_wallpaper}")
                        if selected_event == "leave_world":
                            if not self.leave_world_handled:
                                if self.current_wallpaper and self.current_wallpaper == self.wallpapers.get(0, ""):
                                    print("Wallpaper Default is already set. Skipping change to avoid loop.")
                                else:
                                    set_wallpaper(self.wallpapers.get(0, ""))
                                    self.current_wallpaper = self.wallpapers.get(0, "")
                                self.leave_world_handled = True
                                print("Detected leave_world event: waiting 1 second before switching back to latest_world.json monitoring.")
                                time.sleep(1)
                                self.observer.unschedule_all()
                                self.observer.schedule(self.latest_world_handler, os.path.dirname(self.latest_world_path), recursive=False)
                            else:
                                print("leave_world event already handled.")
                        else:
                            set_wallpaper(self.wallpapers.get(selected_wallpaper, ""))
                    else:
                        print("No events detected in events.log.")
            except Exception as e:
                print(f"Error checking events.log: {e}")
        else:
            print("Warning: events.log does not exist while checking for existing keywords!")

# Watchdog Handlers
class LatestWorldHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
    
    def on_modified(self, event):
        print(f"Detected change in latest_world.json: {event.src_path}")
        if os.path.abspath(event.src_path) == os.path.abspath(self.app.latest_world_path):
            try:
                self.app.leave_world_handled = False  # Reset flag on new update
                self.app.check_latest_world()
                self.app.observer.unschedule_all()
                if os.path.exists(self.app.events_log_path):
                    self.app.observer.schedule(self.app.events_handler, os.path.dirname(self.app.events_log_path), recursive=False)
                    print("Monitoring events.log started.")
                else:
                    print("Warning: events.log does not exist at the expected location!")
            except Exception as e:
                print(f"Unexpected error in LatestWorldHandler: {e}")

class EventsLogHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
    
    def on_modified(self, event):
        if os.path.basename(event.src_path) == "events.log":
            print(f"Detected change in events.log: {event.src_path}")
            try:
                with open(self.app.events_log_path, "r") as file:
                    lines = file.readlines()
                    selected_priority = len(PRIORITY_KEYWORDS)
                    selected_event = None
                    selected_wallpaper = None
                    for line in lines:
                        for priority, (keyword, wallpaper_num) in enumerate(PRIORITY_KEYWORDS):
                            if keyword in line:
                                if priority < selected_priority:
                                    selected_priority = priority
                                    selected_event = keyword
                                    selected_wallpaper = wallpaper_num
                    if selected_event is not None:
                        print(f"Detected highest priority event: {selected_event}, changing wallpaper {selected_wallpaper}")
                        if selected_event == "leave_world":
                            if not self.app.leave_world_handled:
                                if self.app.current_wallpaper and self.app.current_wallpaper == self.app.wallpapers.get(0, ""):
                                    print("Wallpaper Default is already set. Skipping change to avoid loop.")
                                else:
                                    set_wallpaper(self.app.wallpapers.get(0, ""))
                                    self.app.current_wallpaper = self.app.wallpapers.get(0, "")
                                self.app.leave_world_handled = True
                                print("Detected leave_world event: waiting 1 second before switching back to latest_world.json monitoring.")
                                time.sleep(1)
                                self.app.observer.unschedule_all()
                                self.app.observer.schedule(self.app.latest_world_handler, os.path.dirname(self.app.latest_world_path), recursive=False)
                            else:
                                print("leave_world event already handled.")
                        else:
                            set_wallpaper(self.app.wallpapers.get(selected_wallpaper, ""))
                    else:
                        print("No events detected in events.log.")
            except Exception as e:
                print(f"Error in EventsLogHandler: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PaceWallpapersApp(root)
    root.mainloop()



