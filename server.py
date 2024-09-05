import socket
import threading
import time
from database import setup_database, save_message, get_chat_history, add_room, get_all_rooms
from datetime import datetime
import rsa

HOST = ""
PORT = 33994

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
chatrooms = {}
nicknames = []

setup_database()

with open("private_key.pem", "rb") as private_file:
    private_key = rsa.PrivateKey.load_pkcs1(private_file.read())


def broadcast(message, room, ip, user_message=False, plain_message=None, plain_user=None):
    for client in chatrooms[room]:
        client[0].send(message)
    if user_message:
        print(f"{get_timestamp()} [{plain_user} | {ip}] in {room}: {plain_message}")


def handle_client(client, ip):
    while True:
        try:
            encrypted_message = client.recv(1024)
            message = rsa.decrypt(encrypted_message, private_key).decode("utf-8")
            if not message:
                break

            # create a new room
            if message.startswith("/create"):
                room_name = message.split()[1]
                if room_name not in chatrooms:
                    chatrooms[room_name] = []
                    add_room(room_name)
                    client.send(f"Chatroom {room_name} has been created!".encode("utf-8"))
                    print(log_user_info(get_name_by_client(client), ip) + f" Created chatroom '{room_name}'.")

                else:
                    client.send("Chatroom already exists.".encode("utf-8"))
                    print(log_user_info(get_name_by_client(client),
                                        ip) + f" Tried creating chatroom '{room_name}' but it already existed.")

            # join an existing room
            elif message.startswith("/join"):
                room_name = message.split()[1]
                if room_name in [r[0] for r in get_all_rooms()]:
                    client_active = False
                    client_name = get_name_by_client(client)
                    for room in chatrooms:
                        if (client, client_name) in chatrooms[room]:
                            client_active = True
                    if not client_active:
                        broadcast_clear(client)
                        chat_history = get_chat_history(room_name)
                        for msg in chat_history:
                            client.send(f"{msg[2]} {msg[0]}: {msg[1]}\n".encode('utf-8'))
                        chatrooms[room_name].append((client, get_name_by_client(client)))
                        broadcast(
                            f"{get_name_by_client(client)} has joined the Chatroom {room_name}.".encode("utf-8"),
                            room_name, ip)
                        print(log_user_info(get_name_by_client(client),
                                            ip) + f" Has joined the Chatroom {room_name}")
                    else:
                        client.send("Please leave your current Chatroom before joining a new one.".encode("utf-8"))
                        print(log_user_info(get_name_by_client(client),
                                            ip) + f" Tried joining the Chatroom {room_name} but is currently active "
                                                  f"in another Chatroom.")
                else:
                    client.send(f"Chatroom {room_name} doesnt exist.".encode("utf-8"))
                    print(log_user_info(get_name_by_client(client),
                                        ip) + f" Tried joining the Chatroom {room_name} but it doesnt exist.")

            # give overview over existing rooms
            elif message.startswith("/rooms"):
                room_overview = "\n".join([r[0] for r in get_all_rooms()])
                client.send(room_overview.encode("utf-8"))
                print(log_user_info(get_name_by_client(client),
                                    ip) + f" Requested an overview over all active rooms")

            # exit room
            elif message.startswith("/exit"):
                for room in chatrooms:
                    if (client, get_name_by_client(client)) in chatrooms[room]:
                        chatrooms[room].remove((client, get_name_by_client(client)))
                        broadcast_clear(client)
                        broadcast(f"{get_name_by_client(client)} has left the Chatroom.".encode("utf-8"), room,
                                  ip)
                        print(log_user_info(get_name_by_client(client),
                                            ip) + f" Left the Chatroom {room}  ")

            # disconnect from server
            elif message.startswith("/disconnect"):
                disconnect_client(client, get_name_by_client(client), ip)
                print(log_user_info(get_name_by_client(client),
                                    ip) + f" Disconnected.")
                break

            # no command, just simple message
            else:
                client_name = get_name_by_client(client)
                client_active = False
                curr_room = None
                timestamp = get_timestamp()
                formatted_msg = f"{timestamp} {client_name}: {message}"
                for room in chatrooms:
                    if (client, client_name) in chatrooms[room]:
                        client_active = True
                        curr_room = room
                if client_active:
                    broadcast(formatted_msg.encode("utf-8"), curr_room, ip, True, message, client_name)
                    save_message(curr_room, client_name, message, timestamp)
                else:
                    client.send("Please join a Room before sending messages.".encode("utf-8"))

        except Exception as err:
            print(f"Error: {err}")
            break


def disconnect_client(client, name, ip):
    for room in chatrooms:
        if (client, name) in chatrooms[room]:
            chatrooms[room].remove((client, name))
            broadcast(f"{name} has left the Chatroom.".encode("utf-8"), room, ip)

    if client in clients:
        clients.remove(client)

    if name in nicknames:
        nicknames.remove(name)

    try:
        client.send("You have disconnected.".encode("utf-8"))
    except:
        pass

    client.close()
    print(f"{name}/{ip} has disconnected.")


def log_user_info(user, ip):
    info = f"{get_timestamp()} [{user} | {ip}]:"
    return info


def get_name_by_client(client):
    return nicknames[clients.index(client)]


def get_timestamp():
    now = datetime.now()
    return now.strftime("[%d/%m/%y - %H:%M]")


def broadcast_clear(client):
    client.send("clear".encode("utf-8"))


def load_rooms():
    rooms = get_all_rooms()
    for room in rooms:
        chatrooms[room[0]] = []


def send_public_key(client):
    with open("public_key.pem", "rb") as public_file:
        public_key = public_file.read()
    client.send(public_key)


def receive():
    load_rooms()
    while True:
        print("Server is running and listening...")
        client, address = server.accept()
        print(f"connection is established with {address}")
        send_public_key(client)
        time.sleep(7)
        client.send("nickname?".encode("utf-8"))
        nickname = client.recv(1024).decode("utf-8")
        nicknames.append(nickname)
        clients.append(client)
        thread = threading.Thread(target=handle_client, args=(client, address[0]))
        thread.start()


if __name__ == '__main__':
    receive()
