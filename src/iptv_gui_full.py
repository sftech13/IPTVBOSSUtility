import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, simpledialog
import threading
import re
import sys
import os
import subprocess
from iptv_quality_core import run_check, config, parse_m3u8_file, setup_logging
import tkinter.font as font
import shutil
import tempfile

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
            "- Set timeout and max connections (according to your provider)\n"
            "- Optionally choose a category to test\n"
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

        ttk.Label(form, text="Playlist Path:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.playlist_entry = tk.Entry(form, font=self.default_font,
                                       bg="#1e1e1e", fg="white", insertbackground="white")
        self.playlist_entry.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(form, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)

        ttk.Label(form, text="Timeout (s):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.timeout_entry = tk.Entry(form, font=self.default_font,
                                      bg="#1e1e1e", fg="white", insertbackground="white")
        self.timeout_entry.insert(0, "5")
        self.timeout_entry.grid(row=1, column=1, sticky="ew", padx=5)

        ttk.Label(form, text="Max Connections:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.connections_entry = tk.Entry(form, font=self.default_font,
                                          bg="#1e1e1e", fg="white", insertbackground="white")
        self.connections_entry.insert(0, "3")
        self.connections_entry.grid(row=2, column=1, sticky="ew", padx=5)

        ttk.Label(form, text="Category:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form, textvariable=self.category_var,
                                           state="readonly", font=self.default_font)
        self.category_combo.grid(row=3, column=1, sticky="ew", padx=5)
        ttk.Button(form, text="Load Categories", command=self.load_categories).grid(row=3, column=2, padx=5)

        ttk.Button(form, text="Start Scan", command=self.start_scan).grid(row=4, column=1, sticky="e", pady=10)

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
            "- Select a maintenance task from the dropdown\n"
            "- Some actions will auto-run, others enable extra options\n"
            "- 'Run traceroute?' is only enabled for Check Connectivity\n"
            "- Click 'Run' to execute the selected action"
        )
        instruction_label = tk.Label(
            tab, text=instruction_text, justify="left", anchor="w",
            font=self.default_font, bg="#2e2e2e", fg="white"
        )
        instruction_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

        frame = ttk.Frame(tab)
        frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        frame.columnconfigure(1, weight=1)

        actions = [
            "1 - Kill IPTV BOSS Process",
            "2 - Clean Cache",
            "3 - Run NoGUI Fix",
            "4 - Check Connectivity",
            "5 - Check Logs",
            "6 - Move Backups",
            "7 - Antivirus Status/Windows Defender",
            "8 - Speed Test",
            # Optionally only add Flush DNS Cache on Windows
        ]
        if sys.platform.startswith("win"):
            actions.append("9 - Flush DNS Cache")
            actions.append("10 - Port Check")
            actions.append("11 - Update App")
            actions.append("12 - Exit")
        else:
            actions.append("9 - Port Check")
            actions.append("10 - Update App")
            actions.append("11 - Exit")

        ttk.Label(frame, text="Select Action:").grid(row=0, column=0, sticky="w", padx=5)
        self.maint_var = tk.StringVar()
        self.maint_combo = ttk.Combobox(frame, textvariable=self.maint_var,
                                        state="readonly", values=actions)
        self.maint_combo.grid(row=0, column=1, sticky="ew", padx=5)
        self.maint_combo.set(actions[0])

        ttk.Label(frame, text="Log Type:").grid(row=1, column=0, sticky="e", padx=5, pady=(5,0))
        self.logtype_var = tk.StringVar()
        self.logtype_combo = ttk.Combobox(frame, textvariable=self.logtype_var,
                                          state="disabled",
                                          values=[
                                              "1 - IPTVBoss Logs",
                                              "2 - AdvEPGDummy Logs",
                                              "3 - NoGUI Logs",
                                              "4 - All Logs",
                                          ])
        self.logtype_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))
        self.trace_var = tk.BooleanVar(value=False)
        self.trace_chk = ttk.Checkbutton(
            frame,
            text="Run traceroute?",
            variable=self.trace_var,
            state="disabled"
        )
        self.trace_chk.grid(row=2, column=1, sticky="w", padx=5, pady=(5,0))

        def on_action_change(evt=None):
            sel = self.maint_var.get().split(" - ")[0]
            self.logtype_combo.configure(state="readonly" if sel=="5" else "disabled")
            self.trace_chk.configure(state="normal" if sel=="4" else "disabled")

        self.maint_combo.bind("<<ComboboxSelected>>", on_action_change)
        on_action_change()

        ttk.Button(frame, text="Run", command=self.run_selected_maintenance).grid(row=0, column=2, padx=5)

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

        # 1) Run NoGUI Fix (your Python method)
        if idx == "3":
            self.run_nogui_fix()
            return

        # 2) Check Connectivity (special)
        if idx == "4":
            self.maint_output.delete("1.0", tk.END)
            if sys.platform.startswith("win"):
                script    = resource_path("win_functions.bat")
                trace_arg = "-t" if self.trace_var.get() else ""
                cmd       = f'cmd.exe /c "{script} {idx} {trace_arg}"'
                shell     = True
            else:
                script = resource_path("linux_functions.sh")
                tr      = "--traceroute" if self.trace_var.get() else ""
                cmd     = f"bash '{script}' {idx} {tr}"
                shell   = True
            threading.Thread(target=self._run_process,
                            args=(cmd, self.maint_output, shell),
                            daemon=True).start()
            return

        # 3) Prompt for port if doing Port Check
        port_arg = None
        if idx == "10":
            p = simpledialog.askinteger("Port Check",
                                    "Enter port number:",
                                    parent=self.root,
                                    minvalue=1, maxvalue=65535)
            if p is None:
                return
            port_arg = str(p)

        # 4) Tail-log argument if tail log
        log_arg = None
        if idx == "5" and self.logtype_var.get():
            log_arg = self.logtype_var.get().split(" - ")[0]

        # 5) Build argument list
        args = [idx]
        if log_arg:  args.append(log_arg)
        if port_arg: args.append(port_arg)

        # 6) Dispatch everything else
        if sys.platform.startswith("win"):
            script_call = f'"{resource_path("win_functions.bat")}" ' + " ".join(args)
            cmd = f'cmd.exe /c {script_call}'
            shell = True
        else:
            script_call = f"bash '{resource_path('linux_functions.sh')}' " + " ".join(args)
            cmd = script_call
            shell = True

        self.maint_output.delete("1.0", tk.END)
        threading.Thread(target=self._run_process,
                        args=(cmd, self.maint_output, shell),
                        daemon=True).start()

    def _run_process(self, cmd, output_widget, use_shell=False):
        si = None
        if use_shell and sys.platform.startswith("win"):
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        popen_kwargs = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=use_shell
        )
        if si is not None:
            popen_kwargs["startupinfo"] = si

        proc = subprocess.Popen(cmd, **popen_kwargs)
        for line in proc.stdout:
            output_widget.insert(tk.END, line)
            output_widget.see(tk.END)
        proc.wait()



    def run_nogui_fix(self):
        if sys.platform.startswith("win"):
            batch_code = r"""@echo off
    echo [1/6] Closing IPTVBoss-related processes...

    taskkill /F /IM IPTVBoss.exe >nul 2>&1

    echo [2/6] Waiting briefly to ensure clean shutdown...
    timeout /t 5 /nobreak >nul

    echo [3/6] Cleaning up IPTVBoss DB folder (except IPTVBoss.mv.db)...

    set "dbpath=%USERPROFILE%\IPTVBoss\db"

    for %%f in ("%dbpath%\*") do (
        if /I not "%%~nxf"=="IPTVBoss.mv.db" (
            echo Deleting: %%f
            del /f /q "%%f" >nul 2>&1
        )
    )

    echo [4/6] Launching NoGUI sync...

    set "bossdir=%USERPROFILE%\IPTVBoss"
    cd /d "%bossdir%"

    start "" /B IPTVBoss.exe -nogui

    echo [5/6] Monitoring NoGUI sync process, Please be patient... 

    :waitloop
    timeout /t 10 /nobreak >nul
    tasklist /FI "IMAGENAME eq IPTVBoss.exe" | find /I "IPTVBoss.exe" >nul
    if %ERRORLEVEL%==0 (
        echo noGUI TEST is currently running. Please wait patiently...
        goto waitloop
    )

    echo [6/6] NoGUI sync finished. You may now launch IPTVBoss normally.
    timeout /t 5 /nobreak >nul
    exit
    """
            with tempfile.NamedTemporaryFile('w', suffix='.bat', delete=False) as f:
                f.write(batch_code)
                bat_path = f.name

            # Only use creationflags on Windows!
            subprocess.Popen(
                ['cmd.exe', '/k', bat_path],
                creationflags=getattr(subprocess, 'CREATE_NEW_CONSOLE', 0)
            )

            messagebox.showinfo(
                "Manual Step",
                "A terminal window has opened and will perform the NoGUI fix steps.\n\n"
                "When finished, close the window and return here."
            )

        else:
            # Linux: Call your existing shell function directly
            script = os.path.join(os.path.dirname(__file__), "linux_functions.sh")
            if not os.path.isfile(script):
                messagebox.showerror("Missing Script", f"linux_functions.sh not found at:\n{script}")
                return

            # You can show output in the maint_output widget, or run in terminal
            cmd = ["bash", script, "3"]
            def run_shell():
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
                )
                out = []
                for line in proc.stdout:
                    out.append(line)
                    self.maint_output.insert(tk.END, line)
                    self.maint_output.see(tk.END)
                proc.wait()
                if proc.returncode == 0:
                    messagebox.showinfo("Done", "NoGUI fix completed.")
                else:
                    messagebox.showerror("Error", "NoGUI fix failed. See output for details.")


            threading.Thread(target=run_shell, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    def center(win, w_pct=0.5, h_pct=0.5):
        win.update_idletasks()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        w, h   = int(sw*w_pct), int(sh*h_pct)
        x, y   = (sw-w)//2, (sh-h)//2
        win.geometry(f"{w}x{h}+{x}+{y}")
    center(root)
    app = IPTVApp(root)
    root.mainloop()
