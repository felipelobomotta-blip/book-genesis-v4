import sys
import subprocess

model = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else 'gemini-3.1-pro-high'
prompt = sys.stdin.read()

cmd = [
    r'C:\Users\felip\AppData\Local\agy\bin\agy.EXE',
    '--print',
    prompt,
    '--output-format',
    'text',
    '--model',
    model
]

proc = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)

if proc.returncode != 0:
    sys.stderr.write(proc.stderr or proc.stdout)
    sys.exit(proc.returncode)

sys.stdout.write(proc.stdout)
