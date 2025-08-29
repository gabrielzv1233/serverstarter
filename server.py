import os
import json
import argparse
import subprocess
import re
import sys

import os, sys, time, psutil, subprocess, textwrap

def start_title_usage_monitor(interval=0.5, pid=None, include_parent=True, include_top_ancestor=False):
    me = psutil.Process(os.getpid())
    root = me
    if pid is not None:
        target_pid = int(pid)
    else:
        if include_parent:
            try: root = me.parent() or me
            except Exception: pass
        if include_top_ancestor:
            try:
                while root.parent(): root = root.parent()
            except Exception: pass
        target_pid = root.pid

    code = textwrap.dedent(f"""\
        import os, sys, time, psutil
        def set_title(t):
            if os.name == 'nt':
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetConsoleTitleW(t)
                except Exception:
                    os.system('title ' + t)
            else:
                sys.stdout.write('\\33]0;' + t + '\\a'); sys.stdout.flush()

        def get_tree(pid):
            try: root = psutil.Process(pid)
            except psutil.NoSuchProcess: return []
            procs = [root]
            try: procs += root.children(recursive=True)
            except Exception: pass
            out = []
            for p in procs:
                try: _ = p.status(); out.append(p)
                except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied): pass
            return out

        def prime_cpu(procs):
            for p in procs:
                try: p.cpu_percent(None)
                except Exception: pass

        def sum_usage(procs):
            c = 0.0; r = 0
            for p in procs:
                try:
                    c += p.cpu_percent(None)
                    r += p.memory_info().rss
                except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied): pass
            return c, r

        pid = {target_pid}
        interval = {float(interval)}
        while True:
            procs = get_tree(pid)
            if not procs: break
            prime_cpu(procs)
            time.sleep(interval)
            cpu, rss = sum_usage(procs)
            total = psutil.virtual_memory().total or 1
            mp = rss / total * 100.0
            mb = rss / (1024*1024)
            set_title(f'CPU {{cpu:.1f}}% | Mem {{mb:.1f}}MB ({{mp:.1f}}%)')
    """)

    subprocess.Popen([sys.executable, "-c", code],
                     close_fds=True,
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)


parser = argparse.ArgumentParser()
parser.add_argument("--path", type=str, default=os.getcwd())
parser.add_argument("--json", type=str, default='launchopts.json')
parser.add_argument("--java", type=str, default="C:/Program Files/Eclipse Adoptium/jre-21.0.4.7-hotspot/bin/java.exe")
parser.add_argument("--mem", type=str, default="16G")
parser.add_argument("--jar", type=str, default="paper.jar")
parser.add_argument("--gui", action="store_true")
args = parser.parse_args()

def validate_mem(mem):
    if re.fullmatch(r'\d+[MG]', mem.upper()):
        return mem.upper()
    print(f"Invalid --mem value: '{mem}'. Use format like '16G' or '1024M'")
    sys.exit(1)

def main():
    path = os.path.abspath(args.path)
    json_path = os.path.join(path, args.json)

    default_java = "C:/Program Files/Eclipse Adoptium/jre-21.0.4.7-hotspot/bin/java.exe"
    default_mem = "16G"
    default_jar = "paper.jar"

    mem = validate_mem(args.mem)
    jarfile = default_jar
    java_path = default_java
    use_gui = args.gui

    if os.path.isfile(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)

        if args.mem != default_mem:
            print(f"Using --mem {mem} instead of config")
        else:
            mem = validate_mem(data.get('mem', mem))

        if args.jar != default_jar:
            print(f"Using --jar {args.jar} instead of config")
            jarfile = args.jar
        else:
            jarfile = data.get('jarfile', jarfile)

        if args.java != default_java:
            print(f"Using --java {args.java} instead of config")
            java_path = args.java
        else:
            java_path = data.get('javapath', java_path)

        if args.gui:
            print("Using --gui instead of config")
        use_gui = use_gui or data.get('gui', False)

    elif os.path.isfile(os.path.join(path, 'start.bat')):
        return 200, 0, os.path.join(path, "start.bat")
    else:
        return 404, 1, None

    if isinstance(jarfile, str) and jarfile.lower() == 'auto':
        keywords = ['server', 'paper', 'neoforge', 'forge', 'fabric', 'spigot', 'bukkit']
        jars = [f for f in os.listdir(path) if f.lower().endswith('.jar')]
        found = False
        for keyword in keywords:
            for j in jars:
                if keyword in j.lower():
                    jarfile = j
                    found = True
                    break
            if found:
                break
        if not found:
            return 404, 2, None

    nogui_args = [] if use_gui else ["nogui"]
    command = [java_path, f"-Xmx{mem}", "-jar", jarfile, *nogui_args]
    pretty = " ".join([f'"{c}"' if " " in c else c for c in command])
    print(f"Running: {pretty}")
    return 200, -1, command

status, code, command = main()

if status == 404:
    message = "Error 404: "
else:
    message = ""

if code == -1:
    message += f"Starting with {os.path.join(os.path.abspath(args.path), args.json)}"
if code == 0:
    message += "Starting with start.bat"
elif code == 1:
    message += "Could not find a start option"
elif code == 2:
    message += "Could not find a server jar file"

if message:
    print(message)

try:
    if status == 200:
        wd = os.path.abspath(args.path)
        if code == 0 and isinstance(command, str) and command.endswith(".bat"):
            subprocess.run(command, shell=True, cwd=wd)
        elif code == 0 and isinstance(command, str):
            subprocess.run(command, shell=True, cwd=wd)
        elif code == -1 and isinstance(command, list):
            subprocess.run(command, shell=False, cwd=wd)
except KeyboardInterrupt:
    pass
