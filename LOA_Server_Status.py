# =============================================================================
#                       LOST ARK SERVER STATUS BOT v7.0 (Final)
# =============================================================================
# - GUI Library: Tkinter (standard, 100% free)
# - Features: Advanced State Machine Logic, GUI Webhook Management, System Tray
# - Dependencies: pip install requests beautifulsoup4 pystray Pillow
# =============================================================================

import sys
import threading
import time
import datetime
import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext, messagebox
import queue
import json
from PIL import Image
from pystray import MenuItem as item, Icon
from email.utils import parsedate_to_datetime

# --- CONFIGURATION (Most settings are now in config.json) ---
CONFIG_FILE = "config.json"
SERVER_NAME = "Ratik"  # Change this to your server name
STATUS_URL = "https://www.playlostark.com/en-us/support/server-status"
CHECK_INTERVAL_SECONDS = 5
STATUS_CONFIG = {
    "Online": {"color": 0x2ECC71, "image_url": "https://i.ibb.co/84fVZQxj/mokoko-emote-contest-finalists-make-sure-to-vote-in-the-v0-1p8b731fzf6b1.png", "status_text": "Online"},
    "Busy": {"color": 0xE74C3C, "image_url": "https://i.ibb.co/5CFmdx6/mokoko-emote-contest-finalists-make-sure-to-vote-in-the-v0-91e3vuufzf6b1.webp", "status_text": "Busy"},
    "Full": {"color": 0xE74C3C, "image_url": "https://i.ibb.co/5CFmdx6/mokoko-emote-contest-finalists-make-sure-to-vote-in-the-v0-91e3vuufzf6b1.webp", "status_text": "Full"},
    "Maintenance": {"color": 0xE74C3C, "image_url": "https://i.ibb.co/5CFmdx6/mokoko-emote-contest-finalists-make-sure-to-vote-in-the-v0-91e3vuufzf6b1.webp", "status_text": "In Maintenance"},
}

# --- Global bot running flag ---
bot_running = threading.Event()

# --- Configuration file management functions ---
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        default_config = {"webhook_urls": ["https://discord.com/api/webhooks/CHANGE_THIS_URL"]}
        save_config(default_config)
        return default_config

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Bot functions ---
def get_server_status(html_content, server_name):
    soup = BeautifulSoup(html_content, 'html.parser')
    server_name_div = soup.find('div', class_='ags-ServerStatus-content-responses-response-server-name', string=lambda text: text and server_name.lower() in text.lower())
    if not server_name_div: return 'Not Found'
    server_container = server_name_div.find_parent('div', class_='ags-ServerStatus-content-responses-response-server')
    if not server_container: return 'Not Found'
    if server_container.find('div', class_='ags-ServerStatus-content-responses-response-server-status--good'): return 'Online'
    if server_container.find('div', class_='ags-ServerStatus-content-responses-response-server-status--busy'): return 'Busy'
    if server_container.find('div', class_='ags-ServerStatus-content-responses-response-server-status--full'): return 'Full'
    if server_container.find('div', class_='ags-ServerStatus-content-responses-response-server-status--maintenance'): return 'Maintenance'
    return 'Unknown Status'

def send_discord_notification(status, server_name, webhook_urls, timestamp_obj):
    config = STATUS_CONFIG.get(status, STATUS_CONFIG["Online"])
    embed_data = {"title": "Lost Ark Server Status Update", "color": config["color"], "fields": [{"name": "Server", "value": server_name, "inline": True}, {"name": "Status", "value": config["status_text"], "inline": True}], "image": {"url": config["image_url"]}, "footer": {"text": "Ratik Status Bot"}, "timestamp": timestamp_obj.isoformat()}
    content_message = f"The **{server_name}** server is now **{config['status_text']}**."
    payload = {"content": content_message, "embeds": [embed_data], "username": "Lost Ark Status", "avatar_url": "https://i.ibb.co/HTbGPV4B/Generated-Image-September-05-2025-9-21-PM.png"}
    for url in webhook_urls:
        try:
            requests.post(url, json=payload, timeout=10).raise_for_status()
            print(f"Notification sent successfully to ...{url[-30:]}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send notification to ...{url[-30:]}: {e}")

