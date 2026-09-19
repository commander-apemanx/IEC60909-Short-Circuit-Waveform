#!/usr/bin/env python3
"""
IEC 60909 short-circuit current waveform.

Tkinter UI with an embedded matplotlib plot. Reset and Save are native
buttons (not matplotlib widgets), so they keep working in the .exe.

    python iec60909_waveform.py

Copyright (c) 2026 commander-apemanx
Licensed under CC BY 4.0. Attribution is required — see NOTICE.
https://github.com/commander-apemanx/IEC60909-Short-Circuit-Waveform
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from dataclasses import dataclass, replace
from tkinter import filedialog, messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _output_dir() -> str:
    if _is_frozen():
        return os.path.dirname(sys.executable)
    return os.getcwd()


def _log(msg: str) -> None:
    try:
        print(msg)
    except Exception:
        pass


AUTHOR = "commander-apemanx"
REPO_URL = "https://github.com/commander-apemanx/IEC60909-Short-Circuit-Waveform"
LICENSE_ID = "CC BY 4.0"
CREDIT_LINE = (
    f"IEC 60909 Short-Circuit Waveform by {AUTHOR}  ·  {REPO_URL}  ·  {LICENSE_ID}"
)


# ---------------------------------------------------------------------------
# User parameters
# ---------------------------------------------------------------------------
@dataclass
class UserParams:
    I_k: float = 20.0
    I_kpp: float = 25.0
    xr_ratio: float = 14.0
    frequency: float = 50.0
    dc_offset: float = 1.0
    T_ac: float = 0.080
    t_end: float = 0.24
    n_samples: int = 5000


DEFAULTS = UserParams()

# Slider definitions: key, label, min, max, default, resolution
CONTROLS = [
    ("I_kpp", "I_k'' (kA)", 1.0, 80.0, DEFAULTS.I_kpp, 0.1),
    ("I_k", "I_k (kA)", 1.0, 80.0, DEFAULTS.I_k, 0.1),
    ("xr_ratio", "X/R", 1.0, 60.0, DEFAULTS.xr_ratio, 0.1),
    ("dc_offset", "d.c. offset", -1.0, 1.0, DEFAULTS.dc_offset, 0.01),
    ("frequency", "Frequency (Hz)", 16.0, 60.0, DEFAULTS.frequency, 0.5),
    ("T_ac_ms", "T_ac (ms)", 10.0, 400.0, DEFAULTS.T_ac * 1e3, 1.0),
    ("t_end_ms", "Duration (ms)", 40.0, 500.0, DEFAULTS.t_end * 1e3, 1.0),
]


# ---------------------------------------------------------------------------
# IEC 60909 model
# ---------------------------------------------------------------------------
def time_constant(xr_ratio: float, frequency: float) -> float:
    return xr_ratio / (2.0 * np.pi * frequency)


def kappa_iec(xr_ratio: float) -> float:
    return 1.02 + 0.98 * np.exp(-3.0 / xr_ratio)


def compute(p: UserParams) -> dict:
    f = p.frequency
    omega = 2.0 * np.pi * f
    tau = time_constant(p.xr_ratio, f)
    t = np.linspace(0.0, p.t_end, p.n_samples)

    I_ac_rms = p.I_k + (p.I_kpp - p.I_k) * np.exp(-t / p.T_ac)
    I_ac_peak = np.sqrt(2.0) * I_ac_rms

    dc = float(np.clip(p.dc_offset, -1.0, 1.0))
    phase0 = np.arcsin(-dc)

    i_ac = I_ac_peak * np.sin(omega * t + phase0)
    i_dc = dc * np.sqrt(2.0) * p.I_kpp * np.exp(-t / tau)
    i_total = i_ac + i_dc

    top = i_dc + I_ac_peak
    bottom = i_dc - I_ac_peak

    ip_t, ip_val = _first_extremum(t, i_total, positive=(dc >= 0.0))

    return {
        "t": t,
        "i_total": i_total,
        "i_dc": i_dc,
        "i_ac": i_ac,
        "top": top,
        "bottom": bottom,
        "tau": tau,
        "kappa": kappa_iec(p.xr_ratio),
        "A": abs(i_dc[0]),
        "ip": ip_val,
        "ip_t": ip_t,
        "pkpk_initial": 2.0 * np.sqrt(2.0) * p.I_kpp,
        "pkpk_steady": 2.0 * np.sqrt(2.0) * p.I_k,
        "ip_iec": kappa_iec(p.xr_ratio) * np.sqrt(2.0) * p.I_kpp,
    }


def _first_extremum(t: np.ndarray, y: np.ndarray, positive: bool) -> tuple[float, float]:
    dy = np.diff(y)
    if positive:
        turns = np.where((dy[:-1] > 0.0) & (dy[1:] <= 0.0))[0]
    else:
        turns = np.where((dy[:-1] < 0.0) & (dy[1:] >= 0.0))[0]
    i = int(turns[0] + 1) if turns.size else int(np.argmax(y) if positive else np.argmin(y))
    return float(t[i]), float(y[i])


def dc_i2t(p: UserParams) -> float:
    """DC let-through specific energy over [0, T], T = Duration (t_end).

    Circuit-breaker datasheet quantity: I²t = ∫ i_dc(t)² dt.
    Returns (kA)²·s (i_dc in kA, t in seconds). Not joules; E = R·I²t.
    """
    data = compute(p)
    i2 = np.square(data["i_dc"])
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(i2, data["t"]))
    return float(np.trapz(i2, data["t"]))


def _info_text(p: UserParams, d: dict) -> str:
    return (
        "IEC 60909 quantities\n"
        "--------------------\n"
        f"f           = {p.frequency:.1f} Hz\n"
        f"X/R         = {p.xr_ratio:.2f}\n"
        f"tau = L/R   = {d['tau']*1e3:.2f} ms\n"
        f"T_ac        = {p.T_ac*1e3:.1f} ms\n"
        f"d.c. offset = {p.dc_offset:+.2f}\n"
        "\n"
        f"I_k''       = {p.I_kpp:.2f} kA rms\n"
        f"I_k         = {p.I_k:.2f} kA rms\n"
        f"sqrt(2) I_k'' = {np.sqrt(2)*p.I_kpp:.2f} kA pk\n"
        f"sqrt(2) I_k   = {np.sqrt(2)*p.I_k:.2f} kA pk\n"
        "\n"
        f"A  (d.c.0)  = {d['A']:.2f} kA\n"
        f"k (IEC)     = {d['kappa']:.3f}\n"
        f"i_p (IEC)   = {d['ip_iec']:.2f} kA\n"
        f"i_p (sim)   = {d['ip']:.2f} kA\n"
        f"  at t      = {d['ip_t']*1e3:.2f} ms\n"
        f"2sqrt(2) I_k'' = {d['pkpk_initial']:.2f} kA\n"
        f"2sqrt(2) I_k   = {d['pkpk_steady']:.2f} kA"
    )


def _iec_annotations(ax, d: dict) -> list:
    arts = []
    t_ms = d["t"] * 1e3
    t_end = t_ms[-1]
    top0, bot0 = float(d["top"][0]), float(d["bottom"][0])
    topN, botN = float(d["top"][-1]), float(d["bottom"][-1])
    A = float(d["i_dc"][0])
    ip, ip_t = d["ip"], d["ip_t"] * 1e3

    def vdim(x, y0, y1, text, dx, color="#444444"):
        ann = ax.annotate(
            "", xy=(x, y1), xytext=(x, y0),
            arrowprops=dict(arrowstyle="<->", color=color, lw=1.0),
            zorder=5,
        )
        txt = ax.text(
            x + dx, 0.5 * (y0 + y1), text,
            va="center", ha="left" if dx > 0 else "right",
            fontsize=8.5, color=color,
            rotation=90 if abs(y1 - y0) > 8 else 0,
            zorder=5,
        )
        return [ann, txt]

    x_left = -0.015 * t_end
    arts += vdim(x_left, bot0, top0, r"$2\sqrt{2}\,I_k''$", dx=-0.012 * t_end)

    if abs(A) > 0.05 * max(abs(top0), 1e-9):
        arts += vdim(0.012 * t_end, 0.0, A, r"$A$", dx=0.008 * t_end, color="#c0392b")

    arts += vdim(
        max(ip_t - 0.018 * t_end, 0.045 * t_end), 0.0, ip,
        r"$i_p$", dx=0.008 * t_end, color="#1a1a1a",
    )
    peak_mark, = ax.plot([ip_t], [ip], "o", color="#1a1a1a", ms=4.5, zorder=6)
    arts.append(peak_mark)

    arts += vdim(t_end * 1.025, botN, topN, r"$2\sqrt{2}\,I_k$", dx=0.008 * t_end)

    i_call = int(0.22 * len(t_ms))
    arts.append(ax.annotate(
        "Top envelope",
        xy=(t_ms[i_call], d["top"][i_call]),
        xytext=(t_ms[i_call] + 0.08 * t_end, d["top"][i_call] + 0.12 * abs(top0)),
        fontsize=8, color="#1f6aa5",
        arrowprops=dict(arrowstyle="->", color="#1f6aa5", lw=0.8),
    ))
    arts.append(ax.annotate(
        r"d.c. component $i_{\mathrm{d.c.}}$",
        xy=(t_ms[i_call], d["i_dc"][i_call]),
        xytext=(t_ms[i_call] + 0.10 * t_end,
                d["i_dc"][i_call] + 0.18 * abs(top0) * np.sign(A + 1e-12)),
        fontsize=8, color="#c0392b",
        arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.8),
    ))
    j_call = int(0.18 * len(t_ms))
    arts.append(ax.annotate(
        "Bottom envelope",
        xy=(t_ms[j_call], d["bottom"][j_call]),
        xytext=(t_ms[j_call] + 0.08 * t_end, d["bottom"][j_call] - 0.18 * abs(top0)),
        fontsize=8, color="#1e8449",
        arrowprops=dict(arrowstyle="->", color="#1e8449", lw=0.8),
    ))
    return arts


def _autoscale(ax, data: dict) -> None:
    t_ms = data["t"] * 1e3
    y = np.concatenate([data["top"], data["bottom"], data["i_total"]])
    y_abs = float(np.max(np.abs(y)))
    ax.set_xlim(-0.04 * t_ms[-1], t_ms[-1] * 1.06)
    ax.set_ylim(-1.18 * y_abs, 1.22 * y_abs)


# ---------------------------------------------------------------------------
# Tkinter application
# ---------------------------------------------------------------------------
class WaveformApp:
    """IEC 60909 plotter. All controls are Tk widgets held on the instance."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("IEC 60909 short-circuit current — commander-apemanx")
        self.root.minsize(1100, 720)
        self.root.geometry("1280x820")
        self._updating = False
        self.annotations: list = []
        self.vars: dict[str, tk.DoubleVar] = {}
        self.value_labels: dict[str, ttk.Label] = {}

        self._apply_theme()
        self._build_plot()
        self._build_controls()
        self._build_info()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.refresh()

    def _apply_theme(self) -> None:
        style = ttk.Style(self.root)
        for name in ("vista", "xpnative", "clam"):
            if name in style.theme_names():
                style.theme_use(name)
                break
        style.configure("TButton", padding=(14, 6), font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 9))
        style.configure("Value.TLabel", font=("Segoe UI", 9), width=7, anchor="e")
        style.configure("Hint.TLabel", font=("Segoe UI", 8), foreground="#555555")

    def _build_plot(self) -> None:
        plot_frame = ttk.Frame(self.root)
        plot_frame.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        self.fig = Figure(figsize=(10.5, 5.6), dpi=100, facecolor="white")
        self.ax = self.fig.add_axes([0.08, 0.16, 0.90, 0.76])
        self.ax.grid(True, alpha=0.35)
        self.ax.set_xlabel("Time (ms)")
        self.ax.set_ylabel("Current (kA)")
        self.ax.set_title("IEC 60909 short-circuit current — offset waveform with envelopes")
        self.fig.text(
            0.5, 0.012, CREDIT_LINE,
            ha="center", va="bottom", fontsize=7, color="#555555",
        )

        data = compute(DEFAULTS)
        t_ms = data["t"] * 1e3
        (self.line_i,) = self.ax.plot(
            t_ms, data["i_total"], color="#1a1a1a", lw=1.7,
            label="Short-circuit current $i_k(t)$", zorder=3,
        )
        (self.line_dc,) = self.ax.plot(
            t_ms, data["i_dc"], color="#c0392b", ls="--", lw=1.6,
            label=r"d.c. component $i_{\mathrm{d.c.}}$ (centre-line)", zorder=4,
        )
        (self.line_top,) = self.ax.plot(
            t_ms, data["top"], color="#1f6aa5", ls="--", lw=1.25,
            label="Top envelope", zorder=2,
        )
        (self.line_bot,) = self.ax.plot(
            t_ms, data["bottom"], color="#1e8449", ls="--", lw=1.25,
            label="Bottom envelope", zorder=2,
        )
        self.ax.axhline(0.0, color="k", lw=0.8, zorder=1)
        self.ax.legend(loc="upper right", framealpha=0.92, fontsize=9)
        _autoscale(self.ax, data)

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def _build_info(self) -> None:
        info_frame = ttk.Frame(self.root, padding=(8, 8, 12, 8))
        info_frame.grid(row=0, column=1, sticky="ns")

        ttk.Label(info_frame, text="Calculated values", style="Title.TLabel").pack(anchor="w")
        self.info = tk.Text(
            info_frame, width=32, height=28, font=("Consolas", 9),
            relief="solid", borderwidth=1, state="disabled", wrap="none",
            background="#f7f7f7",
        )
        self.info.pack(fill="y", expand=True, pady=(6, 8))
        ttk.Label(
            info_frame,
            text=f"© {AUTHOR}\n{LICENSE_ID} — attribution required",
            style="Hint.TLabel",
            justify="left",
        ).pack(anchor="w")

    def _build_controls(self) -> None:
        bar = ttk.Frame(self.root, padding=(10, 8, 10, 10))
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.columnconfigure(0, weight=1)
        bar.columnconfigure(1, weight=1)

        left = ttk.LabelFrame(bar, text="Fault current", padding=8)
        left.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        right = ttk.LabelFrame(bar, text="System / time", padding=8)
        right.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        left_keys = ("I_kpp", "I_k", "xr_ratio", "dc_offset")
        right_keys = ("frequency", "T_ac_ms", "t_end_ms")
        self._add_sliders(left, left_keys)
        self._add_sliders(right, right_keys)

        btns = ttk.Frame(right)
        btns.pack(fill="x", pady=(10, 0))
        self.btn_reset = ttk.Button(btns, text="Reset", command=self.on_reset)
        self.btn_reset.pack(side="left", padx=(0, 8))
        self.btn_save = ttk.Button(btns, text="Save PNG…", command=self.on_save)
        self.btn_save.pack(side="left")
        self.btn_dc_energy = ttk.Button(
            btns, text="DC I²t", command=self.on_dc_energy
        )
        self.btn_dc_energy.pack(side="left", padx=(16, 8))
        self.dc_energy_var = tk.StringVar(value="")
        self.dc_energy_box = ttk.Entry(
            btns, textvariable=self.dc_energy_var, width=20, state="readonly"
        )
        self.dc_energy_box.pack(side="left")

        ttk.Label(
            bar,
            text=(
                "The d.c. component is the moving centre-line of the offset sinusoid.  "
                "Top / bottom envelopes = d.c. ± √2 I_ac(t).  "
                "Set I_k'' = I_k for a far-from-generator fault.  "
                f"Credit: {CREDIT_LINE}"
            ),
            style="Hint.TLabel",
            wraplength=1100,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _add_sliders(self, parent: ttk.LabelFrame, keys: tuple[str, ...]) -> None:
        lookup = {row[0]: row for row in CONTROLS}
        for i, key in enumerate(keys):
            _key, label, vmin, vmax, v0, res = lookup[key]
            row = ttk.Frame(parent)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=label, width=16, style="Title.TLabel").pack(side="left")

            var = tk.DoubleVar(value=v0)
            self.vars[key] = var
            scale = tk.Scale(
                row,
                from_=vmin,
                to=vmax,
                resolution=res,
                orient="horizontal",
                variable=var,
                showvalue=False,
                length=260,
                command=self._on_slide,
                troughcolor="#dde8f2",
                highlightthickness=0,
            )
            scale.pack(side="left", fill="x", expand=True, padx=6)

            val_lbl = ttk.Label(row, style="Value.TLabel")
            val_lbl.pack(side="left")
            self.value_labels[key] = val_lbl
            self._update_value_label(key)

    def _on_slide(self, _value: str | None = None) -> None:
        if self._updating:
            return
        for key in self.vars:
            self._update_value_label(key)
        self.refresh()

    def _update_value_label(self, key: str) -> None:
        v = self.vars[key].get()
        if key == "dc_offset":
            text = f"{v:+.2f}"
        elif key in ("T_ac_ms", "t_end_ms", "frequency"):
            text = f"{v:.1f}"
        else:
            text = f"{v:.1f}"
        self.value_labels[key].configure(text=text)

    def params_from_controls(self) -> UserParams:
        v = self.vars
        return replace(
            DEFAULTS,
            I_kpp=v["I_kpp"].get(),
            I_k=v["I_k"].get(),
            xr_ratio=max(v["xr_ratio"].get(), 0.1),
            dc_offset=v["dc_offset"].get(),
            frequency=max(v["frequency"].get(), 1.0),
            T_ac=max(v["T_ac_ms"].get(), 1.0) / 1e3,
            t_end=max(v["t_end_ms"].get(), 10.0) / 1e3,
        )

    def refresh(self) -> None:
        p = self.params_from_controls()
        data = compute(p)
        t_ms = data["t"] * 1e3
        self.line_i.set_data(t_ms, data["i_total"])
        self.line_dc.set_data(t_ms, data["i_dc"])
        self.line_top.set_data(t_ms, data["top"])
        self.line_bot.set_data(t_ms, data["bottom"])
        _autoscale(self.ax, data)

        for art in self.annotations:
            art.remove()
        self.annotations = _iec_annotations(self.ax, data)

        self.info.configure(state="normal")
        self.info.delete("1.0", "end")
        self.info.insert("1.0", _info_text(p, data))
        self.info.configure(state="disabled")

        self.canvas.draw_idle()

    def on_reset(self) -> None:
        self._updating = True
        try:
            lookup = {row[0]: row[4] for row in CONTROLS}
            for key, default in lookup.items():
                self.vars[key].set(default)
                self._update_value_label(key)
        finally:
            self._updating = False
        self.refresh()

    def on_dc_energy(self) -> None:
        """Fill the text box with DC I²t = ∫ i_dc² dt over Duration T."""
        p = self.params_from_controls()
        i2t = dc_i2t(p)
        self.dc_energy_var.set(f"{i2t:.4f} (kA)²·s")

    def save_png(self, path: str) -> None:
        self.fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")

    def on_save(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save waveform PNG",
            defaultextension=".png",
            initialdir=_output_dir(),
            initialfile="iec60909_waveform.png",
            filetypes=[("PNG image", "*.png"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.save_png(path)
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc), parent=self.root)
            return
        messagebox.showinfo("Saved", f"Saved to:\n{path}", parent=self.root)

    def on_close(self) -> None:
        self.root.quit()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    WaveformApp(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        try:
            err = tk.Tk()
            err.withdraw()
            messagebox.showerror("IEC 60909 Waveform", f"{type(exc).__name__}: {exc}")
        except Exception:
            _log(f"{type(exc).__name__}: {exc}")
        raise
