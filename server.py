import os
import json
import argparse
import subprocess
import re
import sys

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
    path = args.path
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
                print(f"Using --gui instead of config")
            use_gui = use_gui or data.get('gui', False)

    elif os.path.isfile(os.path.join(path, 'start.bat')):
        return 200, 0, os.path.join(path, "start.bat")
    else:
        return 404, 1, None

    if jarfile.lower() == 'auto':
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

    nogui_flag = "" if use_gui else " nogui"
    command = f'"{java_path}" -Xmx{mem} -jar "{jarfile}"{nogui_flag}'
    print(f"Running: {command}")
    return 200, -1, command

status, code, command = main()

if status == 404:
    message = "Error 404: "
else:
    message = ""

if code == -1:
    message += f"Starting with {os.path.join(args.path, args.json)}"
if code == 0:
    message += "Starting with start.bat"
elif code == 1:
    message += "Could not find a start option"
elif code == 2:
    message += "Could not find a server jar file"

if message:
    print(message)

if status == 200:
    if code == 0 and command.endswith(".bat"):
        subprocess.run([command], shell=True)
    else:
        subprocess.run(command, shell=True)
