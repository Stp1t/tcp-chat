# TCP Chat
This project is a simple terminal-based chat application built on the TCP Protocol. It encrypts all messages using <a href=https://en.wikipedia.org/wiki/RSA_(cryptosystem)> RSA </a> encryption. Chat histories are stored in an SQLite database.
 ## Running the Project
### 1. Clone the project
Use the following command:
``` 
git clone https://github.com/Stp1t/tcp-chat.git
 ```
### 2. Install Dependencies
Run:
```
pip install -r requirements.txt
```
### 3. Generate RSA Keys
The ```keys.py``` file will automatically generate them for you, just run:
```
python keys.py
```
### 4. Start the Server and run the Client
Run the following two commands:
```
python server.py
```
```
python client.py
```
You will be asked to enter a nickname for the chat.
Please wait until 'You are connected' appears in the terminal before typing.

## Commands
Once you are connected, you can use the following commands in the chat:

**Creating new rooms:**
```
/create <room_name>  
```
**Joining rooms:**
```
/join <room_name>
```
**Overview of existing rooms:**
```
/rooms
```
**Leaving current room:**
```
/exit
```
**Disconnecting from server**
```
/disconnect
```