def bot_logic(get_webhook_urls_func):
    """The main bot logic that runs in the background with advanced state management."""
    last_known_status = None
    last_notified_status = None
    monitoring_mode = False
    monitoring_end_time = None
    last_change_timestamp = None
    
    print("Bot thread started with advanced logic. Monitoring server status...")

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(STATUS_URL, headers=headers, timeout=10)
        response.raise_for_status()
        initial_status = get_server_status(response.text, SERVER_NAME)
        last_known_status = initial_status
        last_notified_status = initial_status
        print(f"Initial status is: {initial_status}. Monitoring for changes...")
    except requests.exceptions.RequestException as e:
        print(f"Initial network error: {e}. Will retry.")
        last_known_status = "Error"

    while not bot_running.is_set():
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(STATUS_URL, headers=headers, timeout=10)
            response.raise_for_status()
            
            time_of_check = parsedate_to_datetime(response.headers.get('Date')) if response.headers.get('Date') else datetime.datetime.now(datetime.timezone.utc)
            current_status = get_server_status(response.text, SERVER_NAME)

            if current_status == 'Not Found':
                print(f"Server '{SERVER_NAME}' not found on page (temporary issue). Retrying...")
                bot_running.wait(CHECK_INTERVAL_SECONDS)
                continue

            if monitoring_mode:
                if current_status != last_known_status:
                    print(f"Flicker detected: {last_known_status} -> {current_status}. Resetting stability timer.")
                    last_known_status = current_status
                    last_change_timestamp = time_of_check
                
                elif (time_of_check - last_change_timestamp) >= datetime.timedelta(minutes=1):
                    print(f"Status stable at '{last_known_status}' for 1 minute. Making final decision.")
                    if last_known_status != last_notified_status:
                        print(f"Correction needed. Last notification was '{last_notified_status}', stable is '{last_known_status}'.")
                        current_webhooks = get_webhook_urls_func()
                        send_discord_notification(last_known_status, SERVER_NAME, current_webhooks, time_of_check)
                        last_notified_status = last_known_status
                    else:
                        print("No correction needed.")
                    monitoring_mode = False

                if monitoring_mode and time_of_check > monitoring_end_time:
                    print("2-minute monitoring window expired. Making final decision.")
                    if last_known_status != last_notified_status:
                         print(f"Correction needed after timeout. Last notification was '{last_notified_status}', last seen is '{last_known_status}'.")
                         current_webhooks = get_webhook_urls_func()
                         send_discord_notification(last_known_status, SERVER_NAME, current_webhooks, time_of_check)
                         last_notified_status = last_known_status
                    else:
                        print("No correction needed after timeout.")
                    monitoring_mode = False

            elif current_status != last_known_status:
                print(f"Potential change from '{last_known_status}' to '{current_status}'. Waiting 10s for confirmation...")
                bot_running.wait(10)

                confirm_response = requests.get(STATUS_URL, headers=headers, timeout=10)
                confirm_status = get_server_status(confirm_response.text, SERVER_NAME)

                if confirm_status == current_status:
                    print(f"Change confirmed to '{current_status}'. Sending notification and entering 2-min monitoring mode.")
                    current_webhooks = get_webhook_urls_func()
                    send_discord_notification(current_status, SERVER_NAME, current_webhooks, time_of_check)
                    last_known_status = current_status
                    last_notified_status = current_status
                    monitoring_mode = True
                    monitoring_end_time = time_of_check + datetime.timedelta(minutes=2)
                    last_change_timestamp = time_of_check
                else:
                    print("Change was a temporary flicker. Ignoring.")
                    last_known_status = confirm_status
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}. Retrying.")
        
        bot_running.wait(CHECK_INTERVAL_SECONDS)
    
    print("Bot thread has been stopped.")

