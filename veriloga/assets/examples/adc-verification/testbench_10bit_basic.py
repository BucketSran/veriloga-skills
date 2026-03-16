#!/usr/bin/env python3
"""
Basic 10-bit ADC testbench using real ADCToolbox API.

This example demonstrates:
- Coherent frequency calculation (avoiding spectral leakage)
- Sinusoid generation with configurable amplitude
- ADC quantization simulation
- Spectrum analysis with ADCToolbox.analyze_spectrum()
- Metrics extraction (ENOB, SNDR, SFDR, THD, SNR)
- Publication-quality plot generation

ADCToolbox Documentation:
  https://github.com/Arcadia-1/ADCToolbox

Usage:
    python testbench_10bit_basic.py
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Try to import ADCToolbox; provide fallback for development
try:
    from adctoolbox import find_coherent_frequency, analyze_spectrum
    ADCTOOLBOX_AVAILABLE = True
except ImportError:
    ADCTOOLBOX_AVAILABLE = False
    print("WARNING: adctoolbox not installed. Install with: pip install adctoolbox")

# Configuration
FS = 100e6           # Sampling frequency [Hz]
FIN_TARGET = 10e6    # Desired input frequency [Hz]
NSAMPLES = 4096      # Number of samples (FFT size)
NBITS = 10           # ADC resolution [bits]
VREF_MIN = 0.0       # Reference minimum [V]
VREF_MAX = 1.0       # Reference maximum [V]
AMPLITUDE = 0.49     # Sine amplitude as fraction of full scale
DC_OFFSET = 0.5      # DC offset as fraction of full scale
OUTPUT_DIR = 'results_10bit'

# ─────────────────────────────────────────────────────────────────
# Main testbench
# ─────────────────────────────────────────────────────────────────

def main():
    """Run ADC testbench with real ADCToolbox API."""

    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}/\n")

    if not ADCTOOLBOX_AVAILABLE:
        print("ERROR: ADCToolbox not available. Exiting.")
        return

    # Step 1: Find coherent frequency
    print("Step 1: Calculate coherent frequency")
    fin_actual, bin_idx = find_coherent_frequency(
        fs=FS,
        fin_target=FIN_TARGET,
        n_fft=NSAMPLES,
        force_odd=True  # J should be odd for better spectral properties
    )
    print(f"  Target fin: {FIN_TARGET / 1e6:.2f} MHz")
    print(f"  Actual fin: {fin_actual / 1e6:.6f} MHz")
    print(f"  FFT bin: {bin_idx}")

    # Step 2: Generate time-domain signal
    print("\nStep 2: Generate coherent sinusoid")
    t = np.arange(NSAMPLES) / FS
    vfull_scale = VREF_MAX - VREF_MIN
    v_amplitude = AMPLITUDE * vfull_scale
    v_dc = DC_OFFSET * vfull_scale + VREF_MIN

    v_in = v_dc + v_amplitude * np.sin(2 * np.pi * fin_actual * t)
    print(f"  Amplitude: {AMPLITUDE * 100:.1f}% of full scale")
    print(f"  Peak: {np.max(v_in):.3f} V, Min: {np.min(v_in):.3f} V")
    print(f"  DC offset: {v_dc:.3f} V")

    # Step 3: Simulate ADC quantization
    print("\nStep 3: Simulate ADC quantization")
    num_levels = 2 ** NBITS
    code_out = np.floor(
        (v_in - VREF_MIN) / vfull_scale * num_levels
    )
    code_out = np.clip(code_out, 0, num_levels - 1).astype(int)
    print(f"  Resolution: {NBITS} bits")
    print(f"  Full scale: {vfull_scale:.3f} V")
    print(f"  Output range: {np.min(code_out)} to {np.max(code_out)}")

    # Step 4: Analyze spectrum with ADCToolbox
    print("\nStep 4: Spectrum analysis with ADCToolbox.analyze_spectrum()")
    result = analyze_spectrum(
        data=code_out,
        fs=FS,
        create_plot=False,      # Suppress auto-plotting
        win_type='hann',        # Hanning window (good for ADC testing)
        max_harmonic=5          # Analyze up to 5th harmonic
    )

    # Extract metrics from result dict
    enob = result['enob']
    sndr = result['sndr_dbc']
    sfdr = result['sfdr_dbc']
    snr = result['snr_dbc']
    thd = result['thd_dbc']
    sig_pwr = result['sig_pwr_dbfs']
    nsd = result['nsd_dbfs_hz']

    print(f"  ENOB:       {enob:.2f} bits")
    print(f"  SNDR:       {sndr:.2f} dBc")
    print(f"  SFDR:       {sfdr:.2f} dBc")
    print(f"  SNR:        {snr:.2f} dBc")
    print(f"  THD:        {thd:.2f} dBc")
    print(f"  Signal Pwr: {sig_pwr:.2f} dBFS")
    print(f"  NSD:        {nsd:.2f} dBFS/Hz")

    # Step 5: Generate plots
    print("\nStep 5: Generate plots")

    # Plot 1: Input waveform (first 400 samples)
    fig, ax = plt.subplots(figsize=(12, 4))
    idx = slice(0, min(400, NSAMPLES))
    ax.plot(t[idx] * 1e9, v_in[idx], 'b-', linewidth=1)
    ax.set_xlabel('Time [ns]')
    ax.set_ylabel('Voltage [V]')
    ax.set_title('ADC Input Signal (first 400 samples)')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([t[0]*1e9, t[400]*1e9])
    plt.savefig(f'{OUTPUT_DIR}/01_input_signal.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {OUTPUT_DIR}/01_input_signal.png")

    # Plot 2: ADC output codes (first 400 samples)
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(code_out[idx], 'r-', linewidth=0.8, marker='o', markersize=2)
    ax.set_xlabel('Sample Number')
    ax.set_ylabel(f'Digital Code (0–{num_levels-1})')
    ax.set_title('ADC Output Codes (first 400 samples)')
    ax.grid(True, alpha=0.3)
    plt.savefig(f'{OUTPUT_DIR}/02_adc_codes.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {OUTPUT_DIR}/02_adc_codes.png")

    # Plot 3: Spectrum using ADCToolbox
    fig, ax = plt.subplots(figsize=(12, 5))
    _ = analyze_spectrum(
        data=code_out,
        fs=FS,
        create_plot=True,
        ax=ax,
        win_type='hann',
        max_harmonic=5
    )
    ax.set_xlim([0, FS / 2 / 1e6])
    plt.savefig(f'{OUTPUT_DIR}/03_spectrum.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {OUTPUT_DIR}/03_spectrum.png")

    # Plot 4: Code histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(code_out, bins=min(100, num_levels), color='green', alpha=0.7, edgecolor='black')
    ax.set_xlabel('Digital Code')
    ax.set_ylabel('Frequency')
    ax.set_title('ADC Output Code Distribution')
    ax.grid(True, alpha=0.3, axis='y')
    plt.savefig(f'{OUTPUT_DIR}/04_histogram.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✓ {OUTPUT_DIR}/04_histogram.png")

    # Step 6: Save metrics to file
    print("\nStep 6: Save analysis summary")
    with open(f'{OUTPUT_DIR}/metrics.txt', 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("ADC Testbench Results (10-bit ADC with Coherent Sampling)\n")
        f.write("=" * 60 + "\n\n")
        f.write("CONFIGURATION\n")
        f.write("-" * 60 + "\n")
        f.write(f"Sampling frequency:    {FS / 1e6:.1f} MHz\n")
        f.write(f"Target signal freq:    {FIN_TARGET / 1e6:.2f} MHz\n")
        f.write(f"Actual signal freq:    {fin_actual / 1e6:.6f} MHz\n")
        f.write(f"FFT bin index:         {bin_idx}\n")
        f.write(f"Number of samples:     {NSAMPLES}\n")
        f.write(f"Signal amplitude:      {AMPLITUDE * 100:.1f}% FS\n")
        f.write(f"DC offset:             {DC_OFFSET * 100:.1f}% FS\n")
        f.write(f"ADC resolution:        {NBITS} bits\n")
        f.write(f"Reference range:       {VREF_MIN:.1f}V to {VREF_MAX:.1f}V\n\n")
        f.write("RESULTS\n")
        f.write("-" * 60 + "\n")
        f.write(f"ENOB:                  {enob:.2f} bits\n")
        f.write(f"SNDR:                  {sndr:.2f} dBc\n")
        f.write(f"SFDR:                  {sfdr:.2f} dBc\n")
        f.write(f"SNR:                   {snr:.2f} dBc\n")
        f.write(f"THD:                   {thd:.2f} dBc\n")
        f.write(f"Signal Power:          {sig_pwr:.2f} dBFS\n")
        f.write(f"Noise Spectral Density: {nsd:.2f} dBFS/Hz\n\n")
        f.write("EXPECTED VALUES (Ideal 10-bit ADC)\n")
        f.write("-" * 60 + "\n")
        f.write(f"ENOB:                  ~10.0 bits\n")
        f.write(f"SNDR:                  ~62 dB\n")
        f.write(f"SNR (quantization):    ~62 dB\n")
        f.write(f"THD:                   -70 dBc to -75 dBc\n\n")
        f.write("INTERPRETATION\n")
        f.write("-" * 60 + "\n")
        if abs(enob - NBITS) < 0.5:
            f.write(f"✓ ENOB matches bit resolution (within 0.5 bits)\n")
        else:
            f.write(f"✗ ENOB deviates from {NBITS} bits by {abs(enob - NBITS):.1f} bits\n")
            f.write(f"  Check: frequency coherence, amplitude, ADC model\n")
        if sndr > 60:
            f.write(f"✓ SNDR is near ideal (>60 dB)\n")
        else:
            f.write(f"⚠ SNDR is degraded (<60 dB) — check for distortion\n")
        f.write("\n")

    print(f"  ✓ {OUTPUT_DIR}/metrics.txt")

    print("\n" + "=" * 60)
    print("✓ Testbench complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
