import sys
sys.path.append('/home/taiunse/.local/lib/python3.12/site-packages')
import socket, keyboard
port = 6566
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('',port))
server.listen(1)
print('keyboard event server listening on port',port)

clients = []  

def event_handler(e):
    cp = clients.copy()
    for client in cp:
        try:
            client.sendall(bytes(e.name,'utf-8'))
        except:
            clients.remove(client)

keyboard.on_press(event_handler)

while True:
    conn, addr = server.accept()
    clients.append(conn)
