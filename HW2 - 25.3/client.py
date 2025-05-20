import socket
import sys

def send_file(filename, host='127.0.0.1', port=54321):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            sock.sendall(line.encode('utf-8'))
    sock.shutdown(socket.SHUT_WR)
    data = bytearray()
    while True:
        chunk = sock.recv(1024)
        if not chunk:
            break
        data.extend(chunk)
    print('Контакти:')
    print(data.decode('utf-8'))
    sock.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Використання: python client.py <якийсь файл>')
        sys.exit(1)
    send_file(sys.argv[1])
