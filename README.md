# IEC 60909 Short-Circuit Waveform

Interactive plot of an **offset (asymmetrical) short-circuit current** as drawn in IEC 60909:

- total current \(i_k(t)\)
- decaying **d.c. component** (centre-line of the sinusoid)
- **top** and **bottom** envelopes

Sliders adjust \(I_k''\), \(I_k\), \(X/R\), d.c. offset, frequency, a.c. decay time, and plot duration. **Reset** restores the defaults. **Save PNG…** writes the waveform to an image file.

This is a **visualisation / teaching tool**, not a certified IEC 60909 calculation package and not affiliated with the IEC.

## Requirements

| Item | Version / notes |
| --- | --- |
| Python | 3.10 or newer |
| numpy | ≥ 1.26 |
| matplotlib | ≥ 3.8 |
| tkinter | Standard library. On Debian/Ubuntu/Fedora you must install the OS package (see below). |

Pinned install file: [`requirements.txt`](requirements.txt).

```text
numpy>=1.26
matplotlib>=3.8
```

Optional, only if you rebuild the Windows `.exe`:

```text
pyinstaller>=6.0
```

## Run from source (Linux / macOS / Windows)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python iec60909_waveform.py
```

On **Debian / Ubuntu**:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-tk
```

On **Fedora**:

```bash
sudo dnf install python3 python3-pip python3-tkinter
```

On **Windows**, official python.org installers include tkinter. Microsoft Store Python sometimes does not — use the python.org build if the window fails to open.

## Releases (v1.0.0)

Download from [Releases](https://github.com/commander-apemanx/IEC60909-Short-Circuit-Waveform/releases/tag/v1.0.0).

| Asset | Platform | What it is |
| --- | --- | --- |
| `IEC60909_Waveform-linux-v1.0.0.tar.gz` | Linux / macOS | Python source + `requirements.txt` |
| `IEC60909_Waveform-windows-v1.0.0.exe` | Windows 10/11 (x64) | Standalone app, no Python install |

### Linux archive

```bash
tar -xzf IEC60909_Waveform-linux-v1.0.0.tar.gz
cd IEC60909_Waveform-linux-v1.0.0
python3 -m pip install -r requirements.txt
python3 iec60909_waveform.py
```

### Windows executable

Double-click `IEC60909_Waveform-windows-v1.0.0.exe`. The first start can take several seconds while the bundle unpacks. Windows SmartScreen may warn because the binary is unsigned — choose **More info → Run anyway** if you trust the file.

## Parameters

| Control | Meaning |
| --- | --- |
| \(I_k''\) | Initial (subtransient) RMS current (kA) |
| \(I_k\) | Steady-state RMS current (kA). Set equal to \(I_k''\) for a far-from-generator fault (constant a.c. amplitude). |
| \(X/R\) | Reactance/resistance of the short-circuit path. Larger \(X/R\) → slower d.c. decay. |
| d.c. offset | −1 … +1. `+1` is maximum positive offset (IEC textbook figure). `0` is symmetrical. |
| \(f\) | System frequency (Hz) |
| \(T_{ac}\) | Time constant of a.c. amplitude decay \(I_k'' \rightarrow I_k\) (ms) |
| Duration | Plot length (ms) |

The d.c. time constant is \(\tau = (X/R) / (2\pi f)\). Peak factor \(\kappa = 1.02 + 0.98\,e^{-3R/X}\) follows IEC 60909-0.

## Rebuild the Windows executable

From this directory, with PyInstaller installed:

```bash
python -m pip install pyinstaller
python -m PyInstaller IEC60909_Waveform.spec
```

The binary is written to `dist/IEC60909_Waveform.exe`.

## Files in this repository

| File | Role |
| --- | --- |
| `iec60909_waveform.py` | Application |
| `requirements.txt` | Runtime Python packages |
| `IEC60909_Waveform.spec` | PyInstaller spec used to build the Windows `.exe` |
| `LICENSE` | CC BY 4.0 |
| `NOTICE` | Required credit text |
| `CITATION.cff` | Machine-readable citation (GitHub “Cite this repository”) |

## License and attribution

Copyright (c) 2026 [commander-apemanx](https://github.com/commander-apemanx).

This project is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You may use, copy, modify, and share it — **including commercially** — **only if you give credit**.

### Required credit

```
IEC 60909 Short-Circuit Waveform by commander-apemanx
https://github.com/commander-apemanx/IEC60909-Short-Circuit-Waveform
Licensed under CC BY 4.0
```

Put that credit (or a hyperlink that shows it) in:

- copies and modified versions of the software
- documentation of any derivative tool
- publications, reports, screenshots, and plots you share that were produced with this software

GitHub’s **Cite this repository** button uses `CITATION.cff`. Full terms: [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Disclaimer

IEC 60909 is an International Electrotechnical Commission standard. This project is an independent educational plotter. Verify any engineering result against the published standard and your network model.
