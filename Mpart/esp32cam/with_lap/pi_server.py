import socket
import json

def start_server(host='0.0.0.0', port=8888):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Server listening on {host}:{port}")

    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f"Connected to {addr}")
            while True:
                data = client_socket.recv(1024).decode('utf-8').strip()
                if not data:
                    break
                try:
                    gesture_data = json.loads(data)
                    print(f"Received Gesture: {gesture_data['gesture']} "
                          f"(Confidence: {gesture_data['confidence']:.1%}) "
                          f"at {gesture_data['timestamp']}")
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
            client_socket.close()
            print(f"Disconnected from {addr}")
        except Exception as e:
            print(f"Server error: {e}")
        except KeyboardInterrupt:
            print("\nStopping server...")
            break

    server_socket.close()

if __name__ == "__main__":
    start_server()