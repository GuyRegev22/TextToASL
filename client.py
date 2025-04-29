<<<<<<< HEAD
import socket
import re
import hashlib
import multiprocessing
import threading
import time
from protocol import client_protocol
import sys

class client:
    """
    Represents a client that communicates with a server to register, log in, 
    perform hash calculations, and execute other protocol-defined commands.
    """
    server_ip = "127.0.0.1"  # Server IP address
    server_port = 5555       # Server port
    connected = False        # Connection state
    client_socket = socket.socket()  # Client socket
    found = False
    start_time = 0

    def __init__(self):
        """
        Initializes the client instance.
        Sets up initial variables such as username.
        """
        self.username = ""

    def is_valid_username(self, username) -> bool:
        """
        Validates the username based on predefined rules.

        :param username: The username string to validate.
        :return: True if valid, False otherwise.
        """
        return (4 <= len(username) <= 16 and
                re.fullmatch(r"[a-zA-Z0-9]+", username) is not None)

    def is_valid_password(self, password) -> bool:
        """
        Validates the password based on predefined rules.

        :param password: The password string to validate.
        :return: True if valid, False otherwise.
        """
        return (6 <= len(password) <= 16 and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password) and
                re.fullmatch(r"[a-zA-Z0-9]+", password) is not None)

    def user_connection(self):
        """
        Collects and validates user credentials (username and password) from input.

        :return: A tuple containing the username and password.
        """
        username = ""
        while not self.is_valid_username(username):
            username = input("Enter a username: ").strip()
            if not self.is_valid_username(username):
                print("Invalid username. Use only letters and numbers.")

        password = ""
        while not self.is_valid_password(password):
            password = input("Enter a password: ").strip()
            if not self.is_valid_password(password):
                print("Invalid password. Must include at least one uppercase letter and one digit.")

        self.username = username
        return username, password

    def register(self):
        """
        Handles user registration by collecting a username, password, and phone number.

        :return: The response from the server.
        """
        username, password = self.user_connection()
        phone_number = input("Enter your phone number: ").strip()
        while len(phone_number) != 10 or not phone_number.isdigit():
            print("Invalid phone number. Please enter a 10-digit number.")
            phone_number = input("Enter your phone number: ").strip()

        return client_protocol.register(self.client_socket, username, password, phone_number)

    def login(self):
        """
        Handles user login by collecting a username and password.

        :return: The response from the server.
        """
        username, password = self.user_connection()
        return client_protocol.login(self.client_socket, username, password)

    def logout(self):
        """
        Handles user logout.

        :return: The response from the server.
        """
        return client_protocol.logout(self.client_socket)

    def handle_user_input(self, user_input):
        """
        Processes user commands and calls the appropriate method.

        :param user_input: The input command from the user.
        :return: The result of the command execution or None if invalid.
        """
        if user_input is None:
            return
        command = user_input.strip().lower()

        if command == "register":
            if self.connected:
                print("You are already connected.")
            else:
                return self.register()
        elif command == "login":
            if self.connected:
                print("You are already connected.")
            else:
                return self.login()
        elif command == "logout":
            if self.connected:
                return self.logout()
            else:
                print("You are not connected.")
        else:
            print("Invalid input.")

    def calc_hash(self, args):
        """
        Finds the number in the range [start, end] that matches the given MD5 hash.

        :param args: A tuple (start, end, target_hash).
        :return: The matching number or None if not found.
        """
        start, end, target_hash = args
        for number in range(start, end + 1):
            if hashlib.md5(str(number).encode()).hexdigest() == target_hash:
                return number
        return None

    def find_md5_match_multiprocessing(self, start, end, target_hash, num_processes=None):
        """
        Uses multiprocessing to find the number that matches the given MD5 hash.

        :param start: The start of the range.
        :param end: The end of the range.
        :param target_hash: The target MD5 hash.
        :param num_processes: Number of processes (default is the number of CPU cores).
        :return: The matching number or None if not found.
        """
        if num_processes is None:
            num_processes = multiprocessing.cpu_count()

        range_size = end - start + 1
        chunk_size = range_size // num_processes
        chunks = [
            (start + i * chunk_size, min(start + (i + 1) * chunk_size - 1, end), target_hash)
            for i in range(num_processes)
        ]
        if chunks[-1][1] < end:
            chunks[-1] = (chunks[-1][0], end, target_hash)

        with multiprocessing.Pool(processes=num_processes) as pool:
            results = pool.map(self.calc_hash, chunks)
            for result in results:
                if result is not None:
                    return result
        return None

    def input_thread(self):
        """
        Runs in a separate thread to handle user input during the connection.
        Allows the user to log out or perform other actions.
        """
        time.sleep(3)
        while self.connected and not self.found:
            user_input = input("Enter logout to exit: \n").strip().lower()
            if user_input.lower() == "logout":
                print("Logging out...")
                self.logout()
                self.connected = False
                break
            else:
                print(self.handle_user_input(user_input))

    def main(self):
        """
        Main client logic for connecting to the server, managing input threads,
        and processing server communication.
        """
        print("searching for connection...")
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
        except socket.error as e:
            print(f"Failed to connect to the server: {e}")
            return

        try:
            while not self.found:
                print("\n--- Client Menu ---")
                print("1. Register")
                print("2. Login")
                print("3. Logout")
                choice = input("Enter your choice: ").strip()
                ans = self.handle_user_input(choice)
                while not ans:
                    print("Error occurred. Try again.")
                    choice = input("Enter your choice: ").strip()
                    ans = self.handle_user_input(choice)
                self.connected = True
                input_thread = threading.Thread(target=self.input_thread, daemon = True)
                input_thread.start()
                self.start_time = time.time()
                i = 0
                while not self.found and self.connected:
                    ans = client_protocol.get_range(self.client_socket, self.username)
                    while not ans:
                        ans = client_protocol.get_range(self.client_socket, self.username)
                    if time.time() - self.start_time > 5: 
                        print("Seraching for number" + ('.  ' if i== 0 else '.' * (i + 1)), end='\r', flush=True)
                        i = (i + 1) % 3       

                    if isinstance(ans, int):
                        self.found = True
                        print("Number found. Stopping search.")
                        print(f"The number was: {ans}" )
                        print("Thank you for helping!")
                        sys.exit()
                    start, end, target_hash = ans
                    result = self.find_md5_match_multiprocessing(start, end, target_hash)
                    if result is not None:
                        client_protocol.send_found(self.client_socket, result)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.client_socket.close()

