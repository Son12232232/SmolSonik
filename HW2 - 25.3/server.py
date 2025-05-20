import socket
import re

def extract_contacts(text):
    pattern = re.compile(r'[\w\.-]+@[\w\.-]+')
    return set(pattern.findall(text))

def start_server(host='127.0.0.1', port=54321):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen()
    print(f"Сервер запущено на {host}:{port}. Очікую з’єднання…")
    while True:
        conn, addr = sock.accept()
        print("Підключився клієнт:", addr)
        data = bytearray()
        while True:
            chunk = conn.recv(1024)
            if not chunk:
                break
            data.extend(chunk)
        text = data.decode('utf-8')
        contacts = extract_contacts(text)
        response = '\n'.join(sorted(contacts))
        conn.sendall(response.encode('utf-8'))
        conn.close()

if __name__ == '__main__':
    start_server()
