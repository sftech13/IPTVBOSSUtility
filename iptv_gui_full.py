import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import threading
import re
from iptv_checker_core import run_check, config, parse_m3u8_file, setup_logging
import tkinter.font as font
import os

class IPTVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IPTV Stream Checker")

        self.default_font = font.Font(family="Segoe UI", size=10)
        self.output_font = font.Font(family="Courier New", size=10)
        self.style = ttk.Style()

        self.configure_theme()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        form = tk.Frame(root, bg=self.root["bg"])
        form.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Playlist Path:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.playlist_entry = tk.Entry(form)
        self.playlist_entry.configure(font=self.default_font, highlightthickness=1, relief="flat")
        self.playlist_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(form, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)

        ttk.Label(form, text="Timeout (s):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.timeout_entry = tk.Entry(form)
        self.timeout_entry.insert(0, "5")
        self.timeout_entry.configure(font=self.default_font, highlightthickness=1, relief="flat")
        self.timeout_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Max Connections:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.connections_entry = tk.Entry(form)
        self.connections_entry.insert(0, "3")
        self.connections_entry.configure(font=self.default_font, highlightthickness=1, relief="flat")
        self.connections_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Category:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form, textvariable=self.category_var, state="readonly")
        self.category_combo.configure(font=self.default_font)
        self.category_combo.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(form, text="Load Categories", command=self.load_categories).grid(row=3, column=2, padx=5)

        ttk.Button(form, text="Start Scan", command=self.start_scan).grid(row=4, column=1, sticky="e", pady=10)

        self.output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=self.output_font, bg="#1e1e1e", fg="white", insertbackground="white")
        self.output_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    def configure_theme(self):
        bg = "#2e2e2e"
        fg = "white"
        entry_bg = "#1e1e1e"

        self.root.configure(bg=bg)
        self.style.theme_use("default")
        self.style.configure("TLabel", background=bg, foreground=fg, font=self.default_font)
        self.style.configure("TButton", background="#444", foreground=fg, font=self.default_font)
        self.style.configure("TCombobox", fieldbackground=entry_bg, background=bg, foreground=fg, padding=2)
        self.style.configure("TEntry", padding=2, relief="flat")

        for widget in [getattr(self, w) for w in ["playlist_entry", "timeout_entry", "connections_entry"] if hasattr(self, w)]:
            widget.configure(bg=entry_bg, fg=fg, insertbackground=fg)
        if hasattr(self, "output_text"):
            self.output_text.configure(bg=entry_bg, fg=fg, insertbackground=fg)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("M3U files", "*.m3u")])
        if file_path:
            self.playlist_entry.delete(0, tk.END)
            self.playlist_entry.insert(0, file_path)
            self.load_categories()

    def load_categories(self):
        path = self.playlist_entry.get()
        if not path:
            messagebox.showwarning("Warning", "Please select a playlist file first.")
            return

        categories = set()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    match = re.search(r'group-title="([^"]+)",?', line)
                    if match:
                        categories.add(match.group(1))

            sorted_categories = sorted(categories)
            sorted_categories.insert(0, "All")
            self.category_combo['values'] = sorted_categories
            self.category_combo.set("All")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load categories:\n{e}")

    def start_scan(self):
        playlist = self.playlist_entry.get()
        try:
            timeout = int(self.timeout_entry.get())
            max_conn = int(self.connections_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Timeout and connections must be numbers.")
            return

        if not playlist:
            messagebox.showerror("Error", "Please select a playlist.")
            return

        category = self.category_var.get()
        if category == "All":
            category = None

        self.output_text.delete("1.0", tk.END)
        threading.Thread(target=self.run_background_scan, args=(playlist, timeout, max_conn, category), daemon=True).start()

    def run_background_scan(self, playlist, timeout, max_conn, category):
        config.PLAYLIST_PATH = playlist
        config.TIMEOUT = timeout
        config.MAX_CONNECTIONS = max_conn
        setup_logging()

        self.append_output("Starting scan...\n", "white")
        self.append_output(f"Timeout: {timeout}s\n", "white")
        self.append_output(f"Connections: {max_conn}\n\n", "white")

        import builtins
        original_print = builtins.print

        def gui_print(*args, **kwargs):
            message = " ".join(str(arg) for arg in args)
            color = "green" if "✓" in message else "red" if "✗" in message else "white"
            self.append_output(message + "\n", color)

        builtins.print = gui_print

        try:
            parse_m3u8_file(playlist, timeout, config.EXTENDED_TIMEOUT, selected_category=category)
        except Exception as e:
            self.append_output(f"Error during scan:\n{e}\n", "red")
        finally:
            builtins.print = original_print

    def append_output(self, message, color="white"):
        self.output_text.insert(tk.END, message, color)
        self.output_text.tag_config("red", foreground="red")
        self.output_text.tag_config("green", foreground="lime")
        self.output_text.tag_config("white", foreground="white")
        self.output_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    def center_window(win, width_pct=0.7, height_pct=0.7):
        win.update_idletasks()
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        width = int(screen_width * width_pct)
        height = int(screen_height * height_pct)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        win.geometry(f"{width}x{height}+{x}+{y}")

    center_window(root)
    app = IPTVApp(root)
    root.mainloop()
