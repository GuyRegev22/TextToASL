import socket
import threading
import sqlite3
import hashlib
from aes_methods import decrypt_with_rsa, generate_rsa_keys
from cryptography.hazmat.primitives import serialization
import protocol
import signal
import sys


class Server:
    """
    Server class to handle multiple client connections, user authentication, and task distribution.
    This class supports user registration, login, task allocation (ranges), and client disconnection handling.
    Database is used to store user information and manage assigned/unassigned tasks.
    """

    def __init__(self, IP, PORT=5555):
        """
        Initialize the server object with IP, port, and default parameters.

        Args:
            IP (str): IP address to bind the server.
            PORT (int): Port number to listen for client connections.
        """
        self.server_private_key, self.server_public_key = generate_rsa_keys()
        self.IP = IP
        self.PORT = PORT
        self.client_sockets = []  # Active client sockets
        self.lock = threading.Lock()  # Lock for thread-safe operations
        self.stop_event = threading.Event()  # Event to signal shutdown

    def create_socket(self):
        """
        Create and bind the server socket, then start listening for client connections.
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.IP, self.PORT))
        self.server_socket.listen()
        print(f"Server is up and running on port: {self.PORT}")
    
    def handle_key_exchange(self, cl_socket):
        try:
            # Attempt to decode the client hello message
            client_hello = protocol.server_protocol.get_msg_plaintext(cl_socket).decode(encoding="latin-1")
        except UnicodeDecodeError as e:
            print(f"Error decoding client hello message: {e}")
            # Optionally, you can send an error response or handle the failure case
            return None

        # Ensure the loop checks for the correct "Client hello"
        while client_hello != "Client hello":
            try:
                client_hello = protocol.server_protocol.get_msg_plaintext(cl_socket).decode(encoding="latin-1")
            except UnicodeDecodeError as e:
                print(f"Error decoding client hello message during loop: {e}")
                return None

        # Serialize server public key
        print(self.server_public_key)
        serialized_server_public_key = self.server_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Send the public key to the client
        protocol.server_protocol.send_msg_plaintext(cl_socket, serialized_server_public_key)

        try:
            # Receive the encrypted AES key
            encrypted_aes_key = protocol.server_protocol.get_msg_plaintext(cl_socket)
        except Exception as e:
            print(f"Error receiving encrypted AES key: {e}")
            return None

        try:
            # Decrypt the AES key using RSA
            aes_key = decrypt_with_rsa(self.server_private_key, encrypted_aes_key)
        except Exception as e:
            print(f"Error decrypting AES key: {e}")
            return None

        print("RSA-AES Handshake Successfully!")
        print(aes_key)
        return aes_key

    
    def setup_database(self):
        """
        Create and initialize the SQLite database for user management.
        Ensures tables for users exist before starting server operations.
        """
        with self.lock:
            conn = sqlite3.connect("demo.db")
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                username TEXT PRIMARY KEY,
                                password TEXT NOT NULL,
                                phone TEXT NOT NULL
                            )''')
            conn.commit()
            conn.close()
            print("Database initialized.")

    def handle_client(self, cl_socket):
        """
        Handle communication with a single connected client.

        Args:
            cl_socket (socket): The client socket object.
        """
        aes_key = self.handle_key_exchange(cl_socket)
        username = None  # Store the current client's username
        try:
            while not self.stop_event.is_set():
                try:
                    parsed_req = protocol.server_protocol.get_request(cl_socket, aes_key=aes_key)
                    print(parsed_req)
                    if parsed_req[0] == '': 
                        break
                    print(f"[*] Received request: {parsed_req} [*]")

                    if username is None:  # Client not authenticated
                        match parsed_req[0]:
                            case 'REG':  # Registration
                                ret_code = self.register_user(username=parsed_req[1], password=parsed_req[2], phone=parsed_req[3])
                                # if ret_code:
                                #     username = parsed_req[1]
                                protocol.server_protocol.send_register_success(success=ret_code, cl_socket=cl_socket, aes_key=aes_key)

                            case 'LOGIN':  # Login
                                ret_code = self.authenticate_user(username=parsed_req[1], password=parsed_req[2])
                                if ret_code:
                                    username = parsed_req[1]
                                    print(f"[*] {username} Logged In [*]")
                                protocol.server_protocol.send_login_success(aes_key=aes_key, success=ret_code, cl_socket=cl_socket)

                            case _:  # Error: Unauthenticated action
                                protocol.server_protocol.send_error(aes_key=aes_key, cl_socket=cl_socket, error_msg="Error: Client is not logged in!")
                                continue
                    else:  # Authenticated client actions
                        match parsed_req[0]:
                            case 'REQ': # Client requests a translation
                                protocol.server_protocol.send_success(aes_key=aes_key, cl_socket=cl_socket, success=(parsed_req[1]!= ''))
                                data = parsed_req[1]
                                print(f"[*] {username} Requested translation of: {data} [*]")

                                #TO - DO: Implement translation logic
                            case 'LOGOUT':  # Client logout
                                print(f"{username} logged out.")
                                username = None
                            case _:  # Unknown request
                                protocol.server_protocol.send_error(aes_key, cl_socket=cl_socket, error_msg="Error: Unknown request.")
                                break
                except (ConnectionResetError, BrokenPipeError):
                    print(f"Client {username or 'unknown'} disconnected unexpectedly.")
                    break
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            with self.lock:
                if cl_socket in self.client_sockets:
                    self.client_sockets.remove(cl_socket)
            print(f"Client {username or 'unknown'} disconnected.")
            cl_socket.close()

    def register_user(self, username, password, phone):
        """
        Register a new user in the database.

        Args:
            username (str): Username of the client.
            password (str): Password of the client.
            phone (str): Phone number of the client.

        Returns:
            bool: True if registration is successful, False otherwise.
        """
        hashed_pass = hashlib.md5(password.encode()).hexdigest()
        with self.lock:
            conn = sqlite3.connect("demo.db")
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                if user: return False
                cursor.execute("INSERT INTO users (username, password, phone) VALUES (?, ?, ?)",
                               (username, hashed_pass, phone))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()

    def authenticate_user(self, username, password):
        """
        Authenticate a user against the database.

        Args:
            username (str): Username of the client.
            password (str): Password of the client.

        Returns:
            bool: True if the credentials are valid, False otherwise.
        """
        hashed_pass = hashlib.md5(password.encode()).hexdigest()
        with self.lock:
            conn = sqlite3.connect("demo.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_pass))
            user = cursor.fetchone()
            conn.close()
            return user is not None

    def run(self):
        """
        Start accepting client connections and handle them in separate threads.
        """
        while not self.stop_event.is_set():
            try:
                client_socket, addr = self.server_socket.accept()
                self.client_sockets.append(client_socket)
                print(f"Accepted connection from {addr}")
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_handler.start()
            except OSError:
                break

    def shutdown(self):
        """
        Cleanly shut down the server.
        """
        self.stop_event.set()
        self.server_socket.close()
        for sock in self.client_sockets:
            sock.close()
        print("Server shut down cleanly.")


def signal_handler(sig, frame):
    """
    Handle Ctrl+C signal for graceful server shutdown.
    """
    print("\nShutting down the server...")
    server_instance.shutdown()
    sys.exit(0)


def main():
    """
    Main entry point for the server program.
    """
    global server_instance
    server_instance = Server("0.0.0.0", 5555)
    signal.signal(signal.SIGINT, signal_handler)
    server_instance.setup_database()
    server_instance.create_socket()
    server_instance.run()


if __name__ == "__main__":
    main()