# --- TKINTER GUI ---
class App:
    def __init__(self, root, log_queue):
        self.root = root; self.log_queue = log_queue; self.bot_thread = None; self.tray_icon = None
        self.root.title("Lost Ark Status Bot")
        self.config = load_config(); self.webhook_urls = self.config.get("webhook_urls", [])
        
        main_frame = tk.Frame(root); main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        console_frame = tk.Frame(main_frame); console_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.label = tk.Label(console_frame, text=f"Monitoring Log: {SERVER_NAME}", font=("Helvetica", 14)); self.label.pack(pady=5, anchor=tk.W)
        self.console = scrolledtext.ScrolledText(console_frame, state='disabled', height=20, bg='black', fg='white'); self.console.pack(fill=tk.BOTH, expand=True)
        
        webhook_frame = tk.LabelFrame(main_frame, text="Webhook Management", padx=10, pady=10); webhook_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.webhook_listbox = tk.Listbox(webhook_frame, height=15, width=50); self.webhook_listbox.pack(fill=tk.BOTH, expand=True)
        for url in self.webhook_urls: self.webhook_listbox.insert(tk.END, url)
        self.webhook_entry = tk.Entry(webhook_frame, width=50); self.webhook_entry.pack(pady=5, fill=tk.X)
        webhook_button_frame = tk.Frame(webhook_frame); webhook_button_frame.pack()
        tk.Button(webhook_button_frame, text="Add", command=self.add_webhook).pack(side=tk.LEFT, padx=5)
        tk.Button(webhook_button_frame, text="Remove Selected", command=self.remove_webhook).pack(side=tk.LEFT, padx=5)
        
        self.bottom_frame = tk.Frame(root); self.bottom_frame.pack(fill=tk.X, padx=10, pady=(5,0))
        self.start_button = tk.Button(self.bottom_frame, text="Start Monitoring", command=self.start_bot); self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_button = tk.Button(self.bottom_frame, text="Stop Monitoring", command=self.stop_bot, state='disabled'); self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.status_bar = tk.Label(root, text="Status: Idle", bd=1, relief=tk.SUNKEN, anchor=tk.W); self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray); self.process_queue()

    def get_webhook_urls(self): return self.webhook_urls
    def add_webhook(self):
        new_url = self.webhook_entry.get().strip()
        if new_url and new_url.startswith("https://discord.com/api/webhooks/"):
            if new_url not in self.webhook_urls:
                self.webhook_urls.append(new_url); self.webhook_listbox.insert(tk.END, new_url); self.webhook_entry.delete(0, tk.END)
                save_config({"webhook_urls": self.webhook_urls}); print(f"Webhook added: ...{new_url[-30:]}")
            else: messagebox.showwarning("Duplicate", "This webhook URL is already in the list.")
        else: messagebox.showerror("Invalid URL", "Please enter a valid Discord webhook URL.")
    def remove_webhook(self):
        selected_indices = self.webhook_listbox.curselection()
        if not selected_indices: messagebox.showwarning("No Selection", "Please select a webhook to remove."); return
        url_to_remove = self.webhook_listbox.get(selected_indices[0]); self.webhook_urls.remove(url_to_remove); self.webhook_listbox.delete(selected_indices[0])
        save_config({"webhook_urls": self.webhook_urls}); print(f"Webhook removed: ...{url_to_remove[-30:]}")
    def start_bot(self): print("Starting bot..."); self.start_button.config(state='disabled'); self.stop_button.config(state='normal'); self.status_bar.config(text="Status: Running"); bot_running.clear(); self.bot_thread = threading.Thread(target=bot_logic, args=(self.get_webhook_urls,), daemon=True); self.bot_thread.start()
    def stop_bot(self): print("Stopping bot... Please wait."); bot_running.set(); self.stop_button.config(state='disabled'); self.status_bar.config(text="Status: Stopping...")
    def process_queue(self):
        try:
            while True: msg = self.log_queue.get_nowait(); self.console.config(state='normal'); self.console.insert(tk.END, msg); self.console.see(tk.END); self.console.config(state='disabled')
        except queue.Empty: pass
        if self.stop_button['state'] == 'disabled' and self.start_button['state'] == 'disabled' and self.bot_thread and not self.bot_thread.is_alive():
             self.start_button.config(state='normal'); self.status_bar.config(text="Status: Idle"); print("Bot stopped successfully.")
        self.root.after(100, self.process_queue)
    def hide_to_tray(self): self.root.withdraw(); image = Image.open("icon.png"); menu = (item('Show', self.show_from_tray, default=True), item('Exit', self.quit_app)); self.tray_icon = Icon("LOA Status Bot", image, "Lost Ark Status Bot", menu); self.tray_icon.run()
    def show_from_tray(self): self.tray_icon.stop(); self.root.deiconify(); self.root.lift()
    def quit_app(self):
        print("Exiting application..."); self.tray_icon.stop()
        if self.bot_thread and self.bot_thread.is_alive(): bot_running.set(); self.bot_thread.join()
        self.root.destroy()

class QueueWriter:
    def __init__(self, log_queue): self.log_queue = log_queue
    def write(self, msg): self.log_queue.put(msg)
    def flush(self): pass

if __name__ == '__main__':
    log_queue = queue.Queue()
    sys.stdout = QueueWriter(log_queue)
    root = tk.Tk()
    app = App(root, log_queue)
    root.mainloop()