#!/usr/bin/env python3
"""
SAR ADC testbench with real ADCToolbox API.

Demonstrates:
- SAR approximation algorithm (MSB-to-LSB)
- Comparison vs ideal quantization
- Spectrum analysis with ADCToolbox
- Error characterization

Usage:
    python testbench_sar.py
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

try:
    from adctoolbox import find_coherent_frequency, analyze_spectrum
    ADCTOOLBOX_AVAILABLE = True
except ImportError:
    ADCTOOLBOX_AVAILABLE = False

# Configuration
FS = 100e6           # Sampling frequency [Hz]
FIN_TARGET = 8e6     # Desired input frequency [Hz]
NSAMPLES = 2048      # Number of samples (FFT size)
NBITS = 12           # SAR ADC resolution [bits]
VREF_MIN = 0.0       # Reference minimum [V]
VREF_MAX = 1.0       # Reference maximum [V]
AMPLITUDE = 0.40     # Sine amplitude (40% of FS to avoid clipping)
OUTPUT_DIR = 'results_sar'

# ─────────────────────────────────────────────────────────────────
# SAR ADC Behavioral Model
# ─────────────────────────────────────────────────────────────────

class SARConverter:
    """
    Behavioral model of a SAR (Successive Approximation Register) ADC.

    Algorithm (MSB-to-LSB approximation):
    1. Sample input voltage Vin
    2. For bit = MSB downto LSB:
       a. Set test bit = 1 in DAC register
       b. Evaluate Vdac = DAC(register)
       c. If Vdac > Vin: clear test bit
       d. Else: keep test bit
    3. Final code is in register
    """

    def __init__(self, nbits, vref_min=0.0, vref_max=1.0):
        self.nbits = nbits
        self.vref_min = vref_min
        self.vref_max = vref_max
        self.vfull_scale = vref_max - vref_min
        self.num_levels = 2 ** nbits

    def convert(self, v_in):
        """Convert analog voltage to digital code using SAR algorithm."""
        v_in = np.clip(v_in, self.vref_min, self.vref_max)
        code = 0

        # MSB-to-LSB approximation
        for bit in range(self.nbits - 1, -1, -1):
            test_code = code | (1 << bit)
            v_dac = self.vref_min + (test_code / self.num_levels) * self.vfull_scale

            if v_dac < v_in:
                code = test_code

        return code

    def batch_convert(self, v_in_array):
        """Vectorized SAR conversion."""
        return np.array([self.convert(v) for v in v_in_array], dtype=int)


# ─────────────────────────────────────────────────────────────────
# Main testbench
# ─────────────────────────────────────────────────────────────────

def main():
    """Run SAR ADC testbench."""

    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}/\n")

    if not ADCTOOLBOX_AVAILABLE:
        print("ERROR: ADCToolbox not available. Exiting.")
        return

    # Step 1: Find coherent frequency
    print("Step 1: Find coherent frequency")
    fin_actual, bin_idx = find_coherent_frequency(
        fs=FS,
        fin_target=FIN_TARGET,
        n_fft=NSAMPLES,
        force_odd=True
    )
    print(f"  Target fin: {FIN_TARGET / 1e6:.2f} MHz")
    print(f"  Actual fin: {fin_actual / 1e6:.6f} MHz")
    print(f"  FFT bin: {bin_idx}")

    # Step 2: Generate input signal
    print("\nStep 2: Generate test signal")
    t = np.arange(NSAMPLES) / FS
    vfull_scale = VREF_MAX - VREF_MIN
    v_mid = (VREF_MAX + VREF_MIN) / 2.0
    v_amplitude = AMPLITUDE * vfull_scale
    v_in = v_mid + v_amplitude * np.sin(2 * np.pi * fin_actual * t)
    print(f"  Amplitude: {AMPLITUDE * 100:.1f}% FS")
    print(f"  Peak: {np.max(v_in):.3f} V, Min: {np.min(v_in):.3f} V")

    # Step 3: Run SAR conversion
    print("\nStep 3: SAR ADC conversion")
    sar = SARConverter(nbits=NBITS, vref_min=VREF_MIN, vref_max=VREF_MAX)
    code_sar = sar.batch_convert(v_in)
    print(f"  ADC bits: {NBITS}")
    print(f"  Output range: {np.min(code_sar)} to {np.max(code_sar)}")

    # Step 4: Compare with ideal quantization
    print("\nStep 4: Compare SAR vs Ideal quantization")
    num_levels = 2 ** NBITS
    code_ideal = np.floor((v_in - VREF_MIN) / vfull_scale * num_levels)
    code_ideal = np.clip(code_ideal, 0, num_levels - 1).astype(int)
    code_diff = code_sar - code_ideal
    max_diff = np.max(np.abs(code_diff))
    avg_diff = np.mean(np.abs(code_diff))
    print(f"  Max error: {max_diff} LSB")
    print(f"  Avg error: {avg_diff:.3f} LSB")

    # Step 5: Analyze spectrum
    print("\nStep 5: Spectrum analysis")
    result_sar = analyze_spectrum(
        data=code_sar,
        fs=FS,
        create_plot=False,
        win_type='hann',
        max_harmonic=5
    )
    result_ideal = analyze_spectrum(
        data=code_ideal,
        fs=FS,
        create_plot=False,
        win_type='hann',
        max_harmonic=5
    )

    print(f"  SAR ENOB:    {result_sar['enob']:.2f} bits")
    print(f"  SAR SNDR:    {result_sar['sndr_dbc']:.2f} dBc")
    print(f"  SAR THD:     {result_sar['thd_dbc']:.2f} dBc")
    print(f"  Ideal ENOB:  {result_ideal['enob']:.2f} bits")
    print(f"  Ideal SNDR:  {result_ideal['sndr_dbc']:.2f} dBc")
    print(f"  Ideal THD:   {result_ideal['thd_dbc']:.2f} dBc")

    # Step 6: Generate plots
    print("\nStep 6: Generate plots")

    # Plot 1: SAR vs Ideal waveforms
    fig, ax = plt.subplots(figsize=(14, 5))
    idx = slice(0, min(300, NSAMPLES))
    ax.plot(t[idx] * 1e9, v_in[idx], 'b-', linewidth=1.5, label='Input signal', alpha=0.8)
    v_sar_analog = VREF_MIN + code_sar[idx] / num_levels * vfull_scale
    ax.plot(t[idx] * 1e9, v_sar_analog, 'r.', markersize=5, label='SAR output', alpha=0.7)
    ax.set_xlabel('Time [ns]')
    ax.set_ylabel('Voltage [V]')
    ax.set_title('SAR ADC: Input Signal and Output (first 300 samples)')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    plt.savefig(f'{OUTPUT_DIR}/01_sar_waveform.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {OUTPUT_DIR}/01_sar_waveform.png")

    # Plot 2: SAR vs Ideal codes
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(code_sar[idx], 'r-', linewidth=0.8, marker='o', markersize=2, label='SAR', alpha=0.8)
    ax.plot(code_ideal[idx], 'g--', linewidth=0.8, marker='x', markersize=2, label='Ideal', alpha=0.8)
    ax.set_xlabel('Sample Number')
    ax.set_ylabel('Digital Code')
    ax.set_title('SAR vs Ideal Quantization (first 300 samples)')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    plt.savefig(f'{OUTPUT_DIR}/02_sar_vs_ideal.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {OUTPUT_DIR}/02_sar_vs_ideal.png")

    # Plot 3: Quantization error
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(code_diff[idx], 'purple', linewidth=0.8, marker='o', markersize=2)
    ax.axhline(0, color='k', linestyle='--', linewidth=0.5)
    ax.set_xlabel('Sample Number')
    ax.set_ylabel('Error (SAR - Ideal) [LSB]')
    ax.set_title('SAR Quantization Error (first 300 samples)')
    ax.grid(True, alpha=0.3)
    plt.savefig(f'{OUTPUT_DIR}/03_error.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {OUTPUT_DIR}/03_error.png")

    # Plot 4: Spectrum comparison
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    _ = analyze_spectrum(code_sar, fs=FS, create_plot=True, ax=ax1,
                        win_type='hann', max_harmonic=5)
    ax1.set_title('SAR ADC Spectrum')
    ax1.set_xlim([0, FS / 2 / 1e6])
    _ = analyze_spectrum(code_ideal, fs=FS, create_plot=True, ax=ax2,
                        win_type='hann', max_harmonic=5)
    ax2.set_title('Ideal ADC Spectrum')
    ax2.set_xlim([0, FS / 2 / 1e6])
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/04_spectrum_comparison.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {OUTPUT_DIR}/04_spectrum_comparison.png")

    # Plot 5: Code histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    bins = min(100, num_levels)
    ax.hist(code_sar, bins=bins, color='orange', alpha=0.7, edgecolor='black', label='SAR')
    ax.hist(code_ideal, bins=bins, color='green', alpha=0.4, edgecolor='black', label='Ideal')
    ax.set_xlabel('Digital Code')
    ax.set_ylabel('Frequency')
    ax.set_title('Code Distribution: SAR vs Ideal')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    plt.savefig(f'{OUTPUT_DIR}/05_histogram.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {OUTPUT_DIR}/05_histogram.png")

    # Step 7: Save metrics
    print("\nStep 7: Save analysis summary")
    with open(f'{OUTPUT_DIR}/metrics.txt', 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("SAR ADC Testbench Results\n")
        f.write("=" * 60 + "\n\n")
        f.write("CONFIGURATION\n")
        f.write("-" * 60 + "\n")
        f.write(f"Sampling frequency:    {FS / 1e6:.1f} MHz\n")
        f.write(f"Signal frequency:      {fin_actual / 1e6:.6f} MHz\n")
        f.write(f"Number of samples:     {NSAMPLES}\n")
        f.write(f"Signal amplitude:      {AMPLITUDE * 100:.1f}% FS\n")
        f.write(f"ADC resolution:        {NBITS} bits\n")
        f.write(f"Reference range:       {VREF_MIN:.1f}V to {VREF_MAX:.1f}V\n\n")
        f.write("ALGORITHM ACCURACY\n")
        f.write("-" * 60 + "\n")
        f.write(f"Max error (SAR vs Ideal): {max_diff} LSB\n")
        f.write(f"Avg error (SAR vs Ideal): {avg_diff:.3f} LSB\n")
        f.write(f"Ideal tolerance:         <1 LSB\n\n")
        f.write("SPECTRUM ANALYSIS\n")
        f.write("-" * 60 + "\n")
        f.write("SAR ADC:\n")
        f.write(f"  ENOB:  {result_sar['enob']:.2f} bits\n")
        f.write(f"  SNDR:  {result_sar['sndr_dbc']:.2f} dBc\n")
        f.write(f"  SFDR:  {result_sar['sfdr_dbc']:.2f} dBc\n")
        f.write(f"  SNR:   {result_sar['snr_dbc']:.2f} dBc\n")
        f.write(f"  THD:   {result_sar['thd_dbc']:.2f} dBc\n")
        f.write("\nIdeal ADC:\n")
        f.write(f"  ENOB:  {result_ideal['enob']:.2f} bits\n")
        f.write(f"  SNDR:  {result_ideal['sndr_dbc']:.2f} dBc\n")
        f.write(f"  SFDR:  {result_ideal['sfdr_dbc']:.2f} dBc\n")
        f.write(f"  SNR:   {result_ideal['snr_dbc']:.2f} dBc\n")
        f.write(f"  THD:   {result_ideal['thd_dbc']:.2f} dBc\n\n")
        f.write("INTERPRETATION\n")
        f.write("-" * 60 + "\n")
        if max_diff <= 1:
            f.write("✓ SAR algorithm matches ideal quantization (error ≤ 1 LSB)\n")
        else:
            f.write(f"✗ SAR algorithm deviates significantly (error = {max_diff} LSB)\n")
            f.write("  Check: algorithm implementation, floating-point precision\n")
        f.write("\n")

    print(f"  ✓ {OUTPUT_DIR}/metrics.txt")

    print("\n" + "=" * 60)
    print("✓ SAR ADC testbench complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
