import socket
import json
import time

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 8888       # Same as sender's default port
BUFFER_SIZE = 1024

def main():
    print(f"Starting gesture receiver server on port {PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)  # Allow one connection at a time
        print("Waiting for connection from laptop...")
        
        while True:
            try:
                conn, addr = server_socket.accept()
                print(f"Connected by {addr}")
                data_buffer = ""  # To accumulate partial data
                
                while True:
                    data = conn.recv(BUFFER_SIZE).decode('utf-8')
                    if not data:
                        break
                    
                    data_buffer += data
                    while '\n' in data_buffer:
                        line, data_buffer = data_buffer.split('\n', 1)
                        try:
                            gesture_data = json.loads(line)
                            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(gesture_data['timestamp']))
                            print(f"Received at {timestamp}:")
                            if gesture_data.get('type') == 'gesture':
                                print(f"  Gesture: {gesture_data['data']}")
                                print(f"  Confidence: {gesture_data['confidence']:.1%}")
                                print(f"  Source: {gesture_data['source']}")
                            elif gesture_data.get('type') == 'ball':
                                ball_info = gesture_data['data']
                                print(f"  Ball Position: {ball_info.get('position')}")
                                print(f"  Ball Radius: {ball_info.get('radius')}")
                                print(f"  Ball Color: {ball_info.get('color')}")
                                print(f"  Confidence: {gesture_data['confidence']:.1%}")
                                print(f"  Source: {gesture_data['source']}")
                            else:
                                print(f"  Unknown type: {gesture_data.get('type')}")
                                print(f"  Data: {gesture_data.get('data')}")
                            print("-" * 40)
                            # You can add custom actions here, e.g., control GPIO based on gesture or ball
                        except json.JSONDecodeError:
                            print(f"Invalid JSON received: {line}")
                
                print("Connection closed. Waiting for new connection...")
            except KeyboardInterrupt:
                print("\nStopping server...")
                break
            except Exception as e:
                print(f"Error: {e}. Retrying...")

if __name__ == "__main__":
    main()