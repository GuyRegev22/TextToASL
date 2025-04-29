

import tkinter as tk
import cv2
from PIL import Image, ImageTk

class VideoPlayer:
    def __init__(self, parent_frame, video_path):
        self.parent_frame = parent_frame
        self.video_path = video_path

        # Create a Label inside the given frame to show video frames
        self.video_label = tk.Label(self.parent_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Open the video
        self.cap = cv2.VideoCapture(self.video_path)

        self.play_video_loop()

    def play_video_loop(self):
        ret, frame = self.cap.read()
        if ret:
            self.parent_frame.update_idletasks()  # Make sure geometry is up to date
            desired_width = self.parent_frame.winfo_width()
            desired_height = self.parent_frame.winfo_height()

            # Resize the frame
            frame = cv2.resize(frame, (desired_width, desired_height))

            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            # Call again after 30ms
            self.video_label.after(60, self.play_video_loop)
        else:
            # Loop the video
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.play_video_loop()
