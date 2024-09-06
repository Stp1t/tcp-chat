import socket
import threading
import time
from database import setup_database, save_message, get_chat_history, add_room, get_all_rooms
from datetime import datetime
import rsa

HOST = ""
PORT = 33994
ENCODING = "utf-8"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
chatrooms = {}
nicknames = []

setup_database()

with open("private_key.pem", "rb") as private_file:
    private_key = rsa.PrivateKey.load_pkcs1(private_file.read())

with open("public_key.pem", "rb") as public_file:
    public_key = rsa.PublicKey.load_pkcs1(public_file.read())


def broadcast(message, room_name, ip, user_message=False, plain_message=None, plain_nickname=None):
    for client in chatrooms[room_name]:
        send_encrypted_message(client[0], message, public_key)
    if user_message:
        print(f"{get_timestamp()} [{plain_nickname} | {ip}] in {room_name}: {plain_message}")


def handle_client(client, ip):
    while True:
        try:
            encrypted_message = client.recv(1024)
            message = rsa.decrypt(encrypted_message, private_key).decode(ENCODING)
            if not message:
                break

            # create a new room
            if message.startswith("/create"):
                create_room(client, message, ip)
            # join an existing room
            elif message.startswith("/join"):
                join_room(client, message, ip)

                # give overview over existing rooms
            elif message.startswith("/rooms"):
                get_room_overview(client, ip)

            # exit room
            elif message.startswith("/exit"):
                exit_room(client, ip)

            # disconnect from server
            elif message.startswith("/disconnect"):
                disconnect_client(client, get_name_by_client(client), ip)
                print(log_user_info(get_name_by_client(client),
                                    ip) + f" Disconnected.")
                break

            # no command, just simple message
            else:
                handle_client_message(client, message, ip)
        except Exception as err:
            print(f"Error: {err}")
            break


def disconnect_client(client, nickname, ip):
    for room_name in chatrooms:
        if (client, nickname) in chatrooms[room_name]:
            chatrooms[room_name].remove((client, nickname))
            broadcast(f"{nickname} has left the Chatroom.", room_name, ip)

    if client in clients:
        clients.remove(client)

    if nickname in nicknames:
        nicknames.remove(nickname)

    try:
        user_alert = "You have disconnected."
        send_encrypted_message(client, user_alert, public_key)
    except:
        pass

    client.close()
    print(f"{nickname}/{ip} has disconnected.")


def join_room(client, message, ip):
    room_to_join = message.split()[1]
    if room_to_join in [r[0] for r in get_all_rooms()]:
        client_active = False
        client_name = get_name_by_client(client)
        for room_name in chatrooms:
            if (client, client_name) in chatrooms[room_name]:
                client_active = True
        if not client_active:
            broadcast_clear(client)
            chat_history = get_chat_history(room_to_join)
            for msg in chat_history:
                formatted_msg = f"{msg[2]} {msg[0]}: {msg[1]}\n"
                send_encrypted_message(client, formatted_msg, public_key)
                time.sleep(0.1)
            chatrooms[room_to_join].append((client, get_name_by_client(client)))
            broadcast(
                f"{get_name_by_client(client)} has joined the Chatroom {room_to_join}.",
                room_to_join, ip)
            print(log_user_info(get_name_by_client(client),
                                ip) + f" Has joined the Chatroom {room_to_join}")
        else:
            user_alert = "Please leave your current Chatroom before joining a new one."
            send_encrypted_message(client, user_alert, public_key)
            print(log_user_info(get_name_by_client(client),
                                ip) + f" Tried joining the Chatroom {room_to_join} but is currently active "
                                      f"in another Chatroom.")
    else:
        user_alert = f"Chatroom {room_to_join} doesnt exist."
        send_encrypted_message(client, user_alert, public_key)
        print(log_user_info(get_name_by_client(client),
                            ip) + f" Tried joining the Chatroom {room_to_join} but it doesnt exist.")


def create_room(client, message, ip):
    room_name = message.split()[1]
    if room_name not in chatrooms:
        chatrooms[room_name] = []
        add_room(room_name)
        room_created_alert = f"Chatroom {room_name} has been created!"
        send_encrypted_message(client, room_created_alert, public_key)
        print(log_user_info(get_name_by_client(client), ip) + f" Created chatroom '{room_name}'.")

    else:
        room_created_alert = "Chatroom already exists"
        send_encrypted_message(client, room_created_alert, public_key)
        print(log_user_info(get_name_by_client(client),
                            ip) + f" Tried creating chatroom '{room_name}' but it already existed.")


def get_room_overview(client, ip):
    room_overview = "\n".join([r[0] for r in get_all_rooms()])
    send_encrypted_message(client, room_overview, public_key)
    print(log_user_info(get_name_by_client(client),
                        ip) + f" Requested an overview over all active rooms")


def exit_room(client, ip):
    for room_name in chatrooms:
        if (client, get_name_by_client(client)) in chatrooms[room_name]:
            chatrooms[room_name].remove((client, get_name_by_client(client)))
            broadcast_clear(client)
            broadcast(f"{get_name_by_client(client)} has left the Chatroom.", room_name,
                      ip)
            print(log_user_info(get_name_by_client(client),
                                ip) + f" Left the Chatroom {room_name}  ")


def handle_client_message(client, message, ip):
    nickname = get_name_by_client(client)
    client_active = False
    curr_room_name = None
    timestamp = get_timestamp()
    formatted_msg = f"{timestamp} {nickname}: {message}"
    for room_name in chatrooms:
        if (client, nickname) in chatrooms[room_name]:
            client_active = True
            curr_room_name = room_name
    if client_active:
        broadcast(formatted_msg, curr_room_name, ip, True, message, nickname)
        save_message(curr_room_name, nickname, message, timestamp)
    else:
        user_alert = "Please join a Room before sending messages."
        send_encrypted_message(client, user_alert, public_key)


def receive():
    load_rooms()
    while True:
        print("Server is running and listening...")
        client, address = server.accept()
        print(f"connection is established with {address}")
        send_public_key(client)
        time.sleep(7)
        client.send(rsa.encrypt("nickname?".encode(ENCODING), public_key))
        encrypted_nickname = client.recv(1024)
        nickname = rsa.decrypt(encrypted_nickname, private_key).decode(ENCODING)
        nicknames.append(nickname)
        clients.append(client)
        thread = threading.Thread(target=handle_client, args=(client, address[0]))
        thread.start()


def log_user_info(nickname, ip):
    info = f"{get_timestamp()} [{nickname} | {ip}]:"
    return info


def get_name_by_client(client):
    return nicknames[clients.index(client)]


def get_timestamp():
    now = datetime.now()
    return now.strftime("[%d/%m/%y - %H:%M]")


def broadcast_clear(client):
    client.send(rsa.encrypt("clear".encode(ENCODING), public_key))


def load_rooms():
    rooms = get_all_rooms()
    for room_name in rooms:
        chatrooms[room_name[0]] = []


def send_public_key(client):
    with open("public_key.pem", "rb") as public_f:
        public_key_info = public_f.read()
    client.send(public_key_info)


def send_encrypted_message(client, message, pub_key):
    encrypted_message = rsa.encrypt(message.encode(ENCODING), pub_key)
    client.send(encrypted_message)


if __name__ == '__main__':
    receive()

