import os
import socket
import threading
import rsa

HOST = "127.0.0.1"
PORT = 33994

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

nickname = input("Please enter your Nickname: ")
receive_mode = True

public_key_data = client.recv(1024)
public_key = rsa.PublicKey.load_pkcs1(public_key_data)


def client_receive():
    while True:
        try:
            message = client.recv(1024).decode("utf-8")
            if message == "nickname?":
                client.send(nickname.encode("utf-8"))
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
            client.send(rsa.encrypt(message.encode("utf-8"), public_key))
            client.close()
            break
        else:
            client.send(rsa.encrypt(message.encode("utf-8"), public_key))


def clear_console():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


receive_thread = threading.Thread(target=client_receive)
receive_thread.start()

send_thread = threading.Thread(target=client_send)
send_thread.start()
