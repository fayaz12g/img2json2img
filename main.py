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
    files = []

    if os.path.isfile(path):
        files.append(path)
    elif os.path.isdir(path):
        for file in os.listdir(path):
            if mode == "Image to JSON" and file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                files.append(os.path.join(path, file))
            elif mode == "JSON to Image" and file.lower().endswith(".json"):
                files.append(os.path.join(path, file))

    return files


# -----------------------------
# GUI
# -----------------------------

class ConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Image ⇄ JSON Converter")
        self.geometry("600x450")

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

        self.input_entry = ctk.CTkEntry(frame, placeholder_text="Input file or folder")
        self.input_entry.pack(fill="x", pady=10)

        ctk.CTkButton(frame, text="Browse Input", command=self.select_input).pack()

        self.output_entry = ctk.CTkEntry(frame, placeholder_text="Output folder")
        self.output_entry.pack(fill="x", pady=10)

        ctk.CTkButton(frame, text="Browse Output", command=self.select_output).pack()

        self.progress = ctk.CTkProgressBar(frame)
        self.progress.pack(fill="x", pady=15)
        self.progress.set(0)

        self.status_box = ctk.CTkTextbox(frame, height=100)
        self.status_box.pack(fill="both", expand=True, pady=10)

        ctk.CTkButton(frame, text="Run Conversion",
                      command=self.start_conversion).pack(pady=10)

    def select_input(self):
        path = filedialog.askopenfilename() or filedialog.askdirectory()
        if path:
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, path)

    def select_output(self):
        path = filedialog.askdirectory()
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

        for i, file in enumerate(files):
            filename = os.path.splitext(os.path.basename(file))[0]

            if self.mode_var.get() == "Image to JSON":
                out = os.path.join(output_dir, filename + ".json")
                success, msg = image_to_json(file, out, self.resize_var.get())
            else:
                out = os.path.join(output_dir, filename + ".png")
                success, msg = json_to_image(file, out)

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

    for file in files:
        filename = os.path.splitext(os.path.basename(file))[0]

        if mode == "img2json":
            out = os.path.join(output_dir, filename + ".json")
            success, msg = image_to_json(file, out, resize)
        else:
            out = os.path.join(output_dir, filename + ".png")
            success, msg = json_to_image(file, out)

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
