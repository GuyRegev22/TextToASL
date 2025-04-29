import os
import tkinter as tk
from tkinter import messagebox, Frame
import socket
import re
import time
from aes_methods import decrypt_with_rsa, encrypt_with_rsa, generate_rsa_keys
from protocol import client_protocol
from cryptography.hazmat.primitives import serialization
from PIL import Image, ImageTk
import os
from threading import Thread 
import threading
import cv2  # Import OpenCV for video handling
from video_player import VideoPlayer  # Import the VideoPlayer class
from asl_translator import ASLTranslator


# Constants for colors and styling
BACKGROUND_COLOR = "#F0F2F5"
PRIMARY_COLOR = "#4267B2"  # Facebook blue
SECONDARY_COLOR = "#E5E5E5"
TEXT_COLOR = "#1D1D1D"
INPUT_BG_COLOR = "#FFFFFF"
FONT_FAMILY = "Arial"


class ClientGUI:
    def __init__(self, root):
        self.client_private_key, self.client_public_key = generate_rsa_keys()
        self.aes_key = None
        self.root = root
        self.main_frame = Frame(root)
        self.main_frame.pack()

        self.root.title("Login Application")
        self.root.geometry("600x750")
        self.root.configure(bg=BACKGROUND_COLOR)
        self.root.resizable(False, False)
        # self.root = root
        # self.root.title("Client GUI")
        # self.root.geometry("800x600")
        self.center_window()
        self.login_frame = None
        self.main_frame = None
        self.bottom_frame = None
        self.entry_frame = None
        self.video_frame = None
        self.server_ip = "127.0.0.1"
        self.server_port = 5555
        self.client_socket = socket.socket()
        self.connected = False
        self.username = ""
        self.found = False
        self.start_time = 0
        self.logged_in = False
        self.video_name = "welcome"
        self.video_label_text = None
        self.video_player = None
        self.finished = False
        self.clicked_ok = False
        self.asl_vocabulary = ASLTranslator().load_asl_vocabulary("asl_dict.txt")
        # Ignore modifier keys
        for mod in ["<Alt_L>", "<Alt_R>", "<Control_L>", "<Control_R>", "<Shift_L>", "<Shift_R>"]:
            self.root.bind_all(mod, lambda e: "break")

        # Optional: dummy menu to avoid Alt focusing
        self.root.config(menu=tk.Menu(self.root))


        self.root.withdraw() # hide root
        self.connect_to_server()
        if not self.connected:
            self.root.destroy()
            return
        self.root.deiconify() # show root after connection
        self.show_login_page()


    def center_window(self):
        """Center the window on the screen"""
        window_width = 600
        window_height = 750
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

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
    
    def show_login_page(self):
        """Display the login page"""
        # Clear any existing frames
        self.clear_frames()
        
        # Create login frame
        self.login_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=500, height=600)
        
        # Create header
        header_label = tk.Label(
            self.login_frame,
            text="Welcome",
            font=(FONT_FAMILY, 24, "bold"),
            bg=BACKGROUND_COLOR,
            fg=PRIMARY_COLOR
        )
        header_label.pack(pady=(20, 30))
        
        # Create form container
        form_frame = tk.Frame(self.login_frame, bg=BACKGROUND_COLOR)
        form_frame.pack(fill=tk.BOTH, padx=20, pady=10)
        
        # Username entry
        username_frame = tk.Frame(form_frame, bg=BACKGROUND_COLOR)
        username_frame.pack(fill=tk.X, pady=10)
        
        username_label = tk.Label(
            username_frame,
            text="Username",
            font=(FONT_FAMILY, 10),
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR,
            anchor="w"
        )
        username_label.pack(fill=tk.X)
        
        self.username_entry = tk.Entry(
            username_frame,
            font=(FONT_FAMILY, 12),
            bg=INPUT_BG_COLOR,
            relief=tk.SOLID,
            bd=1
        )
        self.username_entry.pack(fill=tk.X, pady=(5, 0), ipady=8)

        # Password entry
        password_frame = tk.Frame(form_frame, bg=BACKGROUND_COLOR)
        password_frame.pack(fill=tk.X, pady=10)
        
        password_label = tk.Label(
            password_frame,
            text="Password",
            font=(FONT_FAMILY, 10),
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR,
            anchor="w"
        )
        password_label.pack(fill=tk.X)
        
        self.password_entry = tk.Entry(
            password_frame,
            font=(FONT_FAMILY, 12),
            bg=INPUT_BG_COLOR,
            relief=tk.SOLID,
            bd=1,
            show="•"
        )
        self.password_entry.pack(fill=tk.X, pady=(5, 0), ipady=8)
        
        # Button container
        button_frame = tk.Frame(form_frame, bg=BACKGROUND_COLOR)
        button_frame.pack(fill=tk.X, pady=(20, 10))
        
        # Login button
        login_button = tk.Button(
            button_frame,
            text="Login",
            font=(FONT_FAMILY, 12, "bold"),
            bg=PRIMARY_COLOR,
            fg="white",
            relief=tk.FLAT,
            activebackground="#3B5998",
            activeforeground="white",
            command=self.login
        )
        login_button.pack(fill=tk.X, ipady=8, side=tk.TOP, pady=(0, 10))
        
        # Register button
        register_button = tk.Button(
            button_frame,
            text="Register",
            font=(FONT_FAMILY, 12, "bold"),
            bg=SECONDARY_COLOR,
            fg=TEXT_COLOR,
            relief=tk.FLAT,
            activebackground="#CCCCCC",
            activeforeground=TEXT_COLOR,
            command=self.register
        )
        register_button.pack(fill=tk.X, ipady=8, pady=(0, 10))
        
        # Create a bottom frame for buttons
        self.bottom_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        #bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=10)
        # Exit button on login page - now with a fixed bright color to make it visible
        exit_button = tk.Button(
            self.bottom_frame,
            text="Exit Application",  # Changed text to be more visible
            font=(FONT_FAMILY, 12, "bold"),
            bg="#f44336",  # Red color
            fg="white",
            relief=tk.RAISED,  # Changed to RAISED to stand out
            borderwidth=2,     # Add border
            activebackground="#d32f2f",
            activeforeground="white",
            command=self.exit  # This will close the application
        )
        exit_button.pack(fill=tk.X, ipady=8, pady=(10, 0))

        self.username_entry.focus_set()  # Set focus to username entry
        # Bind Enter key to login
        self.root.bind("<Return>", lambda event: self.login())
        # Bind Escape key to exit
        self.root.bind("<Escape>", lambda event: self.exit())
        # Bind Tab key to password entry
        self.username_entry.bind("<Tab>", lambda event: self.password_entry.focus_set())

    def exit(self):
        self.root.destroy()
        self.root.quit()
        # Close the socket connection
        self.client_socket.close()

    def show_main_page(self, username):
        """Display the main page after login"""
        # Clear any existing frames
        self.clear_frames()
        
        # Create main frame
        self.main_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        self.main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=500, height=600)
        
        # Welcome header
        header_label = tk.Label(
            self.main_frame,
            text=f"Hello, {username}!",
            font=(FONT_FAMILY, 18, "bold"),
            bg=BACKGROUND_COLOR,
            fg=PRIMARY_COLOR
        )
        header_label.pack(pady=(20, 30))
        
        # Text entry frame
        self.entry_frame = tk.Frame(self.main_frame, bg=BACKGROUND_COLOR)
        self.entry_frame.pack(fill=tk.X, padx=20)
        
        entry_label = tk.Label(
            self.entry_frame,
            text="Enter a sentence to translate:",
            font=(FONT_FAMILY, 10),
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR,
            anchor="w"
        )
        entry_label.pack(fill=tk.X, pady=(0, 5))
        
        self.sentence_entry = tk.Entry(
            self.entry_frame,
            font=(FONT_FAMILY, 12),
            bg=INPUT_BG_COLOR,
            relief=tk.SOLID,
            bd=1
        )
        self.sentence_entry.pack(fill=tk.X, ipady=8)
        
        # Submit button
        submit_button = tk.Button(
            self.entry_frame,
            text="Submit",
            font=(FONT_FAMILY, 12),
            bg=PRIMARY_COLOR,
            fg="white",
            relief=tk.FLAT,
            activebackground="#3B5998",
            activeforeground="white",
            command=self.submit_sentence
        )
        submit_button.pack(fill=tk.X, ipady=5, pady=(10, 20))
        
        # Video frame
        self.video_frame = tk.Frame(self.main_frame,height=200,width=200, bg=BACKGROUND_COLOR)
        self.video_frame.pack(fill=tk.X, padx=20, pady=10)

        self.root.bind("<Return>", lambda event: submit_button.invoke())
        # Bind Escape key to exit
        self.root.bind("<Escape>", lambda event: self.exit())

        
        #Create a label for the video name
        self.video_label_text = tk.Label(
            self.video_frame,
            text=f"Video: {self.video_name}",
            font=(FONT_FAMILY, 18, "bold"),
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR,
            anchor="center",   # Center text horizontally
            justify="center"
        )
        self.video_label_text.pack(pady=(5, 5))


        self.video_player = VideoPlayer(self.video_frame, r"videos/sample.mp4")
        video_thread = Thread(target=self.video_player.play_video_loop, daemon=True)
        video_thread.start()
        
        # Create a bottom frame for buttons
        self.bottom_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        #bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        self.bottom_frame.pack( side='bottom',fill=tk.X, padx=20, pady=10)
        
        
        # Exit button at the bottom - with the same style as login page
        exit_button = tk.Button(
            self.bottom_frame,
            text="Exit Application",  # Changed text to be more visible
            font=(FONT_FAMILY, 12, "bold"),
            bg="#f44336",  # Red color
            fg="white",
            relief=tk.RAISED,  # Changed to RAISED to stand out
            borderwidth=2,     # Add border
            activebackground="#d32f2f",
            activeforeground="white",
            command=self.exit  # This will close the application
        )
        exit_button.pack(fill=tk.X, ipady=8)


    def show_loading_page (self):
        
        # Clear any existing frames
        self.finished = False
        self.clear_frames()

        self.main_frame = tk.Frame(self.root, bg="#ffffff")
        self.main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=600, height=750)
        self.video_player = None
        self.video_player = VideoPlayer(self.main_frame, r"videos/loading.mp4")

        self.finished = True



        
    def show_videos_page(self, sentence_translation):
        """Display the videos page"""
        while not self.finished:
            time.sleep(0.1)
        self.finished = False
        # Clear any existing frames
        self.clear_frames()
        # Hide the loading page
        # if self.video_player:
        #     self.video_player.video_label.destroy()
        #     self.video_player.cap.release()
        #     self.video_player = None

        # Create main frame
        self.main_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        self.main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=500, height=600)
        # Welcome header
        header_label = tk.Label(
            self.main_frame,
            text=f"Sentence Translation: \n {sentence_translation}",
            font=(FONT_FAMILY, 20, "bold"),
            bg=BACKGROUND_COLOR,
            fg=PRIMARY_COLOR
        )
        header_label.pack(pady=(20, 30))

        # Video frame
        self.video_frame = tk.Frame(self.main_frame,height=600,width=450, bg=BACKGROUND_COLOR)
        self.video_frame.pack(fill=tk.X, padx=20, pady=10)

        #To-do: Add the video player here 
                # Clear previous video frame (if any)
        for widget in self.video_frame.winfo_children():
            widget.destroy()

        # Add a canvas + scrollbar for scrollable content
        self.canvas = tk.Canvas(self.video_frame, bg=BACKGROUND_COLOR, highlightthickness=0, height=550, width=450)
        scrollbar = tk.Scrollbar(self.video_frame, orient="vertical",width=30, command=self.canvas.yview)
        scrollable_frame = tk.Frame(self.canvas, bg=BACKGROUND_COLOR)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Store VideoPlayer instances to keep them alive
        self.video_players = []

        for word in sentence_translation.split(" "):
            # Word label
            word_label = tk.Label(
                scrollable_frame,
                text=word,
                font=(FONT_FAMILY, 16, "bold"),
                bg=BACKGROUND_COLOR,
                fg=PRIMARY_COLOR
            )
            word_label.pack(anchor="w", padx=10, pady=(10, 2))

            # Container frame for each video to make sure it's sized well
            word_video_frame = tk.Frame(scrollable_frame, bg="#000000", height=300, width=400)
            word_video_frame.pack(padx=10, fill="x")
            word_video_frame.pack_propagate(False)  # Prevent shrinking

            # Try to load the video
            video_path = f"videos/{word.lower()}.mp4"
            if os.path.exists(video_path):
                player = VideoPlayer(word_video_frame, video_path)
                self.video_players.append(player)
                Thread(target=player.play_video_loop, daemon=True).start()
            else:
                # Show placeholder if video is missing
                placeholder = tk.Label(word_video_frame, text="Video not found", bg="#555", fg="white")
                placeholder.pack(expand=True, fill="both")

            # Separator line
            separator = tk.Frame(scrollable_frame, height=3, bg=INPUT_BG_COLOR)
            separator.pack(fill="x", padx=10, pady=5)

            # Bind mouse wheel scrolling to the canvas
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
    # Adjust the scroll region of the canvas to the size of the scrollable frame
        scrollable_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # Create a bottom frame for buttons
        self.bottom_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR)
        #bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        self.bottom_frame.pack(side='bottom',fill=tk.X, padx=20, pady=10)
        # Exit button at the bottom - with the same style as login page
        back_button = tk.Button(
            self.bottom_frame,
            text="Back to Main",  # Changed text to be more visible
            font=(FONT_FAMILY, 14, "bold"),
            bg=PRIMARY_COLOR,  # Red color
            fg="white",
            relief=tk.RAISED,  # Changed to RAISED to stand out
            borderwidth=2,     # Add border
            activebackground="#d32f2f",
            activeforeground="white",
            command=lambda: self.show_main_page(self.username)  # This will close the application
        )
        back_button.pack(fill=tk.X, ipady=8)
        # Exit button at the bottom - with the same style as login page
        exit_button = tk.Button(
            self.bottom_frame,
            text="Exit Application",  # Changed text to be more visible
            font=(FONT_FAMILY, 14, "bold"),
            bg="#f44336",  # Red color
            fg="white",
            relief=tk.RAISED,  # Changed to RAISED to stand out
            borderwidth=2,     # Add border
            activebackground="#d32f2f",
            activeforeground="white",
            command=self.exit  # This will close the application
        )
        exit_button.pack(fill=tk.X, ipady=10)
        
    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
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

        if not self.validate_username(username):
            messagebox.showerror("Invalid Username", "Username must be 4-16 characters, letters, or numbers.")
            self.username_entry.focus_set()
            return

        if not self.validate_password(password):
            messagebox.showerror("Invalid Password", "Password must be 6-16 characters, include 1 uppercase and 1 digit.")
            self.password_entry.focus_set()
            return


        try:
            response = client_protocol.register(self.client_socket, self.aes_key, username, password)
            print(response)
            if response:
                messagebox.showinfo("Success", "Registration Successful")
                response = client_protocol.login(self.client_socket, self.aes_key, username, password)
                if response:
                    self.connected = True
                    self.username = username

                    # Hide all widgets except the logout button and label
                    self.show_main_page(self.username)
                
            else:
                messagebox.showerror("Failed", "Registration on server failed. please try again!")
                # Clear fields
                self.username_entry.delete(0, tk.END)
                self.password_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", str(e))

        

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
                self.show_main_page(self.username)
            else:
                messagebox.showerror("Failed", "Login Failed")
        except Exception as e:
            messagebox.showerror("Error", str(e))



    def logout(self):
        if not self.logged_in:
            messagebox.showwarning("Warning", "Not logged in.")
            self.username_entry.focus_set()
            return

        try:
            client_protocol.logout(self.client_socket, self.aes_key)
            self.logged_in = False
            messagebox.showinfo("Success", "Logout Successful")

            self.show_login_page()
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def submit_sentence(self):

        try:
            sentence = self.sentence_entry.get().strip()
            # Clear the entry
            
            if not sentence:
                messagebox.showwarning("Warning", "Please enter a sentence")
                self.sentence_entry.delete(0, tk.END)
                return
            elif len(sentence.split(" ")) > 12:
                messagebox.showwarning("Warning", "Sentence can only contain up to 12 words")
                return
            self.sentence_entry.delete(0, tk.END)
            response = client_protocol.send_req(sentence, self.client_socket, self.aes_key)
            print(response)
            if response:
                messagebox.showinfo("Submitted", f"You submitted: {sentence}")
                
            self.wait_for_sentence()

                

                


        except Exception as e:
            messagebox.showerror("Error", str(e))

    def wait_for_sentence(self):
        self.sentence_translation = None
        """Show loading page and start background task"""
        self.show_loading_page()
        print("here")
        #time.sleep(1000)
        # Start the long task in a new thread
        threading.Thread(target=self.calculate_sentence, daemon=True).start()
        
        
        # Start checking if task is done
        self.check_translation_complete()

    def calculate_sentence(self):
        """The heavy work function"""
        
        translation = client_protocol.get_msg(self.client_socket, self.aes_key)
        print(translation)
        
        self.sentence_translation = translation

    def check_translation_complete(self):
        """Check if the task finished"""
        if self.sentence_translation is not None:
            # Task finished
            check = self.check_translation_syntax(self.sentence_translation)
            if not check:
                messagebox.showerror("Error", "something went wrong with the translation")
                self.sentence_translation = None
                messagebox.showinfo("info", "Redirecting to main page")
                self.show_main_page(self.username)
                return

            print("Translation complete:", self.sentence_translation)

            self.show_videos_page(self.sentence_translation)
            
        else:
            # Still not ready - check again after 100ms
            print("Waiting for translation...")
            self.root.after(100, self.check_translation_complete)

    def check_translation_syntax(self, sentence=""):
        if not sentence:
            return False

        # Step 1: Remove text inside parentheses and quotes
        sentence = re.sub(r"\(.*?\)", " ", sentence)
        sentence = re.sub(r"\".*?\"", " ", sentence)

        # Step 2: Remove any non-letters and non-spaces
        sentence = re.sub(r"[^a-zA-Z\s]", " ", sentence)

        # Step 3: Normalize spaces
        sentence = sentence.strip()
        words = sentence.split()
        
        if not words:
            return False

        # Step 4: Process words
        processed_words = []
        for word in words:
            clean_word = word.lower()  # Work with lowercase for vocabulary checking
            if clean_word in self.asl_vocabulary:
                processed_words.append(word.lower())
            else:
                # Spell out the word letter-by-letter
                spelled = ' '.join(list(clean_word))
                processed_words.append(spelled)

        self.sentence_translation = ' '.join(processed_words)
        return True
        
        
    
    def clear_frames(self):
        try:
            for frame in (self.login_frame, self.main_frame, self.bottom_frame, self.video_frame, self.entry_frame):
                if frame: #and frame.winfo_exists():
                    
                    frame.destroy()
        
        except Exception as e:
            print(f"Couldn't destroy {frame}: {e}")

        for frame in (self.login_frame, self.main_frame, self.bottom_frame, self.video_frame, self.entry_frame):
            frame = None
        # Clear the video player if it exists   
        if self.video_player:
            #self.video_player.stop()
            self.video_player.video_label.destroy()
            
            self.video_player = None

    def update_video_name(self, new_name):
        """Update the GIF name displayed above the GIF
        
        Args:
            new_name (str): The new name to display for the GIF
        """
        self.video_name = new_name
        if self.video_label_text:
            self.video_label_text.config(text=f"Video: {self.video_name}")





if __name__ == "__main__":
    root = tk.Tk()
    app = ClientGUI(root)
    if app.connected:
        root.mainloop()
    app.client_socket.close()
