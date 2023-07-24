#!/usr/bin/env python3
import shutil
import tkinter as tk
from PIL import Image, ImageTk

from sneparse import RESOURCES

# Choose the source folder
SOURCE_FOLDER = RESOURCES.joinpath("images", "categorized")

# Function to move the image to a category folder
def categorize_image(category: str):
    image_path = image_paths[image_index]
    target_folder = RESOURCES.joinpath("images", "categorized", category)
    shutil.move(image_path, target_folder)
    image_paths[image_index] = target_folder.joinpath(image_path.name)
    next_image()

# Function to display the image
def display_image(image_path):
    with Image.open(image_path) as image:
        photo = ImageTk.PhotoImage(image)
        image_label.config(image=photo)
        image_label.image = photo

def update_hotkeys(i: int):
    for (category, hotkey) in hotkey_labels.items():
        if (category == image_paths[i].parent.name):
            hotkey.configure(background="yellow", foreground="black")
        else:
            hotkey.configure(background="black", foreground="white")

def prev_image():
    global image_index
    image_index = max(image_index - 1, 0)
    display_image(image_paths[image_index])
    update_hotkeys(image_index)

def next_image():
    global image_index
    image_index = min(image_index + 1, len(image_paths) - 1)
    display_image(image_paths[image_index])
    update_hotkeys(image_index)

if __name__ == "__main__":
    # Set up the GUI
    root = tk.Tk()
    root.title("Image Categorization")

    categories = {
        "1": "agn",
        "2": "bad",
        "3": "bizarre_radio",
        "4": "galactic",
        "5": "good",
        "6": "low_dec",
        "7": "nuclear",
        "8": "unclear",
        "9": "weak_radio",
        "0": "unsorted"
    }

    for category in categories.values():
        RESOURCES.joinpath("images", "categorized", category).mkdir(exist_ok=True)

    # Get the list of image paths in the source folder
    image_paths = list(SOURCE_FOLDER.glob("**/*.png"))
    image_index = 0

    # Create and display the image label
    image_label = tk.Label(root)
    image_label.pack()

    # Frame to hold hotkey labels
    hotkey_frame = tk.Frame(root)
    hotkey_frame.pack()

    # Create hotkey labels
    hotkey_labels = {}
    for hotkey, category in categories.items():
        T = tk.Text(hotkey_frame, height=1, width=20)
        T.pack(side=tk.LEFT, padx=5)
        T.insert(tk.END, f"{hotkey}: {category}")
        hotkey_labels[category] = T

    for (category, hotkey) in hotkey_labels.items():
        if (category == image_paths[image_index].parent.name):
            hotkey.configure(background="yellow", foreground="black")
        else:
            hotkey.configure(background="black", foreground="white")

    for (hotkey, category) in categories.items():
        root.bind(hotkey, lambda _, category=category: categorize_image(category))

    root.bind("<Left>", lambda _: prev_image())
    root.bind("<Right>", lambda _: next_image())

    # Start the categorization process by displaying the first image
    if image_paths:
        display_image(image_paths[image_index])
        root.mainloop()
    else:
        print("No images found in the source folder.")
