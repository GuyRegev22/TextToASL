from aes_methods import aes_decrypt, aes_encrypt
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class Protocol:
    """
    Protocol for communication between client and server using a custom message format.
    
    All commands and parameters are separated by `|`.
    Commands:
    
    Client -> Server:
    - REG: Register a user, requires two parameters: username and password.
    - LOGIN: Log in a user, requires two parameters: username and password.
    - LOGOUT: Log out the current user, requires zero parameters.
    - GETRANGE: Request a range of numbers to check, requires zero parameters.
    - FINISHEDRANGE: Notify the server that the client has finished processing a range, requires zero parameters.
    - FOUND: Notify the server that the client found a number, requires one parameter: the number.

    Server -> Client:
    - RANGE: Send a range of numbers to the client, with two parameters: start and end.
    """

    LENGTH_FIELD_SIZE = 8  # Defines the fixed size for the message length field (8 characters).

    @staticmethod
    def send_msg(data, socket, aes_key) -> None:
        """
        Sends a message over the socket with a prefixed length field.
        
        Args:
        - data (str): The message to send.
        - socket: The socket through which the message will be sent.
        """
        encrypted_message = aes_encrypt(aes_key, data)
        msg_length = str(len(encrypted_message))
        zfill_length = msg_length.zfill(Protocol.LENGTH_FIELD_SIZE)
        msg = zfill_length.encode(encoding="latin-1") + encrypted_message
        socket.send(msg)
        print(f"Sent: {msg}")

    @staticmethod
    def get_msg(my_socket, aes_key):
        """
        Receives a message from the socket, extracting and verifying its length.
        
        Args:
        - my_socket: The socket from which the message will be received.
        
        Returns:
        - str: The decoded message without the length field.
        - "Error" if the length field is invalid.
        """
        msg_length = my_socket.recv(Protocol.LENGTH_FIELD_SIZE).decode(encoding="latin-1")
        if msg_length == "":
            return ""
        while len(msg_length) < Protocol.LENGTH_FIELD_SIZE:
            msg_length += my_socket.recv(Protocol.LENGTH_FIELD_SIZE - len(msg_length)).decode(encoding="latin-1")
        try:
            msg_length = int(msg_length)
        except ValueError as e:            
            return f"Error {e}"

        encrypted_message = my_socket.recv(msg_length) #should it use decode()?
        while len(encrypted_message) < msg_length:
            encrypted_message += my_socket.recv(msg_length - len(encrypted_message))
        decrypted_message = aes_decrypt(aes_key, encrypted_message)
        return decrypted_message.decode(encoding="latin-1")

    def send_msg_plaintext(socket, plaintext):
        # Ensure plaintext is in bytes
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()  # Encode string to bytes
        elif not isinstance(plaintext, bytes):
            raise TypeError("plaintext must be a string or bytes")
        
        # Calculate length and prepare message
        msg_length = str(len(plaintext))
        zfill_length = msg_length.zfill(Protocol.LENGTH_FIELD_SIZE)
        msg = zfill_length.encode(encoding="latin-1") + plaintext
        socket.send(msg)


    def get_msg_plaintext (socket):
        msg_length = socket.recv(Protocol.LENGTH_FIELD_SIZE).decode(encoding="latin-1")
        if msg_length == "":
            return ""
        while len(msg_length) < Protocol.LENGTH_FIELD_SIZE:
            msg_length += socket.recv(Protocol.LENGTH_FIELD_SIZE - len(msg_length)).decode(encoding="latin-1")
        try:
            msg_length = int(msg_length)
        except ValueError as e:            
            return f"Error {e}"

        plaintext = socket.recv(msg_length)
        while len(plaintext) < msg_length:
            plaintext += socket.recv(msg_length - len(plaintext))
        return plaintext#.decode(encoding="latin-1")

