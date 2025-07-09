import os
import json
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--path", type=str, default=os.getcwd())
parser.add_argument("--json", type=str, default='launchopt.json')
args = parser.parse_args()
    
def main():
    path = args.path
    json_path = os.path.join(args.path, args.json)
    
    # Set defaults
    mem = '16G'
    jarfile = 'paper.jar'
    javapath = 'C:/Program Files/Eclipse Adoptium/jre-21.0.4.7-hotspot/bin/java.exe'
    
    if os.path.isfile(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
            mem = data.get('mem', mem)
            jarfile = data.get('jarfile', jarfile)
            javapath = data.get('javapath', jarfile)

    elif os.path.isfile(os.path.join(path, 'start.bat')):
        subprocess.run(['start.bat'], shell=True)
        return "Starting with start.bat", 404
    else:
        return "Error: Could not find launchopt.json or start.bat", 404

    if jarfile.lower() == 'auto':
        keywords = ['server', 'paper', 'neoforge', 'forge', 'fabric', 'spigot', 'bukkit']
        jars = [f for f in os.listdir(path) if f.lower().endswith('.jar')]
        for keyword in keywords:
            for j in jars:
                if keyword in j.lower():
                    jarfile = j
                    break
            if jarfile != 'auto':
                break
        if jarfile == 'auto':
            print("Error: No matching jar file found for 'auto'")
            return

    java_path = r"C:/Program Files/Eclipse Adoptium/jre-21.0.4.7-hotspot/bin/java.exe"
    command = f'"{java_path}" -Xmx{mem} -jar "{jarfile}" nogui'

    print(f"Running: {command}")
    subprocess.run(command, shell=True)

main()
