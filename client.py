import os
import socket
import threading
import time
import json
import rsa

HOST = "127.0.0.1"
PORT = 33994
ENCODING = "utf-8"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

nickname = input("Please enter your Nickname: ")
receive_mode = True

keys_serialized = client.recv(4096)
keys = json.loads(keys_serialized.decode(ENCODING))
private_key = rsa.PrivateKey.load_pkcs1(keys['private_key'].encode(ENCODING))
public_key = rsa.PublicKey.load_pkcs1(keys['public_key'].encode(ENCODING))

time.sleep(5)
print("You are connected!")


def client_receive():
    while True:
        try:
            encrypted_message = client.recv(1024)
            message = rsa.decrypt(encrypted_message, private_key).decode(ENCODING)
            if message == "nickname?":
                send_encrypted_message(nickname, public_key)
            elif message == "clear":
                clear_console()
            else:
                print(message)
        except:
            if not receive_mode:
                print("You disconnected.")
                break
            else:
                print("Error has occurred")
                client.close()
                break


def client_send():
    while True:
        message = input()
        if message == "/disconnect":
            global receive_mode
            receive_mode = False
            send_encrypted_message(message, public_key)
            client.close()
            break
        else:
            send_encrypted_message(message, public_key)


def clear_console():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def send_encrypted_message(message, pub_key):
    encrypted_message = rsa.encrypt(message.encode(ENCODING), pub_key)
    client.send(encrypted_message)


if __name__ == '__main__':
    receive_thread = threading.Thread(target=client_receive)
    receive_thread.start()

    send_thread = threading.Thread(target=client_send)
    send_thread.start()
