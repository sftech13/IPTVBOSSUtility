# IPTV BOSS Utility

A cross-platform (Windows & Ubuntu Linux) IPTV playlist checker and maintenance toolkit with a user-friendly GUI.


---

## Features

* **Playlist Checker:** Validate IPTV M3U playlists for working/broken streams, video/audio codec info, resolution, and more.
* **Maintenance Tools:** Kill running app, clean temp/cache, tail logs, move backups, network checks, and more.
* **Simple GUI:** Intuitive interface with tabs for Stream Checker and Maintenance.
* **Cross-platform:** Works on Windows and Linux (Ubuntu).
* **Easy Install:** Download as `.exe` (Windows) or `.deb` (Ubuntu), with all dependencies bundled. No Python required for end users.

---
![alt text](assets/1.png)
![alt text](assets/2.png)
![alt text](assets/3.png)
![alt text](assets/4.png)
---


## Quick Start

### Windows

1. Download the latest `.exe` release from [Releases](https://github.com/sftech13/IPTVBOSSUtility/raw/master/dist/IPTVBoss_Tool.exe).
2. Run the stand alone app.
3. Start **IPTV BOSS Utility** from the Start Menu or Desktop.

### Ubuntu / Linux

1. Download the latest `.deb` from [Releases](https://github.com/sftech13/IPTVBOSSUtility/raw/master/dist/IPTVBoss_Tool.deb).
2. Install via terminal:

   ```bash
   sudo dpkg -i iptvboss-utility_*.deb
   sudo apt-get install -f  # Only if dependencies are missing
   ```
3. Launch from your application menu.

---

## Usage

1. **Open the app.**
2. **Maintenance Tab:** Run maintenance tasks like cleaning cache, process kill, log tail, backups, and connectivity check.
3. **Stream Checker Tab:**

   * Load your `.m3u` playlist file.
   * Set timeout and max concurrent connections.
   * (Optional) Pick a group/category.
   * Click **Start Scan** to begin.
4. **Results** display in the output pane, with working/dead status and stream info.

---

## Credits

Developed by [sftech13](https://github.com/sftech13).