if __name__ == "__main__":
    client_inst = client()
    client_inst.main()  # Create the client instance
=======
import socket
import re
import hashlib
import multiprocessing
import threading
import time
from protocol import client_protocol
import sys

class client:
    """
    Represents a client that communicates with a server to register, log in, 
    perform hash calculations, and execute other protocol-defined commands.
    """
    server_ip = "127.0.0.1"  # Server IP address
    server_port = 5555       # Server port
    connected = False        # Connection state
    client_socket = socket.socket()  # Client socket
    found = False
    start_time = 0

    def __init__(self):
        """
        Initializes the client instance.
        Sets up initial variables such as username.
        """
        self.username = ""

    def is_valid_username(self, username) -> bool:
        """
        Validates the username based on predefined rules.

        :param username: The username string to validate.
        :return: True if valid, False otherwise.
        """
        return (4 <= len(username) <= 16 and
                re.fullmatch(r"[a-zA-Z0-9]+", username) is not None)

    def is_valid_password(self, password) -> bool:
        """
        Validates the password based on predefined rules.

        :param password: The password string to validate.
        :return: True if valid, False otherwise.
        """
        return (6 <= len(password) <= 16 and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password) and
                re.fullmatch(r"[a-zA-Z0-9]+", password) is not None)

    def user_connection(self):
        """
        Collects and validates user credentials (username and password) from input.

        :return: A tuple containing the username and password.
        """
        username = ""
        while not self.is_valid_username(username):
            username = input("Enter a username: ").strip()
            if not self.is_valid_username(username):
                print("Invalid username. Use only letters and numbers.")

        password = ""
        while not self.is_valid_password(password):
            password = input("Enter a password: ").strip()
            if not self.is_valid_password(password):
                print("Invalid password. Must include at least one uppercase letter and one digit.")

        self.username = username
        return username, password

    def register(self):
        """
        Handles user registration by collecting a username, password, and phone number.

        :return: The response from the server.
        """
        username, password = self.user_connection()
        phone_number = input("Enter your phone number: ").strip()
        while len(phone_number) != 10 or not phone_number.isdigit():
            print("Invalid phone number. Please enter a 10-digit number.")
            phone_number = input("Enter your phone number: ").strip()

        return client_protocol.register(self.client_socket, username, password, phone_number)

    def login(self):
        """
        Handles user login by collecting a username and password.

        :return: The response from the server.
        """
        username, password = self.user_connection()
        return client_protocol.login(self.client_socket, username, password)

    def logout(self):
        """
        Handles user logout.

        :return: The response from the server.
        """
        return client_protocol.logout(self.client_socket)

    def handle_user_input(self, user_input):
        """
        Processes user commands and calls the appropriate method.

        :param user_input: The input command from the user.
        :return: The result of the command execution or None if invalid.
        """
        if user_input is None:
            return
        command = user_input.strip().lower()

        if command == "register":
            if self.connected:
                print("You are already connected.")
            else:
                return self.register()
        elif command == "login":
            if self.connected:
                print("You are already connected.")
            else:
                return self.login()
        elif command == "logout":
            if self.connected:
                return self.logout()
            else:
                print("You are not connected.")
        else:
            print("Invalid input.")

    def calc_hash(self, args):
        """
        Finds the number in the range [start, end] that matches the given MD5 hash.

        :param args: A tuple (start, end, target_hash).
        :return: The matching number or None if not found.
        """
        start, end, target_hash = args
        for number in range(start, end + 1):
            if hashlib.md5(str(number).encode()).hexdigest() == target_hash:
                return number
        return None

    def find_md5_match_multiprocessing(self, start, end, target_hash, num_processes=None):
        """
        Uses multiprocessing to find the number that matches the given MD5 hash.

        :param start: The start of the range.
        :param end: The end of the range.
        :param target_hash: The target MD5 hash.
        :param num_processes: Number of processes (default is the number of CPU cores).
        :return: The matching number or None if not found.
        """
        if num_processes is None:
            num_processes = multiprocessing.cpu_count()

        range_size = end - start + 1
        chunk_size = range_size // num_processes
        chunks = [
            (start + i * chunk_size, min(start + (i + 1) * chunk_size - 1, end), target_hash)
            for i in range(num_processes)
        ]
        if chunks[-1][1] < end:
            chunks[-1] = (chunks[-1][0], end, target_hash)

        with multiprocessing.Pool(processes=num_processes) as pool:
            results = pool.map(self.calc_hash, chunks)
            for result in results:
                if result is not None:
                    return result
        return None

    def input_thread(self):
        """
        Runs in a separate thread to handle user input during the connection.
        Allows the user to log out or perform other actions.
        """
        time.sleep(3)
        while self.connected and not self.found:
            user_input = input("Enter logout to exit: \n").strip().lower()
            if user_input.lower() == "logout":
                print("Logging out...")
                self.logout()
                self.connected = False
                break
            else:
                print(self.handle_user_input(user_input))

    def main(self):
        """
        Main client logic for connecting to the server, managing input threads,
        and processing server communication.
        """
        print("searching for connection...")
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
        except socket.error as e:
            print(f"Failed to connect to the server: {e}")
            return

        try:
            while not self.found:
                print("\n--- Client Menu ---")
                print("1. Register")
                print("2. Login")
                print("3. Logout")
                choice = input("Enter your choice: ").strip()
                ans = self.handle_user_input(choice)
                while not ans:
                    print("Error occurred. Try again.")
                    choice = input("Enter your choice: ").strip()
                    ans = self.handle_user_input(choice)
                self.connected = True
                input_thread = threading.Thread(target=self.input_thread, daemon = True)
                input_thread.start()
                self.start_time = time.time()
                i = 0
                while not self.found and self.connected:
                    ans = client_protocol.get_range(self.client_socket, self.username)
                    while not ans:
                        ans = client_protocol.get_range(self.client_socket, self.username)
                    if time.time() - self.start_time > 5: 
                        print("Seraching for number" + ('.  ' if i== 0 else '.' * (i + 1)), end='\r', flush=True)
                        i = (i + 1) % 3       

                    if isinstance(ans, int):
                        self.found = True
                        print("Number found. Stopping search.")
                        print(f"The number was: {ans}" )
                        print("Thank you for helping!")
                        sys.exit()
                    start, end, target_hash = ans
                    result = self.find_md5_match_multiprocessing(start, end, target_hash)
                    if result is not None:
                        client_protocol.send_found(self.client_socket, result)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.client_socket.close()

if __name__ == "__main__":
    client_inst = client()
    client_inst.main()  # Create the client instance
>>>>>>> aeab024 (An update of the translating system)
