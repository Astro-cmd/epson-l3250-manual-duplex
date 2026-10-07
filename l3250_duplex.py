import os
import re
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


def parse_page_range(text, total):
    """
    Turn a range string into a sorted list of 0-based page indexes.

    Accepted examples (page numbers start at 1):
        "5"           -> page 5
        "1-5"         -> pages 1 to 5
        "1-5, 8, 10-12"
        "7-"          -> page 7 to the last page
        "-4"          -> pages 1 to 4

    Duplicates are removed and the pages are always printed in ascending order.
    Raises ValueError with a readable message if the text is invalid.
    """
    text = text.strip()
    if not text:
        raise ValueError("Enter a page range, for example: 1-5, 8, 10-12")

    pages = set()

    for part in text.split(","):
        part = part.strip()
        if not part:
            continue

        match = re.fullmatch(r"(\d*)\s*-\s*(\d*)", part)
        if match:
            start_text, end_text = match.groups()
            if not start_text and not end_text:
                raise ValueError(f"'{part}' is not a valid range.")
            start = int(start_text) if start_text else 1
            end = int(end_text) if end_text else total
        elif part.isdigit():
            start = end = int(part)
        else:
            raise ValueError(
                f"'{part}' is not valid. Use numbers, commas and dashes, "
                "for example: 1-5, 8, 10-12"
            )

        if start < 1 or end < 1:
            raise ValueError("Page numbers start at 1.")
        if start > end:
            raise ValueError(f"'{part}' goes backwards. Write it as {end}-{start}.")
        if end > total:
            raise ValueError(
                f"Page {end} is outside the document (it has {total} pages)."
            )

        pages.update(range(start - 1, end))

    if not pages:
        raise ValueError("No pages selected.")

    return sorted(pages)


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
        self.root.geometry("650x610")
        self.root.minsize(650, 610)

        self.pdf = ""
        self.total_pages = 0
        self.printer = tk.StringVar(value=default_printer())
        self.edge = tk.StringVar(value="long")
        self.range_mode = tk.StringVar(value="all")
        self.range_text = tk.StringVar(value="")
        self.file_text = tk.StringVar(value="No PDF selected")
        self.status = tk.StringVar(value="Ready.")

        self.build()
        self.refresh_printers()
        self.update_range_state()

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

        # 1. PDF
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

        # 2. Printer
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

        # 3. Page range
        range_box = ttk.LabelFrame(self.root, text="3. Pages to print")
        range_box.pack(fill="x", padx=20, pady=8)

        ttk.Radiobutton(
            range_box,
            text="All pages",
            variable=self.range_mode,
            value="all",
            command=self.update_range_state,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 4))

        ttk.Radiobutton(
            range_box,
            text="Page range:",
            variable=self.range_mode,
            value="custom",
            command=self.update_range_state,
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(4, 4))

        self.range_entry = ttk.Entry(
            range_box,
            textvariable=self.range_text,
            width=34,
        )
        self.range_entry.grid(row=1, column=1, sticky="w", pady=(4, 4))

        ttk.Label(
            range_box,
            text="Examples: 1-5   or   2, 4, 7-9   or   10-   (page 10 to the end)",
            foreground="#555555",
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 10))

        # 4. Flip direction
        edge_box = ttk.LabelFrame(self.root, text="4. Flip direction")
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

    def update_range_state(self):
        if self.range_mode.get() == "custom":
            self.range_entry.config(state="normal")
            self.range_entry.focus_set()
        else:
            self.range_entry.config(state="disabled")

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
        self.total_pages = pages
        self.file_text.set(f"{os.path.basename(path)} — {pages} pages")
        self.status.set(f"{pages} pages ready.")

    def selected_pages(self, total):
        """Return the list of 0-based page indexes the user wants to print."""
        if self.range_mode.get() == "all":
            return list(range(total))
        return parse_page_range(self.range_text.get(), total)

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

        # Work out which pages to print.
        try:
            selected = self.selected_pages(total)
        except ValueError as error:
            messagebox.showwarning(APP_NAME, str(error))
            return

        count = len(selected)
        if count < 2:
            messagebox.showwarning(
                APP_NAME,
                "Manual duplex needs at least 2 pages.\n\n"
                "For a single page, print it normally.",
            )
            return

        sheets = (count + 1) // 2

        # Position 1, 3, 5... in the selection go on the front of each sheet,
        # position 2, 4, 6... go on the back. Both are in normal order because
        # the L3250 outputs pages face-up.
        front = selected[0::2]
        back = selected[1::2]

        # Odd number of selected pages: the last sheet's back is blank.
        if count % 2 == 1:
            back.append(None)

        # Short-edge flip: the back-side pages must be rotated 180 degrees.
        back_rotation = 180 if self.edge.get() == "short" else 0

        if not messagebox.askokcancel(
            APP_NAME,
            f"Print {count} page{'s' if count != 1 else ''} "
            f"on {sheets} sheet{'s' if sheets != 1 else ''}?\n\n"
            "Load at least that many sheets in the rear tray.",
        ):
            return

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

            self.status.set(f"Duplex job sent ({count} pages, {sheets} sheets).")
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