# Lost Ark Server Status Bot

Just sharing a bot to monitor the server status for the game Lost Ark and send notifications via Discord.
It was originally for personal use while servers are in Maintenance to know when they are back online without checking manually the website.

## Features

* Real-time monitoring of server status (Online, Busy, Full, Maintenance).
* Discord notifications with custom messages and images for each status.
* Advanced state machine logic to prevent false notifications from rapid status flickers.
* Graphical User Interface (GUI) to manage Discord webhooks.
* System tray icon for background operation.

## Preview

Here is what the application and its notifications look like:

**Application GUI:**
![Application GUI](./screenshots/gui_screenshot.png)

**Discord Notifications:**
![Discord Notifications](./screenshots/discord_notifications.png)

---

## Getting Started (Recommended for most users)

This method uses the pre-built executable (`.exe`) and does not require Python.

1. Go to the [**Releases Page**](https://github.com/BurN-30/LOA-Server-Status/releases).
2. Download the `LOA_Server_Status.exe` file from the latest release.
3. Place the `.exe` in a new, empty folder.
4. **Important:** Place an `icon.png` file in the same folder. This is required for the system tray icon to work correctly. Without this file, the application might not appear in the notification area and could require you to end its process via Task Manager.
5. Run `LOA_Server_Status.exe` once. A `config.json` file will be automatically created.
6. Open `config.json` and edit it with your Discord Webhook URL and the server name you want to monitor.
7. Relaunch the application. It is now configured and ready to use!

---

## Installation for Developers (from source code)

This method is for users who want to run the script directly with Python.

### 1. Clone and Install Dependencies

1. **Clone the repository:**
        ```bash
    git clone https://github.com/BurN-30/LOA-Server-Status.git
    cd LOA-Server-Status
        ```
2. **Create a virtual environment (recommended):**
        ```bash
    python -m venv venv
        ```
3. **Activate the virtual environment:**
    * **On Windows:** `.\venv\Scripts\activate`
    * **On macOS/Linux:** `source venv/bin/activate`
4. **Install the dependencies:**
        ```bash
    pip install -r requirements.txt
        ```

#### 2. Configure and Run

1. **Configure the application:**
    * Open the `config.json` file.
    * Replace the placeholder URL inside `"webhook_urls"` with your own Discord webhook URL.
    * Change the `"server_name"` value to the server you want to monitor.
    * Here is an example `config.json` file:
            ```json
        {
            "webhook_urls": [
                "https://discord.com/api/webhooks/1234567890/ABCDEFG..."
            ],
            "server_name": "Azena"
        }
            ```
2. **Run the script:**
        ```bash
    python LOA_Server_Status.py
        ```

---

## Creating an Executable

To create your own standalone `.exe` file from the source code, you can use PyInstaller.

1. **Install PyInstaller:**
        ```bash
        pip install pyinstaller
        ```
2. **Create the executable:**
        ```bash
    pyinstaller --onefile --windowed --icon=icon.ico LOA_Server_Status.py
        ```
    The executable will be located in the `dist` folder.

## Important Files

* `LOA_Server_Status.py`: The main bot script.
* `config.json`: Configuration file for webhook URLs and server name.
* `requirements.txt`: A list of the required Python dependencies.
* `icon.png`: The icon used for the system tray.
