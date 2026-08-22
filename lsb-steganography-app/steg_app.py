#!/usr/bin/env python3
"""
Simple LSB steganography GUI (Tkinter)

Encode a text message into a PNG image, or decode a hidden message back.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, StringVar, IntVar

from PIL import Image, ImageTk

# ----------------------------------------------------------------------
# Helper functions – LSB operations
# ----------------------------------------------------------------------
def rgb_to_bytes(r, g, b):
    """Pack three 8‑bit channels into a single 24‑bit integer."""
    return (r << 16) | (g << 8) | b

def int_to_rgb(value):
    """Unpack a 24‑bit integer back to (R, G, B)."""
    return ((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)

def extract_bits_from_image(image):
    """Yield LSBs from each channel of each pixel (row‑major order)."""
    for pixel in image.getdata():
        if len(pixel) == 3:               # RGB
            r, g, b = pixel
            yield r & 1
            yield g & 1
            yield b & 1
        elif len(pixel) == 4:              # RGBA – ignore alpha LSB
            r, g, b, _ = pixel
            yield r & 1
            yield g & 1
            yield b & 1
        else:
            # Grayscale etc. – just take the first three channels if available
            for channel in pixel[:3]:
                yield channel & 1

def embed_bits_into_image(image, bits, max_bits):
    """Replace LSBs of the image with `bits` (list of 0/1) up to `max_bits`."""
    if len(bits) > max_bits:
        raise ValueError(f"Message too long for this image (needs {len(bits)} bits, "
                         f"max {max_bits} available).")

    new_pixels = []
    bit_iter = iter(bits)
    for pixel in image.getdata():
        if len(pixel) >= 3:
            r, g, b = pixel[:3]
            # Replace LSB of each channel with next bit (if any)
            r = (r & 0xFE) | next(bit_iter, 0)
            g = (g & 0xFE) | next(bit_iter, 0)
            b = (b & 0xFE) | next(bit_iter, 0)
            new_pixel = list(pixel)
            new_pixel[:3] = (r, g, b)
            new_pixels.append(tuple(new_pixel))
        else:
            new_pixels.append(pixel)

        if len(new_pixels) * 3 >= len(bits):
            break

    # Pad the rest of the pixel data unchanged
    raw = list(image.getdata())
    for i in range(len(new_pixels), len(raw)):
        new_pixels.append(raw[i])

    # Build the new image
    new_img = Image.new(image.mode, image.size)
    new_img.putdata(new_pixels)
    return new_img


def hide_message(image_path, message, output_path):
    """Encode `message` into `image_path` and save to `output_path`."""
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    capacity_bits = width * height * 3   # 3 bits per pixel (R,G,B)

    # Length prefix: 32 bits (stores message length in bits)
    msg_bytes = message.encode("utf-8")
    msg_len_bits = len(msg_bytes) * 8
    if msg_len_bits > capacity_bits - 32:
        raise ValueError("Image is too small to hold this message.")

    # Build bit list: 32‑bit length + message bits
    length_bits = [(msg_len_bits >> i) & 1 for i in range(31, -1, -1)]
    msg_bits = [ (msg_bytes[j // 8] >> (7 - (j % 8))) & 1
                 for j in range(len(msg_bytes) * 8) ]
    bits = length_bits + msg_bits

    stego_img = embed_bits_into_image(img, bits, capacity_bits)
    stego_img.save(output_path)
    return stego_img


def extract_message(stego_path):
    """Decode hidden message from a stego image."""
    img = Image.open(stego_path).convert("RGB")
    width, height = img.size

    capacity_bits = width * height * 3
    if capacity_bits < 32:
        raise ValueError("Image is too small to contain a hidden message.")

    # Read first 32 bits to get length
    length_bits = []
    bit_iter = extract_bits_from_image(img)
    for _ in range(32):
        length_bits.append(next(bit_iter, 0))

    # Convert 32 bits (MSB first) to integer - this is message length in BITS
    message_len_bits = 0
    for bit in length_bits:
        message_len_bits = (message_len_bits << 1) | bit

    if message_len_bits % 8:
        raise ValueError("The encoded message length is invalid.")
    if message_len_bits > capacity_bits - 32:
        raise ValueError("The image does not contain a valid hidden message.")

    # Read the remaining bits (message_len_bits)
    total_bits_to_read = 32 + message_len_bits
    needed_bits = []
    bit_iter = extract_bits_from_image(img)
    for _ in range(total_bits_to_read):
        needed_bits.append(next(bit_iter, 0))

    # Extract message bytes (8 bits per byte)
    message_bytes = []
    for i in range(0, message_len_bits, 8):
        byte = 0
        for j in range(8):
            if i + j < len(needed_bits):
                byte |= (needed_bits[32 + i + j] << (7 - j))
        message_bytes.append(byte)

    message = bytes(message_bytes).decode("utf-8", errors="ignore")
    return message


# ----------------------------------------------------------------------
# Tkinter GUI
# ----------------------------------------------------------------------
class StegApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LSB Steganography Mini‑App")
        self.geometry("560x460")
        self.resizable(False, False)

        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, font=("Helvetica", 10))
        self.style.configure("TLabel", font=("Helvetica", 10))

        self._create_notebook()
        self._create_enc_tab()
        self._create_dec_tab()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _create_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_enc_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Encode")

        # Image selector
        ttk.Label(frame, text="Cover Image (PNG):").grid(row=0, column=0, sticky="w", pady=5)
        self.enc_img_path = StringVar()
        enc_entry = ttk.Entry(frame, textvariable=self.enc_img_path, width=50, state="readonly")
        enc_entry.grid(row=0, column=1, padx=5)

        def browse_enc():
            path = filedialog.askopenfilename(
                title="Select PNG image",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
            )
            if path:
                self.enc_img_path.set(path)

        ttk.Button(frame, text="Browse…", command=browse_enc).grid(row=0, column=2, padx=5)

        # Message entry
        ttk.Label(frame, text="Secret message:").grid(row=1, column=0, sticky="w", pady=5)
        self.enc_msg = StringVar()
        ttk.Entry(frame, textvariable=self.enc_msg, width=50).grid(row=1, column=1, columnspan=2, padx=5)

        # Encode button
        ttk.Button(frame, text="Encode → Save", command=self._encode).grid(
            row=2, column=0, columnspan=3, pady=10
        )

        # Feedback label
        self.enc_feedback = StringVar(value="Ready.")
        ttk.Label(frame, textvariable=self.enc_feedback, foreground="green").grid(
            row=3, column=0, columnspan=3, pady=2
        )

    def _create_dec_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Decode")

        # Image selector
        ttk.Label(frame, text="Stego Image (PNG):").grid(row=0, column=0, sticky="w", pady=5)
        self.dec_img_path = StringVar()
        dec_entry = ttk.Entry(frame, textvariable=self.dec_img_path, width=50, state="readonly")
        dec_entry.grid(row=0, column=1, padx=5)

        def browse_dec():
            path = filedialog.askopenfilename(
                title="Select PNG image",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
            )
            if path:
                self.dec_img_path.set(path)

        ttk.Button(frame, text="Browse…", command=browse_dec).grid(row=0, column=2, padx=5)

        # Decode button
        ttk.Button(frame, text="Decode → Show", command=self._decode).grid(
            row=1, column=0, columnspan=3, pady=10
        )

        # Feedback label
        self.dec_feedback = StringVar(value="Ready.")
        ttk.Label(frame, textvariable=self.dec_feedback, foreground="green").grid(
            row=2, column=0, columnspan=3, pady=2
        )

        # Area to display extracted text
        self.decode_output = tk.Text(frame, height=8, width=58, state="disabled", wrap="word")
        self.decode_output.grid(row=3, column=0, columnspan=3, pady=5)

    # ------------------------------------------------------------------
    # Encoding logic
    # ------------------------------------------------------------------
    def _encode(self):
        img_path = self.enc_img_path.get()
        message = self.enc_msg.get()
        if not img_path or not os.path.isfile(img_path):
            self.enc_feedback.set("❌ Choose a valid PNG image first.")
            return
        if not img_path.lower().endswith(".png"):
            self.enc_feedback.set("❌ Only PNG images are supported.")
            return
        if not message.strip():
            self.enc_feedback.set("❌ Enter a message to hide.")
            return

        try:
            out_path = img_path.rsplit(".", 1)[0] + "_encoded.png"
            hide_message(img_path, message, out_path)
            self.enc_feedback.set(f"✅ Saved encoded image: {os.path.basename(out_path)}")
        except Exception as e:
            self.enc_feedback.set(f"❌ Error: {str(e)}")

    # ------------------------------------------------------------------
    # Decoding logic
    # ------------------------------------------------------------------
    def _decode(self):
        img_path = self.dec_img_path.get()
        if not img_path or not os.path.isfile(img_path):
            self.dec_feedback.set("❌ Choose a valid PNG image first.")
            return
        if not img_path.lower().endswith(".png"):
            self.dec_feedback.set("❌ Only PNG images are supported.")
            return

        try:
            message = extract_message(img_path)
            # Show the decoded text
            self.decode_output.configure(state="normal")
            self.decode_output.delete("1.0", tk.END)
            self.decode_output.insert(tk.END, message)
            self.decode_output.configure(state="disabled")
            self.dec_feedback.set("✅ Message extracted.")
        except Exception as e:
            self.dec_feedback.set(f"❌ Extraction failed: {str(e)}")
            self.decode_output.configure(state="normal")
            self.decode_output.delete("1.0", tk.END)
            self.decode_output.insert(tk.END, f"[error] {e}")
            self.decode_output.configure(state="disabled")


if __name__ == "__main__":
    app = StegApp()
    app.mainloop()
