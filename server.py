from gettext import find
import socket
import threading
import spotipy
from spotipy.oauth2 import SpotifyOAuth

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def init_auth_manager():
    with open('token-data_server.txt', 'r') as file:
        cred_data = file.readlines()

    scope = 'user-library-read user-read-playback-state user-modify-playback-state user-read-currently-playing'

    auth_manager = SpotifyOAuth(
        client_id=cred_data[0].strip(), 
        client_secret=cred_data[1].strip(), 
        redirect_uri=cred_data[2].strip(), 
        scope=scope)

    return auth_manager


"""
Asks user for which playback device they'd like and returns the device id.
"""
def select_device(avail_devices):
    device_names = [*avail_devices]
    device_names = list(avail_devices.keys())

    if len(device_names) == 0:
        return

    user_input = -1

    while user_input-1 not in range(len(device_names)):
        try:
            print()
            for i in range(len(device_names)):
                print(f"({i+1}) {device_names[i]}")
            print()

            print("Enter the number that corresponds with your player.")
            user_input = int(input("> "))
        except ValueError:
            print("[ERROR] Please enter a valid number.")


    return avail_devices[device_names[user_input-1]]
    

"""
Calls API to grab the available devices user can interact with.
"""
def get_avail_devices(sp):
    avail_devices = dict()
    results = sp.devices()
    
    # print(len(results['devices']))

    if len(results['devices']) != 0:
        for i in range(len(results['devices'])):
            avail_devices[results['devices'][i]['name']] = results['devices'][i]['id']
    else:
        print("[ERROR] There are no available devices.")
    
    return avail_devices


"""
Plays a provided track on a provided device.
"""    
def play_track(sp, device_id, track_id):
    uris_list = []
    uris_list.append(track_id)

    sp.start_playback(device_id=device_id, uris=uris_list)


def handle_client(conn, addr, sp, device_id):
    print(f"[NEW CONNECTION] {addr} connected.")
    # conn.send("[CONNECTED] You connected to the host".encode(FORMAT))

    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False

            print(f"[{addr}] {msg}")
            match msg:
                case "playing":
                    track_info = sp.currently_playing()
                    track_name = track_info['item']['name']
                    track_artist = track_info['item']['album']['artists'][0]['name']
                    track_album = track_info['item']['album']['name']

                    conn.send(f"Name: {track_name} | Artist: {track_artist}  | Album: {track_album}".encode(FORMAT))
                

            if ("https://open.spotify.com/track/") in msg:
                play_track(sp, device_id, msg)
                track_info = sp.currently_playing()
                track_name = track_info['item']['name']
                track_artist = track_info['item']['album']['artists'][0]['name']
                conn.send(f"[ADDED] ({track_name} by {track_artist}) added to queue.".encode(FORMAT))

            

    conn.close()


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")

    # Placed API build inside of start fuhnction for organization
    auth_manager = init_auth_manager()
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Host must select device player when initializing server.
    avail_devices = get_avail_devices(sp)
    device_id = select_device(avail_devices)

    while True:
        if device_id == None:
            break
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr, sp, device_id))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    
    print("[CLOSING] server is stopping...")


print("[STARTING] server is starting...")
start()
