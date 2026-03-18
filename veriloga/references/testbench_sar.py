"""
12-bit SAR ADC behavioral model: spectrum vs ideal quantization.
"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from adctoolbox import find_coherent_frequency, analyze_spectrum

output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

N_fft  = 2048
Fs     = 100e6
Nbits  = 12
Vmin, Vmax = 0.0, 1.0


def sar_convert(v_in_array, nbits, vmin, vmax):
    """SAR successive approximation: MSB-to-LSB."""
    num_levels = 2 ** nbits
    vfsr = vmax - vmin
    codes = np.empty(len(v_in_array), dtype=int)
    for n, v in enumerate(v_in_array):
        v = np.clip(v, vmin, vmax)
        code = 0
        for bit in range(nbits - 1, -1, -1):
            test = code | (1 << bit)
            if vmin + (test / num_levels) * vfsr < v:
                code = test
        codes[n] = code
    return codes


Fin, _ = find_coherent_frequency(fs=Fs, fin_target=8e6, n_fft=N_fft)
A      = 0.40 * (Vmax - Vmin)
Vmid   = (Vmax + Vmin) / 2

t      = np.arange(N_fft) / Fs
v_in   = Vmid + A * np.sin(2 * np.pi * Fin * t)

codes_sar   = sar_convert(v_in, Nbits, Vmin, Vmax)
codes_ideal = np.clip(np.floor((v_in - Vmin) / (Vmax - Vmin) * 2**Nbits), 0, 2**Nbits - 1).astype(int)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

r_sar   = analyze_spectrum(codes_sar,   fs=Fs, ax=ax1, max_scale_range=[Vmin, Vmax], n_thd=5, show_plot=True)
r_ideal = analyze_spectrum(codes_ideal, fs=Fs, ax=ax2, max_scale_range=[Vmin, Vmax], n_thd=5, show_plot=True)

ax1.set_title(f"SAR ADC    ENOB={r_sar['enob']:.2f} b  SNDR={r_sar['sndr_db']:.2f} dB  SFDR={r_sar['sfdr_db']:.2f} dB")
ax2.set_title(f"Ideal ADC  ENOB={r_ideal['enob']:.2f} b  SNDR={r_ideal['sndr_db']:.2f} dB  SFDR={r_ideal['sfdr_db']:.2f} dB")

plt.tight_layout()
plt.savefig(output_dir / "testbench_sar.png", dpi=150)
plt.close()
print(f"SAR:   ENOB={r_sar['enob']:.2f} b  SNDR={r_sar['sndr_db']:.2f} dB  SFDR={r_sar['sfdr_db']:.2f} dB")
print(f"Ideal: ENOB={r_ideal['enob']:.2f} b  SNDR={r_ideal['sndr_db']:.2f} dB  SFDR={r_ideal['sfdr_db']:.2f} dB")