class client_protocol(Protocol):
    """
    Client-side implementation of the Protocol, with methods for sending specific commands.
    """

    @staticmethod
    def register(cl_socket, aes_key, username, password, phone_number) -> str:
        """
        Sends a registration request to the server.
        
        Args:
        - username (str): The username to register.
        - password (str): The password for the account.
        
        Returns:
        - str: The server's response.
        """
        client_protocol.send_msg(f"REG|{username}|{password}|{phone_number}".encode(encoding="latin-1"), cl_socket, aes_key)
        return Protocol.get_msg(cl_socket, aes_key)

    @staticmethod
    def logout(cl_socket, aes_key) -> None:
        """
        Sends a logout request to the server.
        """
        client_protocol.send_msg("LOGOUT".encode(encoding="latin-1"), cl_socket, aes_key)

    @staticmethod
    def login(cl_socket, aes_key, username, password) -> bool:
        """
        Sends a login request to the server.
        
        Args:
        - username (str): The username to log in.
        - password (str): The password for the account.
        
        Returns:
        - bool: True if login is successful, False otherwise.
        """
        msg_login = (f"LOGIN|{username}|{password}".encode(encoding="latin-1"))
        client_protocol.send_msg(msg_login, cl_socket, aes_key)
        print(msg_login)
        
        msg = client_protocol.get_msg(cl_socket, aes_key)
        if msg.startswith("Error"):
            return False
        return msg == "Logged in successfully"
    
    @staticmethod
    def send_req (request, cl_socket, aes_key) -> bool: 
        client_protocol.send_msg(f"REQ|{request}".encode(encoding="latin-1"), cl_socket, aes_key)
        msg = client_protocol.get_msg(cl_socket, aes_key)
        if msg.startswith("Error"):
            return False
        return msg == "Success"




class server_protocol(Protocol):
    """
    Server-side implementation of the Protocol, with methods for handling client requests.
    """

    @staticmethod
    def is_valid(msg: str) -> bool:
        """
        Validates the format of an incoming message.
        
        Args:
        - msg (str): The message to validate.
        
        Returns:
        - bool: True if the message is valid, False otherwise.
        """
        if msg == "":
            return True
        msg_split = msg.split("|")
        if msg_split[0] not in ["REG", "LOGIN", "LOGOUT", "REQ"]:
            return False
        command = msg_split[0]
        match command:
            case "REG":
                return len(msg_split) == 4
            case "LOGIN":
                return len(msg_split) == 3
            case "REQ":
                return len(msg_split) == 2
            case "LOGOUT":
                return len(msg_split) == 1
        return True

    @staticmethod
    def get_request(cl_socket, aes_key) -> list[str]:
        """
        Receives and validates a client request.
        
        Returns:
        - list[str]: The parsed request as a list of strings.
        """
        decrypted_message = server_protocol.get_msg(cl_socket, aes_key)
        while not server_protocol.is_valid(decrypted_message):
            server_protocol.send_error(cl_socket=cl_socket)
            decrypted_message = server_protocol.get_msg(cl_socket, aes_key)
        return decrypted_message.split("|")

    @staticmethod
    def send_error(cl_socket, aes_key, error_msg: str=None) -> None:
        """
        Sends an error message to the client.
        """
        if error_msg is None:
            server_protocol.send_msg("Server Error".encode(encoding="latin-1"), cl_socket, aes_key)
        else:
            server_protocol.send_msg(f"Server Error|{error_msg}".encode(encoding="latin-1"), cl_socket, aes_key)

    @staticmethod
    def send_login_success(cl_socket, aes_key, success: bool) -> None:
        """
        Sends a login success or failure message to the client.
        
        Args:
        - success (bool): True if login is successful, False otherwise.
        """
        if success:
            server_protocol.send_msg("Logged in successfully".encode(encoding="latin-1"), cl_socket, aes_key)
        else:
            server_protocol.send_error(cl_socket=cl_socket, aes_key=aes_key)

    @staticmethod
    def send_register_success(cl_socket, aes_key, success: bool) -> None:
        """
        Sends a registration success or failure message to the client.
        
        Args:
        - success (bool): True if registration is successful, False otherwise.
        """
        if success:
            server_protocol.send_msg("Registered successfully".encode(encoding="latin-1"), cl_socket, aes_key)
        else:
            server_protocol.send_error(cl_socket=cl_socket, aes_key=aes_key)

    def send_success(cl_socket, aes_key, success: bool) -> None:
        """
        Sends a success or failure message to the client.
        
        Args:
        - success (bool): True if the operation is successful, False otherwise.
        """
        if success:
            server_protocol.send_msg("Success".encode(encoding="latin-1"), cl_socket, aes_key)
        else:
            server_protocol.send_error(cl_socket=cl_socket, aes_key=aes_key)