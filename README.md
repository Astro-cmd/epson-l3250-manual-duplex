# Epson L3250 Manual Duplex Printer

A small Windows desktop app that adds **manual double-sided (duplex) printing** to printers that only print on one side, such as the **Epson EcoTank L3250**. It splits a PDF into two print jobs, tells you when to reload the paper, and sends the second job in the right order and orientation.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

<!-- Add a screenshot: save it as docs/screenshot.png and uncomment the line below -->
<!-- ![App screenshot](docs/screenshot.png) -->

---

## Table of contents

- [Why this exists](#why-this-exists)
- [Features](#features)
- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Running from WSL](#running-from-wsl)
- [Choosing the flip direction](#choosing-the-flip-direction)
- [Reloading the paper](#reloading-the-paper)
- [Testing and calibration](#testing-and-calibration)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Building a standalone .exe](#building-a-standalone-exe)
- [Project structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Why this exists

The Epson L3250 has no automatic duplex unit. Windows can sometimes fake manual duplex through the printer driver, but the result is inconsistent and depends on the app you print from. This tool takes over that job:

1. It prints one set of pages.
2. It pauses while you reload the stack.
3. It prints the other set on the reverse sides.

The page order and rotation are handled for you, so each sheet comes out with the correct pages on the front and back.

## Features

- Manual duplex printing from any PDF
- Page pairing handled automatically (pages 1 and 2 on sheet 1, 3 and 4 on sheet 2, and so on)
- **Long-edge** (book/document) and **short-edge** (calendar/notebook) flip modes
- Automatic **180° rotation** of the back pages in short-edge mode
- **Odd page counts** handled with a blank back side on the last sheet
- Printer picker listing all installed Windows printers
- Silent printing through SumatraPDF, so it does not depend on your default PDF reader
- Temporary files are created and cleaned up automatically
- Launcher scripts for Windows (`.bat`) and WSL (`.sh`)

## How it works

For a PDF with *N* pages, the app builds two temporary PDFs:

| Job | Pages | Printed |
|-----|-------|---------|
| Even pages | 2, 4, 6, ... | First pass |
| Odd pages | 1, 3, 5, ... | Second pass |

If the page count is odd, a blank page is added to the even-page job so every sheet stays paired.

In short-edge mode the even-page job is rotated 180° so the back of each sheet reads upright when flipped over the short edge.

Printing is done by calling SumatraPDF in silent mode:

```
SumatraPDF.exe -print-to "<printer name>" -print-settings "fit,paper=A4" -silent <file.pdf>
```

> The app prints the even pages first and the odd pages second. This matches how the L3250 outputs pages (face-up) and gives the correct page order on each sheet. If your printer behaves differently, see [Troubleshooting](#troubleshooting).

## Requirements

- **Windows 10 or 11**
- **Python 3.9 or newer** (Windows version)
- **SumatraPDF** (free)
- An installed Windows driver for your printer (the Epson L3250 driver)
- Python packages: `pywin32` and `pypdf` (listed in `requirements.txt`)

## Installation

**1. Clone the repository**

```powershell
git clone https://github.com/Astro-cmd/epson-l3250-manual-duplex.git
cd epson-l3250-manual-duplex
```

**2. (Optional) create a virtual environment**

```powershell
python -m venv venv
venv\Scripts\activate
```

**3. Install the Python dependencies**

```powershell
pip install -r requirements.txt
```

**4. Install SumatraPDF**

```powershell
winget install SumatraPDF.SumatraPDF
```

Or download it from <https://www.sumatrapdfreader.org/>. The app looks for it in these places:

- Your system `PATH`
- `C:\Program Files\SumatraPDF\SumatraPDF.exe`
- `C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe`
- `%LOCALAPPDATA%\SumatraPDF\SumatraPDF.exe`

If you use the portable version, add its path to the `candidates` list in `find_sumatra()`.

**5. Check that SumatraPDF can print on its own**

```powershell
& "$env:LOCALAPPDATA\SumatraPDF\SumatraPDF.exe" -print-to "EPSON L3250 Series" -silent "C:\path\to\test.pdf"
```

If this prints, the app will print too.

## Usage

Start the app in any of these ways:

```powershell
# Double-click run_l3250.bat, or from a terminal:
.\run_l3250.bat

# Or run the script directly:
python l3250_duplex.py
```

`run_l3250.bat` looks for Windows Python (`py`, then `python`) and starts the app. If Python is missing, it prints install instructions.

Then:

1. Click **Choose PDF** and select your document.
2. Select your printer from the dropdown (click **Refresh** if it's missing).
3. Select the **flip direction** (see below).
4. Click **Start Duplex Printing**.
5. Wait for the first pass to finish, then **reload the paper** following the [instructions below](#reloading-the-paper).
6. Click **OK** in the popup to print the second pass.

## Running from WSL

The app needs **Windows Python**, because it talks to Windows printers through `pywin32`. If you work in WSL, the helper scripts run the Windows Python for you:

```bash
./setup_wsl.sh    # installs requirements.txt using Windows Python (py.exe or python.exe)
./run_l3250.sh    # starts the app
```

Install Python for Windows first. Python installed inside WSL cannot access Windows printers.

## Choosing the flip direction

| Document | Orientation | Choose |
|----------|-------------|--------|
| Normal document, report, book | Portrait | **Long edge** |
| Calendar, notepad (binding at the top) | Portrait | **Short edge** |
| Landscape slides or document read like a book | Landscape | **Short edge** |
| Landscape document flipped like a calendar | Landscape | **Long edge** |

If you're unsure, choose **Long edge** for portrait documents.

## Reloading the paper

After the first pass finishes:

1. Let the ink dry for a few seconds.
2. Take the whole stack from the output tray **without shuffling it**.
3. Flip it over like turning the page of a book (long edge), so the printed sides face away from you and the blank sides face you.
4. Put it back in the rear paper tray with the **same end going in first** as the first time.
5. Adjust the edge guides, then click **OK** in the app.

For **short-edge** mode, flip the stack over the **short** edge instead. The app has already rotated the pages for this.

> Printers load paper differently. Always confirm the reload steps with the [test PDF](#testing-and-calibration) before printing an important document. Once you know what works on your printer, you can edit the message in `start_print` to match.

## Testing and calibration

Always test with a short document first. The repository includes **`duplex_test_8_pages.pdf`**, an 8-page A4 file with a **big page number**, a **"TOP" arrow**, and a **corner marker** on every page, so upside-down or wrongly ordered pages are easy to spot.

**Expected result for the 8-page test (4 sheets):**

| Sheet | Front | Back |
|-------|-------|------|
| 1 | Page 1 | Page 2 |
| 2 | Page 3 | Page 4 |
| 3 | Page 5 | Page 6 |
| 4 | Page 7 | Page 8 |

**How to check:** hold a sheet with the front facing you and the arrow pointing up. Flip it like a book page. The back should show the next page number with its arrow also pointing up.

Also test a **3-page PDF** to confirm the blank-back logic for odd page counts.

## Configuration

Edit the constants at the top of `l3250_duplex.py`:

```python
# SumatraPDF print settings. Add ",monochrome" for black and white.
PRINT_SETTINGS = "fit,paper=A4"
```

Some useful values for `PRINT_SETTINGS`:

| Setting | Meaning |
|---------|---------|
| `fit` | Scale the page to fit the paper |
| `noscale` | Print at actual size |
| `paper=A4` | Paper size (`A4`, `A5`, `letter`, ...) |
| `monochrome` | Black and white (saves colour ink) |
| `color` | Force colour |

Combine them with commas, for example `"fit,paper=A4,monochrome"`.

Print quality and paper type (plain, photo, and so on) come from the Epson driver defaults: **Settings > Bluetooth & devices > Printers & scanners > EPSON L3250 Series > Printing preferences**.

## Troubleshooting

### "SumatraPDF not found."

Install SumatraPDF (see [Installation](#installation)) or add its path to `find_sumatra()`.

### "A device attached to the system is not functioning" (error 31)

This was the error from the older `ShellExecute` method, which relied on the default PDF app's print handler. This app uses SumatraPDF instead, so you should not see it. If you do, check that the printer is online and the queue isn't paused.

### The printer is not in the dropdown

Click **Refresh**. Check that the printer appears in Windows under Printers & scanners.

### Nothing prints, and no error appears

Open the print queue and check that the printer isn't offline, paused, or showing "Use printer offline". Then run the standalone SumatraPDF test from the installation section.

### The back sides are upside down

- Long-edge mode: reload the stack rotated 180°, or change `back_rotation` to `180` for long edge in `start_print`.
- Short-edge mode: remove the 180° rotation (set `back_rotation = 0`).

### The pages are paired wrongly (page 2 behind page 3, for example)

The stack order is wrong when reloading. Take the stack from the tray in the same order as it came out and do not reverse it.

### Each sheet has the right pages, but front and back are swapped

Swap the two `send_to_printer` calls in `start_print` so the other set prints first.

### Page sizes look wrong or content is cut off

Set `paper=A4` (or your paper size) in `PRINT_SETTINGS` and use `fit`. Confirm the paper size in the Epson printing preferences too.

### Ink smudges on the second pass

Wait longer before reloading, or use a higher-quality paper setting in the driver.

### The launcher says "Windows Python was not found"

Install Python for Windows from <https://www.python.org/downloads/> and tick **Add python.exe to PATH** during setup.

## Building a standalone .exe

You can build a single executable so others can run the app without installing Python:

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed l3250_duplex.py
```

The executable is created in the `dist/` folder. SumatraPDF still needs to be installed on the target PC, or placed in one of the locations the app searches.

## Project structure

```
epson-l3250-manual-duplex/
├── l3250_duplex.py           # The application
├── requirements.txt          # Python dependencies
├── run_l3250.bat             # Windows launcher
├── run_l3250.sh              # WSL launcher
├── setup_wsl.sh              # Installs dependencies from WSL using Windows Python
├── duplex_test_8_pages.pdf   # Calibration PDF
└── README.md
```

## Roadmap

Ideas for future versions:

- [ ] Page range selection
- [ ] Number of copies
- [ ] Black and white / draft mode checkbox
- [ ] "Even pages first" checkbox
- [ ] Remember the last printer and flip direction
- [ ] Printer status check before printing
- [ ] Paper size dropdown
- [ ] 2-up and 4-up pages per sheet
- [ ] Booklet mode
- [ ] Reprint from a chosen sheet after a paper jam
- [ ] Progress indicator and cancel button
- [ ] Print history log

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push the branch: `git push origin feature/your-feature`
5. Open a pull request

If you test the app on another printer, please open an issue with the printer model and the reload steps that worked, so the compatibility list can grow.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgements

- [SumatraPDF](https://www.sumatrapdfreader.org/) for reliable command-line printing
- [pypdf](https://github.com/py-pdf/pypdf) for PDF splitting and rotation
- [pywin32](https://github.com/mhammond/pywin32) for Windows printer access

## Author

**Moses Wanjiku Muichuhia** (PurpleStack)

- GitHub: [Astro-cmd](https://github.com/Astro-cmd)
- Portfolio: <https://moses-muichuhia.vercel.app/>
