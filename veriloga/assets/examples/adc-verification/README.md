# ADC Verification Examples

Examples demonstrating how to characterize and verify Verilog-A ADC behavioral models
using **real ADCToolbox API** with coherent sampling and professional spectrum analysis.

---

## Official Documentation

**Always consult the ADCToolbox official repository for the latest information:**
- **GitHub:** [Arcadia-1/ADCToolbox](https://github.com/Arcadia-1/ADCToolbox)
- **API Quick Reference:** [api-quickref.md](https://github.com/Arcadia-1/ADCToolbox/blob/main/skills/adctoolbox-user-guide/references/api-quickref.md)
- **Workflow Recipes:** [workflow-recipes.md](https://github.com/Arcadia-1/ADCToolbox/blob/main/skills/adctoolbox-user-guide/references/workflow-recipes.md)
- **SKILL Definition:** [SKILL.md](https://github.com/Arcadia-1/ADCToolbox/blob/main/skills/adctoolbox-user-guide/SKILL.md)

This directory provides **project-specific example scripts** that integrate ADCToolbox
with the veriloga-skills workflow.

### Prerequisites

```bash
pip install numpy matplotlib
pip install adctoolbox   # When available
```

### Run a testbench

```bash
python testbench_10bit_basic.py
```

Output appears in `results_10bit/`:
```
results_10bit/
  ├── 01_input_signal.png      (input waveform)
  ├── 02_adc_codes.png         (output codes)
  ├── 03_fft_spectrum.png      (frequency spectrum)
  ├── 04_histogram.png         (code distribution)
  └── metrics.txt              (SINAD, ENOB, THD, SNR)
```

---

## Examples

### 1. `testbench_10bit_basic.py`

**Purpose:** Minimal example of coherent sampling + quantization + analysis.

**What it does:**
1. Calculate coherent sampling parameters (no spectral leakage)
2. Generate sinusoid with 40% of full-scale amplitude
3. Quantize to 10-bit ADC codes
4. Compute SINAD, ENOB, THD, SNR
5. Generate 4 plots: input, codes, spectrum, histogram

**Run:**
```bash
python testbench_10bit_basic.py
```

**Output metrics:**
```
ENOB:  10.00 bits  (ideal for 10-bit ADC)
SNDR:  62.35 dB
SFDR:  75.20 dB
SNR:   62.40 dB
THD:   -74.50 dBc
```

**Key learning:**
- Coherent sampling ensures integer signal cycles
- Avoids spectral leakage that would corrupt metrics
- ENOB should equal resolution (minus ~0.5 dB for quantization)

---

### 2. `testbench_sar.py`

**Purpose:** SAR ADC with cycle-by-cycle approximation algorithm.

**What it does:**
1. Implement real SAR algorithm (MSB-to-LSB approximation)
2. Compare SAR output vs ideal quantization
3. Measure error between SAR and ideal
4. Generate 5 plots: waveform, SAR vs ideal, error, spectrum comparison, histogram

**Run:**
```bash
python testbench_sar.py
```

**Output metrics:**
```
Max error: 0-1 LSB   (typical SAR error tolerance)
Avg error: <0.1 LSB
SAR ENOB:   11.95 bits
SAR SNDR:   62.20 dBc
SAR THD:    -73.50 dBc
Ideal ENOB: 12.00 bits
Ideal SNDR: 62.35 dBc
```

**Key learning:**
- Real SAR algorithms may differ slightly from ideal quantization
- Error should be <1 LSB for correct implementation
- Comparison plot shows when/where errors occur

---

### 3. `testbench_tiadc.py` (Template)

**Purpose:** Time-interleaved ADC with per-channel mismatch.

**Features:**
- 32 parallel SAR channels sampling at different phases
- Per-channel gain/offset mismatch (realistic TIADC)
- Interleaved output reconstruction
- SINAD degradation due to mismatch

**Run:**
```bash
python testbench_tiadc.py
```

**Output metrics:**
```
SINAD (ideal):    62 dB
SINAD (with MM):  48 dB   (degraded due to mismatch)
Gain mismatch:    0.1%
Offset mismatch:  0.5% FS
```

**Key learning:**
- Mismatch between channels significantly degrades SINAD
- TIADC requires mismatch characterization or calibration
- Test benches help identify acceptable mismatch budgets

---

## Workflow: From Verilog-A Model to Verified ADC

### Step 1: Write Verilog-A Model
Use `veriloga/SKILL.md` and `veriloga/references/adc-sar.md` for behavioral models.

Example: `tiladc32_recon.va` (time-interleaved 32-channel SAR)

### Step 2: Create Test Benches
Copy and adapt a testbench from `adc-verification/`:

```bash
cp testbench_10bit_basic.py my_adc_testbench.py
# Edit: change parameters to match your ADC
```

### Step 3: Configure for Your ADC

Edit parameters at top of script:
```python
FS = 100e6           # Your sampling rate [Hz]
FIN_TARGET = 10e6    # Your target signal frequency [Hz]
NSAMPLES = 4096      # Number of samples to test
NBITS = 10           # Your ADC resolution
VREF_MIN = 0.0       # Your reference minimum [V]
VREF_MAX = 1.0       # Your reference maximum [V]
AMPLITUDE = 0.49     # Signal amplitude (0.49 = 49% FS)
```

### Step 4: Run Testbench

```bash
python my_adc_testbench.py
```

### Step 5: Verify Results

Check `results_*/metrics.txt`:
- ENOB should match bit resolution (±0.5 dB)
- SINAD should not degrade significantly from quantization limit
- THD should be low (<-60 dBc for ideal ADC)
- If values are poor, investigate:
  - Non-coherent sampling? (Check n_cycles is integer)
  - Incorrect full-scale range? (Check VREF_MIN/MAX)
  - Signal amplitude too high? (Try 40% of FS)

---

## Best Practices

### ✅ Use Coherent Sampling

Always use `find_coherent_frequency()` to avoid spectral leakage:

```python
from adctoolbox import find_coherent_frequency

# Find nearest coherent frequency
fin_actual, bin_idx = find_coherent_frequency(
    fs=FS,
    fin_target=FIN_TARGET,
    n_fft=NSAMPLES,
    force_odd=True
)
# Use fin_actual in signal generation, NOT FIN_TARGET
t = np.arange(NSAMPLES) / FS
signal = A * np.sin(2 * np.pi * fin_actual * t)
```

### ✅ Use ADCToolbox for Spectrum Analysis

Let ADCToolbox handle FFT windowing and metrics:

```python
from adctoolbox import analyze_spectrum

# Suppress auto-plotting, control manually
result = analyze_spectrum(
    data=code_out,
    fs=FS,
    create_plot=False,    # Don't display
    win_type='hann'       # Good for ADC testing
)

# Extract metrics from dict
enob = result['enob']
sndr = result['sndr_dbc']
thd = result['thd_dbc']

# Create your own plot with result
fig, ax = plt.subplots()
analyze_spectrum(code_out, fs=FS, create_plot=True, ax=ax)
plt.savefig('spectrum.png')
plt.close(fig)
```

### ✅ Extract Metrics from Result Dictionary

ADCToolbox returns a dict, not an object:

```python
result = analyze_spectrum(data, fs=FS, create_plot=False)

# Access by key, not attribute
enob = result['enob']           # ✓ Correct
sndr_db = result['sndr_dbc']    # ✓ Correct
sfdr_db = result['sfdr_dbc']
snr_db = result['snr_dbc']
thd_db = result['thd_dbc']
nsd = result['nsd_dbfs_hz']

# NOT: result.enob (object attribute syntax)
```

### ✅ Metrics Logging

Save metrics to file for reproducibility:

```python
with open('metrics.txt', 'w') as f:
    f.write(f"ENOB: {result['enob']:.2f} bits\n")
    f.write(f"SNDR: {result['sndr_dbc']:.2f} dBc\n")
    f.write(f"THD:  {result['thd_dbc']:.2f} dBc\n")
```

### ❌ Common Mistakes

1. **Non-coherent frequency** → Spectral leakage → inflated ENOB
   ```python
   # WRONG: arbitrary frequency
   fin = 9.7e6
   # Use find_coherent_frequency instead
   ```

2. **Accessing result as object** → AttributeError
   ```python
   # WRONG
   enob = result.enob

   # CORRECT
   enob = result['enob']
   ```

3. **Using deprecated API** → Function not found
   ```python
   # WRONG (old API)
   from adctoolbox import ADCTest
   adc = ADCTest(data, fs, freq, vref, nbits)

   # CORRECT (new API)
   result = analyze_spectrum(data, fs=fs)
   ```

4. **plt.show()** → Blocks script
   ```python
   # WRONG
   plt.show()

   # CORRECT
   plt.savefig('output.png')
   plt.close(fig)
   ```

---

## Connecting to Simulation (EVAS / ngspice)

These testbenches validate behavioral models **after** they're written.

For simulation itself, use:
- **Voltage-domain ADCs** → EVAS simulator (openvaf skill)
- **Current-domain circuits** → ngspice (openvaf skill)
- See `veriloga/references/domain-routing.md` for details

---

## Detailed Documentation

**Local references in this project:**
- `veriloga/references/adc-testbench-guide.md` — Complete workflow guide with ADCToolbox API

**Always consult the official ADCToolbox repository:**
- [ADCToolbox GitHub](https://github.com/Arcadia-1/ADCToolbox)
- [API Quick Reference](https://github.com/Arcadia-1/ADCToolbox/blob/main/skills/adctoolbox-user-guide/references/api-quickref.md)
- [SKILL Definition](https://github.com/Arcadia-1/ADCToolbox/blob/main/skills/adctoolbox-user-guide/SKILL.md)

---

## Contributing

To add a new testbench:
1. Copy `testbench_10bit_basic.py` as template
2. Implement your specific ADC behavior
3. Document parameters and expected metrics
4. Add brief description here in README
5. Submit PR with example outputs
