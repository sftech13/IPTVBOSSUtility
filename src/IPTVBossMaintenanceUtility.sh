#!/usr/bin/env bash

IPTV_PATH="$HOME/IPTVBoss"
LOG_PATH="$IPTV_PATH/logs"
BACKUP_SRC="$IPTV_PATH/backups"
BACKUP_DEST="$HOME/IPTVBoss_Backup"
DB_PATH="$IPTV_PATH/db"
TEMP_PATH="$IPTV_PATH/temp"
CACHE_PATH="$IPTV_PATH/cache"

#───────────────────────────────────────────────────────────────────────────────
# Functions
#───────────────────────────────────────────────────────────────────────────────
pause() {
    read -rp $'\nPress [Enter] to return to the menu...'
}

kill_process() {
    echo
    echo "[1/1] Checking for IPTVBoss process..."
    if pkill -f iptvboss; then
        echo "IPTVBoss process terminated."
    else
        echo "No IPTVBoss process running."
    fi
    pause
}

clean_files() {
    echo
    echo "[1/1] Cleaning lock, temp, and cache files (preserving logs)..."
    rm -f "$IPTV_PATH"/*.lock
    rm -rf "$TEMP_PATH"/* "$CACHE_PATH"/*
    echo "Cleanup complete."
    pause
}

run_nogui_fix() {
    echo
    echo "[1/5] Killing any running IPTVBoss process..."
    pkill -f iptvboss &>/dev/null

    echo "[2/5] Waiting for clean shutdown..."
    sleep 5

    echo "[3/5] Cleaning DB folder (keeping IPTVBoss.mv.db)..."
    for f in "$DB_PATH"/*; do
        [[ "$(basename "$f")" == "IPTVBoss.mv.db" ]] && continue
        rm -f "$f" && echo "Deleted $(basename "$f")"
    done

    echo "[4/5] Launching noGUI sync..."
    cd "$IPTV_PATH" || {
        echo "Cannot cd to $IPTV_PATH"
        pause
        return
    }
    if [[ -f "IPTVBoss.jar" ]]; then
        java -jar IPTVBoss.jar -nogui &
        pid=$!
    elif [[ -x "./IPTVBoss" ]]; then
        ./IPTVBoss -nogui &
        pid=$!
    elif command -v iptvboss &>/dev/null; then
        iptvboss -nogui &
        pid=$!
    else
        echo "Error: Cannot find IPTVBoss executable."
        pause
        return
    fi
    echo "Started noGUI sync (PID $pid)."

    echo "[5/5] Monitoring noGUI sync (every 10s)..."
    while kill -0 "$pid" &>/dev/null; do
        echo "noGUI sync running. Please wait..."
        sleep 10
    done

    echo "noGUI sync finished. You may now launch the IPTVBoss GUI."
    pause
}

check_connectivity() {
    echo
    echo "=== Network & Endpoint Connectivity Test ==="

    echo
    echo "[DNS] Resolving download.iptvboss.pro..."
    if getent hosts download.iptvboss.pro &>/dev/null; then
        echo "[PASS] DNS resolved."
    else
        echo "[FAIL] DNS resolution failed."
    fi

    echo
    echo "[Ping] Pinging download.iptvboss.pro..."
    if ping -c 3 download.iptvboss.pro &>/dev/null; then
        echo "[PASS] Ping successful."
    else
        echo "[WARN] Ping timed out."
    fi

    echo
    echo "[HTTP] HEAD request to https://download.iptvboss.pro..."
    code=$(curl -Ls -o /dev/null -w "%{http_code}" https://download.iptvboss.pro)
    if [[ "$code" == "200" ]]; then
        echo "[PASS] HTTP 200 OK."
    else
        echo "[FAIL] HTTP status $code."
    fi

    read -rp $'\nRun traceroute? (y/n): ' ans
    [[ "$ans" =~ ^[Yy]$ ]] && traceroute download.iptvboss.pro
    pause
}

tail_log() {
    local logtype
    if [[ -n "$1" ]]; then
        logtype="$1"
    else
        echo
        echo "Log Type Filters:"
        echo "  1) IPTVBoss"
        echo "  2) AdvEPGDummy"
        echo "  3) NoGUI"
        echo "  4) All Logs"
        read -rp "Select log type [1-4]: " logtype
    fi
    case "$logtype" in
    1) FILTER="IPTVBoss" ;;
    2) FILTER="AdvEPGDummy" ;;
    3) FILTER="NoGUI" ;;
    4) FILTER="" ;;
    *)
        echo "Invalid selection."
        pause
        return
        ;;
    esac
    file=$(ls -1t "$LOG_PATH"/${FILTER}*.log 2>/dev/null | head -n1)
    if [[ -f "$file" ]]; then
        echo
        echo "Last 50 lines of: $file"
        tail -n 50 "$file"
    else
        echo "No matching log files."
    fi
    pause
}

move_backups() {
    echo
    echo "[1/7] Preparing backup folders..."
    mkdir -p "$BACKUP_DEST"

    echo "[2/7] Moving existing backups..."
    mv -f "$BACKUP_SRC"/* "$BACKUP_DEST"/ 2>/dev/null

    read -rp $'\nDelete DB and clear folders? (y/n): ' yn
    if [[ ! "$yn" =~ ^[Yy]$ ]]; then
        echo "Skipping DB reset."
        pause
        return
    fi

    echo "[3/7] Deleting DB files..."
    rm -f "$DB_PATH"/IPTVBoss.{mv,lock}.db

    echo "[4/7] Clearing cache, emailtemplates, langs, temp..."
    rm -rf "$CACHE_PATH"/* "$IPTV_PATH"/emailtemplates/* "$IPTV_PATH"/langs/* "$TEMP_PATH"/*

    echo "[5/7] Restoring backups..."
    cp -r "$BACKUP_DEST"/* "$BACKUP_SRC"/

    echo "[6/7] Cleaning duplicate DBs..."
    rm -f "$BACKUP_DEST"/*.mv.db "$BACKUP_DEST"/*.lock.db

    echo "[7/7] Backup and DB reset complete."
    pause
}

check_av() {
    echo
    echo "Checking for antivirus (ClamAV)..."
    if command -v clamscan &>/dev/null; then
        echo "ClamAV installed."
    else
        echo "No antivirus detected."
    fi
    pause
}

#───────────────────────────────────────────────────────────────────────────────
# Non-interactive dispatch
#───────────────────────────────────────────────────────────────────────────────
if [[ -n "$1" ]]; then
    choice="$1"
    log_arg="$2"
    pause() { :; }
    case "$choice" in
    1) kill_process ;;
    2) clean_files ;;
    3) run_nogui_fix ;;
    4) check_connectivity ;;
    5) tail_log "$log_arg" ;;
    6) move_backups ;;
    7) check_av ;;
    8) exit 0 ;;
    *)
        echo "Invalid option: $choice" >&2
        exit 1
        ;;
    esac
    exit 0
fi

#───────────────────────────────────────────────────────────────────────────────
# Interactive menu
#───────────────────────────────────────────────────────────────────────────────
while true; do
    clear
    echo "==== IPTVBoss Maintenance Menu ===="
    echo "1) Kill Process"
    echo "2) Clean Files"
    echo "3) Run NoGUI Fix"
    echo "4) Check Connectivity"
    echo "5) Tail Log"
    echo "6) Move Backups"
    echo "7) Check A/V"
    echo "8) Exit"
    read -rp "Select [1-8]: " choice

    case "$choice" in
    1) kill_process ;;
    2) clean_files ;;
    3) run_nogui_fix ;;
    4) check_connectivity ;;
    5) tail_log ;;
    6) move_backups ;;
    7) check_av ;;
    8) exit 0 ;;
    *)
        echo "Invalid option."
        pause
        ;;
    esac
done
