# Advanced Verilog-A Syntax Reference

Specialized constructs for less common use cases. See `SKILL.md` for common patterns.

---

## String Operations

### String parameters — `.len()` / `.substr()`

Parse string parameters into configuration arrays.

```verilog
parameter string config = "10110";
integer conf_list[4:0];

@(initial_step) begin
    for (i = 0; i < config.len(); i = i + 1)
        conf_list[i] = (config.substr(i, i) == "1");
end
```

---

## Advanced Macro Usage

### Parameterized `` `define ``

Create macro functions for repeated patterns (e.g., mismatch generation).

```verilog
`define FRAC_MM(I) (1.0 + mismatch * abs($random(I) / `MAXINT))

@(initial_step) begin
    ch_gain[0] = `FRAC_MM(seed0);
    ch_gain[1] = `FRAC_MM(seed1);
end

`undef FRAC_MM
```

---

## Conditional Compilation

### `` `ifdef `` — conditional compilation

Enable/disable code blocks based on compile-time definitions.

```verilog
`ifdef __VAMS_ENABLE__
    iin = I(<vin>);
`else
    iin = I(vin, vin);
`endif
```

---

## Current-Domain Functions (Advanced)

These are primarily for **current-domain** ADCs and analog circuits. See `SKILL.md` § Domain Classification.

### `$vt` / `$temperature` — thermal voltage

Thermal voltage constant (≈25.86 mV @ 300K) and temperature variable.

```verilog
I(a, c) <+ is * (limexp(V(a, c) / $vt) - 1);  // Diode equation
```

### `limexp()` — convergence-safe exponential

Prevents numerical overflow in exponential functions (e.g., diode models).

```verilog
I(a, c) <+ is * (limexp(V(a, c) / $vt) - 1);
```

### `slew()` — rate limiter

Limits the rate of change of a signal (e.g., amplifier slew rate).

```verilog
V(out) <+ slew(V(in), max_slope, -max_slope);
```

### `branch` — named branch

Define explicitly named branches for current calculations.

```verilog
branch (IN, OUT) sw;
I(IN, OUT) <+ V(sw) * transition(cond, 0, 10p);
```

---

## Periodic Sampling & Event Timing

### `@(timer())` — periodic event

Sample or log at fixed time intervals.

```verilog
real next_sample;

@(initial_step) begin
    next_sample = 0;
end

@(timer(next_sample)) begin
    val = V(sig);
    next_sample = next_sample + t_sample;
end
```

---

## Signal Edge Detection & History

### `last_crossing()` — time of last crossing

Find the time of the most recent signal crossing.

```verilog
t_cross = last_crossing(V(sig) - vth, +1);  // Last rising edge
```

---

## Analysis-Specific Constructs

### `analysis()` — test analysis type

Conditionally execute code based on the active analysis (DC, AC, transient).

```verilog
if (analysis("ac")) begin
    V(out) <+ gain * V(in);
end else if (analysis("dc")) begin
    V(out) <+ V(in);  // passthrough
end
```

### `exclude` — parameter range exclusion

Restrict valid parameter ranges (exclude specific values).

```verilog
parameter real gain = 1.0 from (-inf:inf) exclude 0;  // Gain cannot be zero
```

---

## Custom Disciplines & Natures (Experimental)

### `nature` — custom physical quantity

Define new physical quantities beyond voltage and current (rarely used).

```verilog
nature Position
    units = "m";
    access = Pos;
    abstol = 1u;
endnature
```

---

## Current-Type Outputs

### `current` type / `I()` single-node

Output port that sources/sinks current (current-domain modules).

```verilog
output current iout;

analog begin
    I(iout) <+ gm * V(vin);
end
```

---

## Related Documents

- `SKILL.md` — Core rules and common syntax
- `references/categories/` — Circuit-specific patterns
- `references/domain-routing.md` — Domain classification guidance
