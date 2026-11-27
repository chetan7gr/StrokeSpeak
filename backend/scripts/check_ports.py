import subprocess
import re

def check_ports():
    print("=== PORT LISTEN STATUS (netstat) ===")
    out = subprocess.check_output("netstat -ano", shell=True, text=True)
    targets = ["8000", "5173", "8001"]
    found = {}
    for line in out.splitlines():
        if "LISTENING" in line:
            for t in targets:
                if f":{t} " in line or f":{t}\t" in line:
                    parts = line.split()
                    pid = parts[-1]
                    found[t] = pid
                    print(f"Port {t}: LISTENING | LocalAddress: {parts[1]} | PID: {pid}")
                    
    for t in targets:
        if t not in found:
            print(f"Port {t}: NOT LISTENING")
            
    print("\n=== PROCESS COMMAND LINES ===")
    for t, pid in found.items():
        try:
            # Query wmic or powershell for process command line
            cmd = f'powershell -Command "Get-CimInstance Win32_Process -Filter \\"ProcessId = {pid}\\" | Select-Object -Property ProcessId, Name, CommandLine | Format-List"'
            p_out = subprocess.check_output(cmd, shell=True, text=True)
            print(f"Port {t} (PID {pid}):\n{p_out.strip()}")
        except Exception as e:
            print(f"Port {t} PID {pid} error: {e}")

if __name__ == "__main__":
    check_ports()
