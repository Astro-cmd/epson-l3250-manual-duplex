import os
import shutil
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import win32print
from pypdf import PdfReader, PdfWriter

APP_NAME = "L3250 Manual Duplex Printer"

# SumatraPDF print settings. Add ",monochrome" for black and white.
PRINT_SETTINGS = "fit,paper=A4"


def find_sumatra():
    candidates = [
        shutil.which("SumatraPDF"),
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\SumatraPDF\SumatraPDF.exe"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def default_printer():
    try:
        return win32print.GetDefaultPrinter()
    except Exception:
        return ""


def installed_printers():
    try:
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        return [item[2] for item in win32print.EnumPrinters(flags)]
    except Exception:
        return []


def make_pdf(source, pages, destination, rotate=0):
    """pages: list of page indexes; None inserts a blank page."""
    reader = PdfReader(source)
    writer = PdfWriter()
    first = reader.pages[0]
    width, height = float(first.mediabox.width), float(first.mediabox.height)

    for number in pages:
        if number is None:
            writer.add_blank_page(width=width, height=height)
        else:
            writer.add_page(reader.pages[number])

    if rotate:
        for page in writer.pages:
            page.rotate(rotate)

    with open(destination, "wb") as output:
        writer.write(output)


def send_to_printer(pdf_file, printer):
    exe = find_sumatra()
    if not exe:
        raise RuntimeError(
            "SumatraPDF not found. Install it from sumatrapdfreader.org."
        )
    subprocess.run(
        [
            exe,
            "-print-to", printer,
            "-print-settings", PRINT_SETTINGS,
            "-silent",
            os.path.abspath(pdf_file),
        ],
        check=True,
    )


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("650x500")
        self.root.minsize(650, 500)

        self.pdf = ""
        self.printer = tk.StringVar(value=default_printer())
        self.edge = tk.StringVar(value="long")
        self.file_text = tk.StringVar(value="No PDF selected")
        self.status = tk.StringVar(value="Ready.")

        self.build()
        self.refresh_printers()

    def build(self):
        ttk.Label(
            self.root,
            text="Epson L3250 Manual Duplex Printer",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(20, 4))

        ttk.Label(
            self.root,
            text="Print one side → reload paper → print the other side",
        ).pack(pady=(0, 18))

        file_box = ttk.LabelFrame(self.root, text="1. PDF document")
        file_box.pack(fill="x", padx=20, pady=8)

        ttk.Button(
            file_box,
            text="Choose PDF",
            command=self.choose_pdf,
        ).grid(row=0, column=0, padx=12, pady=14)

        ttk.Label(
            file_box,
            textvariable=self.file_text,
            wraplength=480,
        ).grid(row=0, column=1, sticky="w")

        printer_box = ttk.LabelFrame(self.root, text="2. Printer")
        printer_box.pack(fill="x", padx=20, pady=8)

        self.printer_combo = ttk.Combobox(
            printer_box,
            textvariable=self.printer,
            state="readonly",
            width=55,
        )
        self.printer_combo.grid(row=0, column=0, padx=12, pady=14)

        ttk.Button(
            printer_box,
            text="Refresh",
            command=self.refresh_printers,
        ).grid(row=0, column=1)

        edge_box = ttk.LabelFrame(self.root, text="3. Flip direction")
        edge_box.pack(fill="x", padx=20, pady=8)

        ttk.Radiobutton(
            edge_box,
            text="Long edge — normal book/document",
            variable=self.edge,
            value="long",
        ).pack(anchor="w", padx=12, pady=(10, 4))

        ttk.Radiobutton(
            edge_box,
            text="Short edge — calendar/notebook",
            variable=self.edge,
            value="short",
        ).pack(anchor="w", padx=12, pady=(4, 10))

        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=20, pady=18)

        self.start = ttk.Button(
            bottom,
            text="Start Duplex Printing",
            command=self.start_print,
        )
        self.start.pack(side="left")

        ttk.Label(
            bottom,
            textvariable=self.status,
            wraplength=390,
        ).pack(side="left", padx=15)

        ttk.Label(
            self.root,
            text=(
                "Test with a 2-page PDF first. The physical reload direction "
                "must be verified on your L3250."
            ),
            wraplength=590,
        ).pack(padx=20, pady=5)

    def refresh_printers(self):
        printers = installed_printers()
        if printers:
            self.printer_combo["values"] = printers
            if self.printer.get() not in printers:
                self.printer.set(printers[0])

    def choose_pdf(self):
        path = filedialog.askopenfilename(
            title="Select PDF",
            filetypes=[("PDF documents", "*.pdf")],
        )

        if not path:
            return

        try:
            pages = len(PdfReader(path).pages)
        except Exception as error:
            messagebox.showerror(APP_NAME, f"Cannot read PDF:\n\n{error}")
            return

        self.pdf = path
        self.file_text.set(f"{os.path.basename(path)} — {pages} pages")
        self.status.set(f"{pages} pages ready.")

    def start_print(self):
        if not self.pdf:
            messagebox.showwarning(APP_NAME, "Choose a PDF first.")
            return

        printer = self.printer.get().strip()
        if not printer:
            messagebox.showwarning(APP_NAME, "Select the L3250 printer first.")
            return

        try:
            total = len(PdfReader(self.pdf).pages)
        except Exception as error:
            messagebox.showerror(APP_NAME, str(error))
            return

        # Odd pages (1, 3, 5, ...) and even pages (2, 4, 6, ...), both in
        # normal order. The L3250 outputs face-up, so no reversal is needed.
        front = list(range(0, total, 2))
        back = list(range(1, total, 2))

        # Odd page count: the last sheet's back is blank.
        if total % 2 == 1:
            back.append(None)

        # Short-edge flip: the back-side pages must be rotated 180 degrees.
        back_rotation = 180 if self.edge.get() == "short" else 0

        temp_dir = tempfile.mkdtemp(prefix="l3250_duplex_")
        front_pdf = os.path.join(temp_dir, "01_odd_pages.pdf")
        back_pdf = os.path.join(temp_dir, "02_even_pages.pdf")

        try:
            make_pdf(self.pdf, front, front_pdf)
            make_pdf(self.pdf, back, back_pdf, rotate=back_rotation)

            self.start.config(state="disabled")

            # PASS 1: even pages first
            self.status.set("Sending first pass...")
            self.root.update()

            send_to_printer(back_pdf, printer)

            self.status.set("Reload the paper.")
            self.root.update()

            messagebox.showinfo(
                APP_NAME,
                "FIRST PASS SENT\n\n"
                "Wait for the L3250 to finish.\n\n"
                "Reload the printed stack using the correct orientation for "
                f"{'long-edge' if self.edge.get() == 'long' else 'short-edge'} "
                "flipping.\n\n"
                "Then click OK.",
            )

            # PASS 2: odd pages second
            self.status.set("Sending second pass...")
            self.root.update()

            send_to_printer(front_pdf, printer)

            self.status.set("Duplex job sent.")
            messagebox.showinfo(
                APP_NAME,
                "SECOND PASS SENT.\n\nThe duplex print job is complete.",
            )

        except Exception as error:
            self.status.set("Printing failed.")
            messagebox.showerror(
                APP_NAME,
                "Printing failed:\n\n"
                f"{error}\n\n"
                "Check that SumatraPDF and the Epson driver are installed, "
                "and that the printer is online.",
            )
        finally:
            self.start.config(state="normal")
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()