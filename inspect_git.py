import subprocess
try:
    res = subprocess.run(["git", "status"], capture_output=True, text=True)
    print("Git status stdout:\n", res.stdout)
    print("Git status stderr:\n", res.stderr)
    res2 = subprocess.run(["git", "log", "-n", "5", "--oneline"], capture_output=True, text=True)
    print("Git log:\n", res2.stdout)
except Exception as e:
    print("Error running git:", e)
