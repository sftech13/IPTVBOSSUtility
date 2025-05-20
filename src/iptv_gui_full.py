import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import threading
import re
import sys
import os
import subprocess
from iptv_quality_core import run_check, config, parse_m3u8_file, setup_logging
import tkinter.font as font

def resource_path(rel_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, rel_path)

class IPTVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IPTV BOSS Maintenance Tool")

        # Fonts & theme
        self.default_font = font.Font(family="Segoe UI", size=10)
        self.output_font  = font.Font(family="Courier New", size=10)
        self.style        = ttk.Style()
        self.configure_theme()

        # Layout
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Maintenance tab
        self.maint_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.maint_tab, text="Maintenance")
        self.setup_maintenance_tab()
        
        # Stream Checker tab
        self.checker_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.checker_tab, text="Stream Checker")
        self.setup_checker_tab()



    def configure_theme(self):
        bg, fg, entry_bg = "#2e2e2e", "white", "#1e1e1e"
        self.root.configure(bg=bg)
        self.style.theme_use("default")
        self.style.configure("TLabel",     background=bg, foreground=fg, font=self.default_font)
        self.style.configure("TButton",    background="#444", foreground=fg, font=self.default_font)
        self.style.configure("TCombobox",  fieldbackground=entry_bg, background=bg,
                             foreground=fg, padding=2, font=self.default_font)
        self.style.configure("TEntry",     padding=2, relief="flat")

    def setup_checker_tab(self):
        tab = self.checker_tab
        tab.rowconfigure(2, weight=1)
        tab.columnconfigure(0, weight=1)


        instruction_text = (
            "📋 Instructions:\n"
            "- Load your .m3u playlist file\n"
            "- Set timeout and max connections\n"
            "- Optionally choose a category\n"
            "- Click 'Start Scan' to begin"
        )

        instruction_label = tk.Label(
            tab, text=instruction_text, justify="left", anchor="w",
            font=self.default_font, bg="#2e2e2e", fg="white"
        )
        instruction_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        
        form = ttk.Frame(tab)
        form.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        form.columnconfigure(1, weight=1)

        # Playlist
        ttk.Label(form, text="Playlist Path:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.playlist_entry = tk.Entry(form, font=self.default_font,
                                       bg="#1e1e1e", fg="white", insertbackground="white")
        self.playlist_entry.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(form, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)

        # Timeout
        ttk.Label(form, text="Timeout (s):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.timeout_entry = tk.Entry(form, font=self.default_font,
                                      bg="#1e1e1e", fg="white", insertbackground="white")
        self.timeout_entry.insert(0, "5")
        self.timeout_entry.grid(row=1, column=1, sticky="ew", padx=5)

        # Connections
        ttk.Label(form, text="Max Connections:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.connections_entry = tk.Entry(form, font=self.default_font,
                                          bg="#1e1e1e", fg="white", insertbackground="white")
        self.connections_entry.insert(0, "3")
        self.connections_entry.grid(row=2, column=1, sticky="ew", padx=5)

        # Category
        ttk.Label(form, text="Category:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form, textvariable=self.category_var,
                                           state="readonly", font=self.default_font)
        self.category_combo.grid(row=3, column=1, sticky="ew", padx=5)
        ttk.Button(form, text="Load Categories", command=self.load_categories).grid(row=3, column=2, padx=5)

        # Start button
        ttk.Button(form, text="Start Scan", command=self.start_scan).grid(row=4, column=1,
                                                                          sticky="e", pady=10)

        # Output pane
        self.output_text = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD, font=self.output_font,
            bg="#1e1e1e", fg="white", insertbackground="white"
        )
        self.output_text.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0,10))

    def setup_maintenance_tab(self):
        tab = self.maint_tab
        tab.rowconfigure(3, weight=1)
        tab.columnconfigure(0, weight=1)
        
        instruction_text = (
    "🛠 Maintenance Instructions:\n"
    "| Select a maintenance task from the dropdown\n"
    "| Some actions will auto-run, others enable extra options\n"
    "| 'Run traceroute?' is only enabled for Connectivity\n"
    "| Click 'Run' to execute the selected action"
        )
        instruction_label = tk.Label(
            tab, text=instruction_text, justify="left", anchor="w",
            font=self.default_font, bg="#2e2e2e", fg="white"
        )
        instruction_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))


        frame = ttk.Frame(tab)
        frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        frame.columnconfigure(1, weight=1)

        # Action dropdown
        ttk.Label(frame, text="Select Action:").grid(row=0, column=0, sticky="w", padx=5)
        actions = [
            "1 - Kill IPTV BOSS Process",
            "2 - Clean Cache",
            "3 - Run NoGUI Fix",
            "4 - Check Connectivity",
            "5 - Check Logs",
            "6 - Move Backups",
            "7 - Antivirus Status/Windows Defender",
        ]
        self.maint_var   = tk.StringVar()
        self.maint_combo = ttk.Combobox(frame, textvariable=self.maint_var,
                                        state="readonly", values=actions)
        self.maint_combo.grid(row=0, column=1, sticky="ew", padx=5)
        self.maint_combo.set(actions[0])

        # Log-type dropdown (for Tail Log)
        ttk.Label(frame, text="Log Type:").grid(row=1, column=0, sticky="e", padx=5, pady=(5,0))
        self.logtype_var   = tk.StringVar()
        self.logtype_combo = ttk.Combobox(frame, textvariable=self.logtype_var,
                                          state="disabled",
                                          values=[
                                              "1 - IPTVBoss Logs",
                                              "2 - AdvEPGDummy Logs",
                                              "3 - NoGUI Logs",
                                              "4 - All Logs",
                                          ])
        self.logtype_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))

        # Traceroute checkbox (for Connectivity)
        self.trace_var = tk.BooleanVar(value=False)
        self.trace_chk = ttk.Checkbutton(
            frame,
            text="Run traceroute?",
            variable=self.trace_var,
            state="disabled"
        )
        self.trace_chk.grid(row=2, column=1, sticky="w", padx=5, pady=(5,0))

        # Show/hide logic
        def on_action_change(evt=None):
            sel = self.maint_var.get().split(" - ")[0]
            self.logtype_combo.configure(state="readonly" if sel=="5" else "disabled")
            self.trace_chk.configure(state="normal" if sel=="4" else "disabled")

        self.maint_combo.bind("<<ComboboxSelected>>", on_action_change)
        on_action_change()

        # Run button
        ttk.Button(frame, text="Run", command=self.run_selected_maintenance)\
            .grid(row=0, column=2, padx=5)

        # Output pane
        self.maint_output = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD, font=self.output_font,
            bg="#1e1e1e", fg="white", insertbackground="white"
        )
        self.maint_output.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0,10))

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("M3U files", "*.m3u")])
        if path:
            self.playlist_entry.delete(0, tk.END)
            self.playlist_entry.insert(0, path)
            self.load_categories()

    def load_categories(self):
        path = self.playlist_entry.get()
        if not path:
            messagebox.showwarning("Warning", "Select a playlist first.")
            return
        cats = set()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    m = re.search(r'group-title="([^"]+)', line)
                    if m:
                        cats.add(m.group(1))
            vals = ["All"] + sorted(cats)
            self.category_combo['values'] = vals
            self.category_combo.set("All")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load categories:\n{e}")

    def start_scan(self):
        playlist = self.playlist_entry.get()
        try:
            timeout = int(self.timeout_entry.get())
            max_conn = int(self.connections_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Timeout/connections must be numbers.")
            return
        if not playlist:
            messagebox.showerror("Error", "Select a playlist.")
            return
        category = self.category_var.get()
        if category == "All":
            category = None
        self.output_text.delete("1.0", tk.END)
        threading.Thread(
            target=self.run_background_scan,
            args=(playlist, timeout, max_conn, category),
            daemon=True
        ).start()

    def run_background_scan(self, playlist, timeout, max_conn, category):
        config.PLAYLIST_PATH    = playlist
        config.TIMEOUT          = timeout
        config.MAX_CONNECTIONS  = max_conn
        setup_logging()

        import builtins
        orig_print = builtins.print
        def gui_print(*args, **kwargs):
            msg = " ".join(str(a) for a in args)
            col = "green" if "✓" in msg else "red" if "✗" in msg else "white"
            self.append_output(msg + "\n", col)
        builtins.print = gui_print

        try:
            parse_m3u8_file(playlist, timeout, config.EXTENDED_TIMEOUT,
                            selected_category=category)
        except Exception as e:
            self.append_output(f"Error during scan:\n{e}\n", "red")
        finally:
            builtins.print = orig_print

    def append_output(self, message, color="white"):
        self.output_text.insert(tk.END, message)
        self.output_text.tag_config("red",   foreground="red")
        self.output_text.tag_config("green", foreground="lime")
        self.output_text.tag_config("white", foreground="white")
        self.output_text.see(tk.END)

    def run_selected_maintenance(self):
        sel = self.maint_var.get()
        idx = sel.split(" - ")[0]

        # Connectivity check now runs DNS, ping, HTTP and optional traceroute
        if idx == "4":
            self.maint_output.delete("1.0", tk.END)
            threading.Thread(target=self._run_connectivity, daemon=True).start()
            return

        # Tail-log argument
        log_arg = None
        if idx == "5" and self.logtype_var.get():
            log_arg = self.logtype_var.get().split(" - ")[0]

        # Build piped command
        if sys.platform.startswith("win"):
            script = resource_path("win_functions.bat")
            script_call = f'"{script}" {idx}' + (f' {log_arg}' if log_arg else '')
            cmd = f'cmd.exe /c "echo {idx} & echo 8 | {script_call}"'
            use_shell = True
        else:
            script = resource_path("linux_functions.sh")
            script_call = f"bash '{script}' {idx}" + (f' {log_arg}' if log_arg else '')
            cmd = f"printf '{idx}\\n8\\n' | {script_call}"
            use_shell = True

        self.maint_output.delete("1.0", tk.END)
        threading.Thread(
            target=self._run_process,
            args=(cmd, self.maint_output, use_shell),
            daemon=True
        ).start()

    def _run_connectivity(self):
        host = "download.iptvboss.pro"
        # DNS
        self.maint_output.insert(tk.END, "\n[DNS] Resolving DNS to IPTV BOSS...\n")
        dns = subprocess.call(["getent", "hosts", host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.maint_output.insert(tk.END, "[PASS] DNS resolved.\n" if dns == 0 else "[FAIL] DNS resolution failed.\n")

        # Ping
        self.maint_output.insert(tk.END, "\n[PING] Pinging IPTV BOSS...\n")
        ping = subprocess.call(["ping", "-c", "3", host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.maint_output.insert(tk.END, "[PASS] Ping successful.\n" if ping == 0 else "[WARN] Ping timed out.\n")

        # HTTP
        self.maint_output.insert(tk.END, "\n[HTTP] HEAD request to IPTV BOSS...\n")
        code = subprocess.check_output(
            ["curl", "-Ls", "-o", "/dev/null", "-w", "%{http_code}", "https://download.iptvboss.pro"],
            text=True
        ).strip()
        self.maint_output.insert(tk.END, "[PASS] HTTP 200 OK.\n" if code == "200" else f"[FAIL] HTTP status {code}.\n")

        # Traceroute if enabled
        if self.trace_var.get():
            self.maint_output.insert(tk.END, "\n[TRACEROUTE]\n")
            cmd = ["traceroute", "-n", host] if not sys.platform.startswith("win") else ["tracert", "-d", host]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                self.maint_output.insert(tk.END, line)
        self.maint_output.see(tk.END)

    def _run_process(self, cmd, output_widget, use_shell=False):
        try:
            if use_shell and sys.platform.startswith("win"):
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, shell=True, startupinfo=si
                )
            else:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, shell=use_shell
                )
            for line in proc.stdout:
                output_widget.insert(tk.END, line)
                output_widget.see(tk.END)
            proc.wait()
        except Exception as e:
            output_widget.insert(tk.END, f"Error running maintenance: {e}\n")

if __name__ == "__main__":
    root = tk.Tk()
    def center(win, w_pct=0.6, h_pct=0.6):
        win.update_idletasks()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        w, h   = int(sw*w_pct), int(sh*h_pct)
        x, y   = (sw-w)//2, (sh-h)//2
        win.geometry(f"{w}x{h}+{x}+{y}")
    center(root)
    app = IPTVApp(root)
    root.mainloop()
