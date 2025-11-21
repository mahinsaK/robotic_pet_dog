import blynklib
import subprocess
import threading
import time

BLYNK_AUTH = 'paste_your_actual_auth_token_here'  # Replace with your actual Blynk Auth Token from step 3

# Start the robot script as a subprocess
robot_proc = subprocess.Popen(
    ['python3', '/home/ubuntu/without_ros/p12-6.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

def robot_stdout_reader():
    for line in robot_proc.stdout:
        print('[ROBOT]', line, end='')

# Start a thread to print robot output
threading.Thread(target=robot_stdout_reader, daemon=True).start()

blynk = blynklib.Blynk(BLYNK_AUTH)

# Map Blynk virtual pins to robot commands
BLYNK_COMMANDS = {
    'V0': 'stand\n',
    'V1': 'sit\n',
    'V2': 'walk\n',
    'V3': 'right\n',
    'V4': 'left\n',
    'V5': 'distance\n'
}

for vpin, cmd in BLYNK_COMMANDS.items():
    @blynk.handle_event(f'write {vpin}')
    def handle(pin, value, cmd=cmd):
        if value[0] == '1':
            print(f'[BLYNK] Sending command: {cmd.strip()}')
            robot_proc.stdin.write(cmd)
            robot_proc.stdin.flush()

try:
    while True:
        blynk.run()
        time.sleep(0.1)
except KeyboardInterrupt:
    print('Exiting...')
    robot_proc.terminate()