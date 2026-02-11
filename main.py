import os
import sys
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox

# -----------------------------
# Core Conversion Logic
# -----------------------------

def image_to_json(input_path, output_path, resize_option=None):
    try:
        img = Image.open(input_path).convert("RGBA")

        if resize_option and resize_option != "Original":
            size = int(resize_option)
            img = img.resize((size, size), Image.Resampling.NEAREST)

        width, height = img.size
        pixels = list(img.getdata())

        data = {
            "width": width,
            "height": height,
            "pixels": [f"#{r:02x}{g:02x}{b:02x}{a:02x}" for (r, g, b, a) in pixels]
        }

        with open(output_path, "w") as f:
            json.dump(data, f)

        return True, f"Converted {os.path.basename(input_path)}"
    except Exception as e:
        return False, str(e)


def json_to_image(input_path, output_path):
    try:
        with open(input_path, "r") as f:
            data = json.load(f)

        width = data["width"]
        height = data["height"]
        pixel_data = data["pixels"]

        img = Image.new("RGBA", (width, height))

        pixels = []
        for hex_code in pixel_data:
            hex_code = hex_code.lstrip("#")
            r = int(hex_code[0:2], 16)
            g = int(hex_code[2:4], 16)
            b = int(hex_code[4:6], 16)
            a = int(hex_code[6:8], 16)
            pixels.append((r, g, b, a))

        img.putdata(pixels)
        img.save(output_path)

        return True, f"Reconstructed {os.path.basename(input_path)}"
    except Exception as e:
        return False, str(e)


# -----------------------------
# Batch Processing
# -----------------------------

def collect_files(path, mode):
    """
    Returns list of tuples: (absolute_path, relative_path)
    relative_path is None for single files, or path relative to input dir for directories
    """
    files = []

    if os.path.isfile(path):
        # Single file: no relative path needed
        files.append((path, None))
    elif os.path.isdir(path):
        # Directory: recursively walk and preserve structure
        for root, dirs, filenames in os.walk(path):
            for file in filenames:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, path)
                
                if mode == "Image to JSON" and file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    files.append((abs_path, rel_path))
                elif mode == "JSON to Image" and file.lower().endswith(".json"):
                    files.append((abs_path, rel_path))

    return files


# -----------------------------
# GUI
# -----------------------------

class ConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("green")

        self.title("Image ⇄ JSON Converter")
        self.geometry("600x900")

        self.executor = ThreadPoolExecutor(max_workers=4)

        self.mode_var = ctk.StringVar(value="Image to JSON")
        self.resize_var = ctk.StringVar(value="Original")

        self.build_ui()

    def build_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Conversion Mode").pack(pady=5)
        ctk.CTkOptionMenu(frame, variable=self.mode_var,
                          values=["Image to JSON", "JSON to Image"]).pack()

        ctk.CTkLabel(frame, text="Resize (Image → JSON only)").pack(pady=10)
        ctk.CTkOptionMenu(frame, variable=self.resize_var,
                          values=["Original", "16", "32", "64", "128"]).pack()

        # Input selection with separate file/folder buttons
        ctk.CTkLabel(frame, text="Input").pack(pady=(15, 5))
        self.input_entry = ctk.CTkEntry(frame, placeholder_text="Input file or folder")
        self.input_entry.pack(fill="x", pady=5)

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(pady=5)
        
        ctk.CTkButton(button_frame, text="Select File", 
                      command=self.select_file, width=140).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Select Folder", 
                      command=self.select_folder, width=140).pack(side="left", padx=5)

        # Output selection
        ctk.CTkLabel(frame, text="Output").pack(pady=(15, 5))
        self.output_entry = ctk.CTkEntry(frame, placeholder_text="Output folder")
        self.output_entry.pack(fill="x", pady=5)

        ctk.CTkButton(frame, text="Browse Output Folder", 
                      command=self.select_output).pack(pady=5)

        self.progress = ctk.CTkProgressBar(frame)
        self.progress.pack(fill="x", pady=15)
        self.progress.set(0)

        self.status_box = ctk.CTkTextbox(frame, height=100)
        self.status_box.pack(fill="both", expand=True, pady=10)

        ctk.CTkButton(frame, text="Run Conversion",
                      command=self.start_conversion, height=40).pack(pady=10)

    def select_file(self):
        """Select a single file"""
        path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[
                ("All supported", "*.png *.jpg *.jpeg *.bmp *.json"),
                ("Image files", "*.png *.jpg *.jpeg *.bmp"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        if path:
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, path)

    def select_folder(self):
        """Select a folder"""
        path = filedialog.askdirectory(title="Select a folder")
        if path:
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, path)

    def select_output(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, path)

    def log(self, message):
        self.status_box.insert("end", message + "\n")
        self.status_box.see("end")

    def start_conversion(self):
        input_path = self.input_entry.get()
        output_dir = self.output_entry.get()

        if not input_path or not output_dir:
            messagebox.showerror("Error", "Select input and output paths.")
            return

        files = collect_files(input_path, self.mode_var.get())
        if not files:
            messagebox.showerror("Error", "No valid files found.")
            return

        os.makedirs(output_dir, exist_ok=True)
        self.progress.set(0)
        self.status_box.delete("1.0", "end")

        threading.Thread(target=self.process_files,
                         args=(files, output_dir),
                         daemon=True).start()

    def process_files(self, files, output_dir):
        total = len(files)

        for i, (file_path, rel_path) in enumerate(files):
            # Determine output path while preserving folder structure
            if rel_path:
                # Directory input: preserve structure
                output_path = os.path.join(output_dir, rel_path)
                output_path = os.path.splitext(output_path)[0]
            else:
                # Single file input: save directly to output dir
                filename = os.path.splitext(os.path.basename(file_path))[0]
                output_path = os.path.join(output_dir, filename)

            # Add appropriate extension
            if self.mode_var.get() == "Image to JSON":
                output_path += ".json"
            else:
                output_path += ".png"

            # Create subdirectories if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Process the file
            if self.mode_var.get() == "Image to JSON":
                success, msg = image_to_json(file_path, output_path, self.resize_var.get())
            else:
                success, msg = json_to_image(file_path, output_path)

            self.after(0, self.log, msg)
            self.after(0, self.progress.set, (i + 1) / total)

        self.after(0, lambda: messagebox.showinfo("Done", "Conversion complete!"))


# -----------------------------
# CLI Mode
# -----------------------------

def run_cli():
    if len(sys.argv) < 4:
        print("Usage:")
        print("Image → JSON: python main.py img2json input output_folder [size]")
        print("JSON → Image: python main.py json2img input output_folder")
        return

    mode = sys.argv[1]
    input_path = sys.argv[2]
    output_dir = sys.argv[3]
    resize = sys.argv[4] if len(sys.argv) > 4 else "Original"

    files = collect_files(input_path,
                          "Image to JSON" if mode == "img2json" else "JSON to Image")

    os.makedirs(output_dir, exist_ok=True)

    for file_path, rel_path in files:
        # Determine output path while preserving folder structure
        if rel_path:
            output_path = os.path.join(output_dir, rel_path)
            output_path = os.path.splitext(output_path)[0]
        else:
            filename = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(output_dir, filename)

        # Add appropriate extension
        if mode == "img2json":
            output_path += ".json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            success, msg = image_to_json(file_path, output_path, resize)
        else:
            output_path += ".png"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            success, msg = json_to_image(file_path, output_path)

        print(msg)


# -----------------------------
# Entry Point
# -----------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli()
    else:
        app = ConverterApp()
        app.mainloop()