#!/usr/bin/env python3
import shutil
import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path
import argparse

# Function to move the image to a category folder
def categorize_image(category: str) -> None:
    image_path = image_paths[image_index]
    target_folder = categories_dir.joinpath(category)
    shutil.move(image_path, target_folder)
    image_paths[image_index] = target_folder.joinpath(image_path.name)
    next_image()

# Function to display the image
def display_image(image_path: Path) -> None:
    with Image.open(image_path) as image:
        new_height = 800
        new_width  = new_height * image.width // image.height

        photo = ImageTk.PhotoImage(image.resize((new_width, new_height)))
        image_label.config(image=photo)
        image_label.image = photo
    update_hotkeys(image_index)
    update_progress(image_index + 1, len(image_paths))

def update_hotkeys(i: int) -> None:
    for (category, hotkey) in hotkey_labels.items():
        if (category == image_paths[i].parent.name):
            hotkey.configure(background="yellow", foreground="black")
        else:
            hotkey.configure(background="black", foreground="white")

def update_progress(i: int, total: int) -> None:
    progress.delete("1.0", tk.END)
    progress.insert(tk.END, f"[{i}/{total}]")

def prev_image() -> None:
    global image_index
    image_index = max(image_index - 1, 0)
    display_image(image_paths[image_index])

def next_image() -> None:
    global image_index
    image_index = min(image_index + 1, len(image_paths) - 1)
    display_image(image_paths[image_index])

def search_and_display(name: str) -> bool:
    global image_index

    # Yes, yes, this is an unnecessarily slow O(n) loop.
    for (i, path) in enumerate(image_paths):
        if path.stem == name:
            image_index = i
            display_image(path)
            return True

    return False

def next_category() -> None:
    global image_index

    current_category = image_paths[image_index].parent.name

    for (i, path) in list(enumerate(image_paths))[image_index + 1:]:
        if path.parent.name != current_category:
            image_index = i
            display_image(path)
            return

def prev_category() -> None:
    global image_index

    current_category = image_paths[image_index].parent.name

    for (i, path) in reversed(list(enumerate(image_paths))[:image_index]):
        if path.parent.name != current_category:
            image_index = i
            display_image(path)
            return

def onKeyRelease(event: tk.Event) -> None:
    global typing_command

    if not typing_command:
        if event.keysym == "Left" or event.keysym == "h":
            prev_image()
        elif event.keysym == "Right" or event.keysym == "l":
            next_image()
        elif event.char in categories.keys():
            categorize_image(categories[event.char])
        elif event.char == "/":
            typing_command = True
            command_text.replace("1.0", tk.END, "search:")
            text_input.delete("1.0", tk.END)
            text_input.configure(foreground="white")
            text_input.focus()
        elif event.char == "n":
            next_category()
        elif event.char == "N":
            prev_category()
    else:
        if event.keysym == "Escape":
            text_input.delete("1.0", tk.END)
            command_text.delete("1.0", tk.END)
            root.focus()
            typing_command = False
        elif event.keysym == "Return":
            name = text_input.get("1.0", tk.END).strip()
            found = search_and_display(name)
            text_input.delete("1.0", tk.END)
            command_text.delete("1.0", tk.END)
            if not found:
                text_input.insert(tk.END, f"No image found for \"{name}\".")
                text_input.configure(foreground="red")
            root.focus()
            typing_command = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "categories",
        type=Path,
        help="Path to the categories directory",
    )

    args = parser.parse_args()
    categories_dir = args.categories

    # Set up the GUI
    root = tk.Tk()
    root.title(f"Image Sorter - {categories_dir}")

    hotkeys = "1234567890qwertyuiop"

    categories: dict[str, str] = {}
    for (i, name) in enumerate(d.name for d in categories_dir.iterdir() if d.is_dir()):
        if i >= len(hotkeys):
            raise Exception("Too many categories")
        categories[hotkeys[i]] = name

    categories_inverse = {v: k for k, v in categories.items()}

    # Get the list of image paths in the source folder
    image_paths = list(
        sorted(
            categories_dir.glob("**/*.png"),
            key=lambda path: hotkeys.index(categories_inverse[path.parent.name])
        )
    )

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
        T.grid(row=(len(hotkey_labels) // 10), column=(len(hotkey_labels) % 10), padx=5, pady=2)

        T.insert(tk.END, f"{hotkey}: {category}")
        hotkey_labels[category] = T

    # Frame to hold command box
    command_frame = tk.Frame(root)
    command_frame.pack(fill="x")

    command_text = tk.Text(command_frame, height=1, width=10)
    command_text.configure(background="black", foreground="white")
    command_text.pack(side=tk.LEFT, padx=5)

    text_input = tk.Text(command_frame, height=1)
    text_input.configure(background="black", foreground="white")
    text_input.pack(side=tk.LEFT, padx=5, fill="x")

    progress = tk.Text(command_frame, height=1, width=10)
    progress.configure(background="black", foreground="white")
    progress.pack(side=tk.RIGHT)

    typing_command = False

    root.bind("<KeyRelease>", onKeyRelease)

    # Start the categorization process by displaying the first image
    if image_paths:
        display_image(image_paths[image_index])
        root.mainloop()
    else:
        print("No images found in the source folder.")
