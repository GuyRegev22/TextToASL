<<<<<<< HEAD
import os
import tkinter as tk
from tkinter import messagebox
import socket
import re
import hashlib
import multiprocessing
import threading
import time
from aes_methods import decrypt_with_rsa, encrypt_with_rsa, generate_rsa_keys
from protocol import client_protocol
from cryptography.hazmat.primitives import serialization
import sys

class ClientGUI:
    def __init__(self, root):
        self.client_private_key, self.client_public_key = generate_rsa_keys()
        self.aes_key = None
        self.root = root
        self.root.title("Client GUI")
        self.root.geometry("800x600")
        self.server_ip = "127.0.0.1"
        self.server_port = 5555
        self.client_socket = socket.socket()
        self.connected = False
        self.username = ""
        self.found = False
        self.start_time = 0
        self.logged_in = False

        self.root.withdraw() # hide root
        self.connect_to_server()
        if not self.connected:
            self.root.destroy()
            return
        self.root.deiconify() # show root after connection
        self.setup_gui()
        self.label.config(text="Please register or login.")

    def handle_key_exchange(self):
        sock = self.client_socket
        client_protocol.send_msg_plaintext(sock, "Client hello")
        serialized_server_public_key = client_protocol.get_msg_plaintext(sock)
        print("server publickey: ", serialized_server_public_key)
        server_public_key = serialization.load_pem_public_key(serialized_server_public_key)
        self.aes_key = os.urandom(32)  # AES-256
        print("aes key: ", self.aes_key)
        encrypted_aes_key = encrypt_with_rsa(server_public_key, self.aes_key)
        client_protocol.send_msg_plaintext(sock, encrypted_aes_key)
    
    def setup_gui(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=20, pady=20)

        self.username_label = tk.Label(self.frame, text="Username:", font=("Arial", 18))
        self.username_entry = tk.Entry(self.frame, font=("Arial", 18))

        self.pass_label = tk.Label(self.frame, text="Password:", font=("Arial", 18))
        
        self.password_entry = tk.Entry(self.frame,font=("Arial", 18), show="*")
        

        self.phone_label = tk.Label(self.frame, text="Phone Number:", font=("Arial", 18))
        self.phone_entry = tk.Entry(self.frame,font=("Arial", 18))
        

        self.register_button = tk.Button(self.frame, text="Register", font=("Arial", 16), command=self.register)
        

        self.login_button = tk.Button(self.frame, text="Login",font=("Arial", 16), command=self.login)
        

        self.logout_button = tk.Button(self.frame, text="Logout",font=("Arial", 16), command=self.logout)
        self.label = tk.Label(self.frame, text="Welcome to the Client GUI", font=("Arial", 22))


        self.logged_out_gui()

        


        self.request_entry = tk.Entry(self.frame, font=("Arial", 20))
        self.instruction_label =  tk.Label(self.frame, text=f"Welcome {self.username} \nenter a sentence to translate", font=("Arial", 25))

        # Center the window on the screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        # Set focus back to the username entry after displaying messages
        self.root.focus_force()
        self.username_entry.focus_set()

    def connect_to_server(self):
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.connected = True
            self.handle_key_exchange()
            messagebox.showinfo("Connection", "Connected to server successfully.")
        except socket.error as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")

    def validate_username(self, username):
        return (4 <= len(username) <= 16 and
                re.fullmatch(r"[a-zA-Z0-9]+", username) is not None)

    def validate_password(self, password):
        return (6 <= len(password) <= 16 and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password) and
                re.fullmatch(r"[a-zA-Z0-9]+", password) is not None)

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        phone_number = self.phone_entry.get()

        if not self.validate_username(username):
            messagebox.showerror("Invalid Username", "Username must be 4-16 characters, letters, or numbers.")
            self.username_entry.focus_set()
            return

        if not self.validate_password(password):
            messagebox.showerror("Invalid Password", "Password must be 6-16 characters, include 1 uppercase and 1 digit.")
            self.password_entry.focus_set()
            return

        if len(phone_number) != 10 or not phone_number.isdigit():
            messagebox.showerror("Invalid Phone Number", "Phone number must be 10 digits.")
            self.phone_entry.focus_set()
            return

        try:
            response = client_protocol.register(self.client_socket, self.aes_key, username, password, phone_number)
            if response:
                messagebox.showinfo("Success", "Registration Successful")
                self.label.config(text="You have registered, Please click login.")
            else:
                messagebox.showerror("Failed", "Registration on server failed")
                self.label.config(text="Please retry registration.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        self.username_entry.focus_set()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Validate username/password first
        if not self.validate_username(username) or not self.validate_password(password):
            messagebox.showerror("Invalid Input", "Invalid username or password format.")
            self.username_entry.focus_set()
            return

        try:
            response = client_protocol.login(self.client_socket, self.aes_key, username, password)
            if response:
                messagebox.showinfo("Success", "Login Successful")
                self.connected = True
                self.username = username

                # Hide all widgets except the logout button and label
                self.logged_in_gui()
            else:
                messagebox.showerror("Failed", "Login Failed")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        self.username_entry.focus_set()

    def logged_in_gui (self):
        for widget in self.frame.winfo_children():        
            widget.grid_remove()

        self.label.grid_remove()
        self.instruction_label.grid(row=0, column=0, ipady=10, columnspan=3)
        self.request_entry.grid(row=3, column=0, columnspan=3, ipady=10)
        self.request_entry.focus_set
        self.send_button = tk.Button(self.frame, text="Send", font=("Arial", 16), command=self.send_request)
        self.send_button.grid(row=4, column=0,sticky="nsew", columnspan=3)
        self.logout_button.grid(row=5, column=0, columnspan=3, sticky="nsew", ipady=5)
        self.logged_in = True
        self.request_entry.delete(0, tk.END)

        self.request_entry.focus_set()

    def logged_out_gui(self):
        for widget in self.frame.winfo_children():
            widget.grid_remove()

        
        self.logout_button.grid(row=6, column=2, sticky="nsew", padx=(5, 0), ipady=5)
        self.label.grid(row=10, column=0, columnspan=3, ipady=10)
        self.login_button.grid(row=6, column=1, sticky="nsew", padx=5, ipady=5)
        self.register_button.grid(row=6, column=0, sticky="nsew", padx=(0, 5), ipady=5)
        self.username_label.grid(row=0, column=0)
        self.username_entry.grid(row=0, column=1, columnspan=2, ipady=8)
        self.pass_label.grid(row=2, column=0)
        self.password_entry.grid(row=2, column=1, columnspan=2,ipady=8)
        self.phone_label.grid(row=4, column=0)
        self.phone_entry.grid(row=4, column=1, columnspan=2, ipady=8)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        
        self.username_entry.focus_set()

    def logout(self):
        if not self.logged_in:
            messagebox.showwarning("Warning", "Not logged in.")
            self.username_entry.focus_set()
            return

        try:
            client_protocol.logout(self.client_socket, self.aes_key)
            self.logged_in = False
            messagebox.showinfo("Success", "Logout Successful")

            self.logged_out_gui()

            self.label.config(text="Welcome to the Client GUI")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        self.username_entry.focus_set()

    def send_request(self):
        if not self.logged_in:
            messagebox.showwarning("Warning", "Not logged in.")
            self.username_entry.focus_set()
            return
        try:
            request = self.request_entry.get()
            self.request_entry.delete(0, tk.END)
            if (request == ""):
                messagebox.showwarning("Warning", "Please enter a sentence to translate.")
                return
            response = client_protocol.send_req(request, self.client_socket, self.aes_key)
            print(response)
        except Exception as e:
            messagebox.showerror("Error", str(e))






if __name__ == "__main__":
    root = tk.Tk()
    app = ClientGUI(root)
    if app.connected:
        root.mainloop()
    app.client_socket.close()
=======
import os
import tkinter as tk
from tkinter import messagebox
import socket
import re
import hashlib
import multiprocessing
import threading
import time
from aes_methods import decrypt_with_rsa, encrypt_with_rsa, generate_rsa_keys
from protocol import client_protocol
from cryptography.hazmat.primitives import serialization
import sys

class ClientGUI:
    def __init__(self, root):
        self.client_private_key, self.client_public_key = generate_rsa_keys()
        self.aes_key = None
        self.root = root
        self.root.title("Client GUI")
        self.root.geometry("800x600")
        self.server_ip = "127.0.0.1"
        self.server_port = 5555
        self.client_socket = socket.socket()
        self.connected = False
        self.username = ""
        self.found = False
        self.start_time = 0
        self.logged_in = False

        self.root.withdraw() # hide root
        self.connect_to_server()
        if not self.connected:
            self.root.destroy()
            return
        self.root.deiconify() # show root after connection
        self.setup_gui()
        self.label.config(text="Please register or login.")

    def handle_key_exchange(self):
        sock = self.client_socket
        client_protocol.send_msg_plaintext(sock, "Client hello")
        serialized_server_public_key = client_protocol.get_msg_plaintext(sock)
        print("server publickey: ", serialized_server_public_key)
        server_public_key = serialization.load_pem_public_key(serialized_server_public_key)
        self.aes_key = os.urandom(32)  # AES-256
        print("aes key: ", self.aes_key)
        encrypted_aes_key = encrypt_with_rsa(server_public_key, self.aes_key)
        client_protocol.send_msg_plaintext(sock, encrypted_aes_key)
    
    def setup_gui(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=20, pady=20)

        self.username_label = tk.Label(self.frame, text="Username:", font=("Arial", 18))
        self.username_entry = tk.Entry(self.frame, font=("Arial", 18))

        self.pass_label = tk.Label(self.frame, text="Password:", font=("Arial", 18))
        
        self.password_entry = tk.Entry(self.frame,font=("Arial", 18), show="*")
        

        self.phone_label = tk.Label(self.frame, text="Phone Number:", font=("Arial", 18))
        self.phone_entry = tk.Entry(self.frame,font=("Arial", 18))
        

        self.register_button = tk.Button(self.frame, text="Register", font=("Arial", 16), command=self.register)
        

        self.login_button = tk.Button(self.frame, text="Login",font=("Arial", 16), command=self.login)
        

        self.logout_button = tk.Button(self.frame, text="Logout",font=("Arial", 16), command=self.logout)
        self.label = tk.Label(self.frame, text="Welcome to the Client GUI", font=("Arial", 22))


        self.logged_out_gui()

        


        self.request_entry = tk.Entry(self.frame, font=("Arial", 20))
        self.instruction_label =  tk.Label(self.frame, text=f"Welcome {self.username} \nenter a sentence to translate", font=("Arial", 25))
        self.translation_label = tk.Label(self.frame, text="", font=("Arial", 20))
        # Center the window on the screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        # Set focus back to the username entry after displaying messages
        self.root.focus_force()
        self.username_entry.focus_set()

    def connect_to_server(self):
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.connected = True
            self.handle_key_exchange()
            messagebox.showinfo("Connection", "Connected to server successfully.")
        except socket.error as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")

    def validate_username(self, username):
        return (4 <= len(username) <= 16 and
                re.fullmatch(r"[a-zA-Z0-9]+", username) is not None)

    def validate_password(self, password):
        return (6 <= len(password) <= 16 and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password) and
                re.fullmatch(r"[a-zA-Z0-9]+", password) is not None)

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        phone_number = self.phone_entry.get()

        if not self.validate_username(username):
            messagebox.showerror("Invalid Username", "Username must be 4-16 characters, letters, or numbers.")
            self.username_entry.focus_set()
            return

        if not self.validate_password(password):
            messagebox.showerror("Invalid Password", "Password must be 6-16 characters, include 1 uppercase and 1 digit.")
            self.password_entry.focus_set()
            return

        if len(phone_number) != 10 or not phone_number.isdigit():
            messagebox.showerror("Invalid Phone Number", "Phone number must be 10 digits.")
            self.phone_entry.focus_set()
            return

        try:
            response = client_protocol.register(self.client_socket, self.aes_key, username, password, phone_number)
            if response:
                messagebox.showinfo("Success", "Registration Successful")
                self.label.config(text="You have registered, Please click login.")
            else:
                messagebox.showerror("Failed", "Registration on server failed")
                self.label.config(text="Please retry registration.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        self.username_entry.focus_set()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Validate username/password first
        if not self.validate_username(username) or not self.validate_password(password):
            messagebox.showerror("Invalid Input", "Invalid username or password format.")
            self.username_entry.focus_set()
            return

        try:
            response = client_protocol.login(self.client_socket, self.aes_key, username, password)
            if response:
                messagebox.showinfo("Success", "Login Successful")
                self.connected = True
                self.username = username

                # Hide all widgets except the logout button and label
                self.logged_in_gui()
            else:
                messagebox.showerror("Failed", "Login Failed")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        self.username_entry.focus_set()

    def logged_in_gui (self):
        for widget in self.frame.winfo_children():        
            widget.grid_remove()

        self.label.grid_remove()
        self.instruction_label.grid(row=0, column=0, ipady=10, columnspan=3)
        self.request_entry.grid(row=3, column=0, columnspan=3, ipady=10)
        self.request_entry.focus_set
        self.send_button = tk.Button(self.frame, text="Send", font=("Arial", 16), command=self.send_request)
        self.send_button.grid(row=4, column=0,sticky="nsew", columnspan=3)
        self.logout_button.grid(row=5, column=0, columnspan=3, sticky="nsew", ipady=5)
        self.logged_in = True
        self.request_entry.delete(0, tk.END)
        self.translation_label.grid(row=6, column=0, columnspan=3, ipady=15)
        self.request_entry.focus_set()

    def logged_out_gui(self):
        for widget in self.frame.winfo_children():
            widget.grid_remove()

        
        self.logout_button.grid(row=6, column=2, sticky="nsew", padx=(5, 0), ipady=5)
        self.label.grid(row=10, column=0, columnspan=3, ipady=10)
        self.login_button.grid(row=6, column=1, sticky="nsew", padx=5, ipady=5)
        self.register_button.grid(row=6, column=0, sticky="nsew", padx=(0, 5), ipady=5)
        self.username_label.grid(row=0, column=0)
        self.username_entry.grid(row=0, column=1, columnspan=2, ipady=8)
        self.pass_label.grid(row=2, column=0)
        self.password_entry.grid(row=2, column=1, columnspan=2,ipady=8)
        self.phone_label.grid(row=4, column=0)
        self.phone_entry.grid(row=4, column=1, columnspan=2, ipady=8)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        
        self.username_entry.focus_set()

    def logout(self):
        if not self.logged_in:
            messagebox.showwarning("Warning", "Not logged in.")
            self.username_entry.focus_set()
            return

        try:
            client_protocol.logout(self.client_socket, self.aes_key)
            self.logged_in = False
            messagebox.showinfo("Success", "Logout Successful")

            self.logged_out_gui()

            self.label.config(text="Welcome to the Client GUI")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        self.username_entry.focus_set()

    def send_request(self):
        if not self.logged_in:
            messagebox.showwarning("Warning", "Not logged in.")
            self.username_entry.focus_set()
            return
        try:
            request = self.request_entry.get()
            self.request_entry.delete(0, tk.END)
            if (request == ""):
                messagebox.showwarning("Warning", "Please enter a sentence to translate.")
                return
            response = client_protocol.send_req(request, self.client_socket, self.aes_key)
            if response:
                translation = client_protocol.get_msg(self.client_socket, self.aes_key)
                print(translation)
                self.translation_label.config(text="Translation: " + translation)


        except Exception as e:
            messagebox.showerror("Error", str(e))







if __name__ == "__main__":
    root = tk.Tk()
    app = ClientGUI(root)
    if app.connected:
        root.mainloop()
    app.client_socket.close()
>>>>>>> aeab024 (An update of the translating system)
