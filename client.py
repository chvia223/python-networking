from multiprocessing.sharedctypes import Value
import socket
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)


def init_client_cred_manager():
    with open('token-data_client.txt', 'r') as file:
        cred_data = file.readlines()

    scope = 'user-library-read user-read-playback-state user-modify-playback-state'

    client_cred_manager = SpotifyClientCredentials(
        client_id=cred_data[0].strip(), 
        client_secret=cred_data[1].strip()
    )
    
    print(cred_data[0])

    return client_cred_manager

def main_display():
    client_cred_manager = init_client_cred_manager()
    sp = spotipy.Spotify(client_credentials_manager=client_cred_manager)
    song_selection = dict()  

    while True:
        print()
        print("==========================================")
        print()
        print("(1) Display currently playing song.")
        print("(2) Search for a song.")
        print("(3) Add song from last search to queue.")
        print("(4) Quit and disconnect.")
        print()
        print("==========================================")
        print("Please enter a selection:")
        user_input = input("> ")

        match user_input:
            case "1":
                print()
                print("[CURRENTLY PLAYING]")
                send("playing")
            case "2":
                song_selection = search_tracks(sp, song_selection)
            case "3":
                if len(song_selection) == 0:
                    print("[Error] You must make a new search before you can select a song.")
                    continue
                track_id = select_track(song_selection)
                print()
                send(track_id)
            case "4":
                break    


def select_track(song_selection):
    for i in range(len(song_selection.keys())):
        print(f"{i+1:3}", f"{song_selection[i+1][0]:60}", "|", f"{song_selection[i+1][1]:30}")

    while True:
        try:
            user_select = int(input("Which song would you like you add to queue? \n> "))
        except ValueError:
            print("[ERROR] Please enter a valid number.")
        else:
            break

    # need to do data validation on this later.
    return song_selection[user_select][2]


"""
Calls track search endpoint and populates a dictionary with results.
"""
def search_tracks(sp, song_selection):
    user_search = input("What is the name of the track you'd like to search for: \n> ")
    results = sp.search(q='track:' + user_search, type='track', limit=20)
    
    # This is to make sure the search results refresh. If I implemented things differently then I probably wouldn't
    # need to do something like this.
    song_selection.clear()

    print("  # | TRACK TITLE                                                  | ARTISTS")
    print("----------------------------------------------------------------------------------------")

    for idx, track in enumerate(results['tracks']['items']):
        song_selection[idx+1] = [track['name'], track['album']['artists'][0]['name'], track['external_urls']['spotify']]
        print(f"{idx+1:3}", "|", f"{track['name']:60}", "|", f"{track['album']['artists'][0]['name']:30}")

    return song_selection


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))

    client.send(send_length)
    client.send(message)
    print(client.recv(2048).decode(FORMAT))


try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    main_display()
except ConnectionRefusedError:
    print("[ERROR] Bad connection. You may have the wrong IP Address or the server may be down.")
