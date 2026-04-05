# EVAS-First Closed Loop (Against Spectre)

Use this method for generated Verilog-A that must be consistent between EVAS and Virtuoso/Spectre.

## Goal

Keep the workflow deterministic and actionable:

1. Treat EVAS as the primary expected behavior for fast iteration
2. Use Virtuoso/Spectre as cross-check oracle on identical stimulus
3. If mismatch appears, fix EVAS semantics first (without touching EVAS matrix-solver fundamentals)
4. If repeated EVAS fixes do not improve mismatch, re-check model code assumptions

## Ordered Workflow

### Step 1: Generate EVAS-friendly model code

For PLL/VCO/CPPLL style modules, start with:

1. Edge events: `@(cross(...))`
2. Discrete state updates in edge events or single-argument absolute-time timers such as
   `@(timer(t_next))`
3. Output shaping via `transition()`
4. No `I() <+`, no `ddt()`, no `idt()`, no `idtmod()` (unless separately justified)

For variable-period oscillator scheduling, avoid `@(timer(0.0, period))` when `period` is updated
inside the event body. Prefer an explicit `t_next = t_next + t_half` pattern so the newly computed
period controls the very next edge.

### Step 2: EVAS pre-check

Run EVAS first and require:

1. Simulation success
2. Non-degenerate waveform dynamics (not flatline, not NaN-only)
3. Basic functional intent visible (for example: toggling clocks, lock progression, bounded control)

### Step 3: Virtuoso/Spectre verification

Run the same testbench and stimulus in Spectre and compare against EVAS report.

Collect at least:

1. Key waveform RMSE (state/control/output)
2. Lock metrics (lock-time, lock flag occupancy)
3. Final frequency/phase mismatch metrics in observation window

### Step 4: Mismatch handling (EVAS-fix-first)

If mismatch exceeds threshold:

1. First modify EVAS frontend/runtime behavior only where semantics differ from Spectre expectations
2. Do not modify EVAS matrix-solver core principles for this loop
3. Re-run EVAS + Spectre on identical inputs after each EVAS fix

If mismatch does not improve after multiple EVAS-side attempts, then inspect generated model code for conceptual errors.

### Step 5: Optional idt/idtmod adoption

Enable `idt()` / `idtmod()` only if all are true:

1. EVAS run succeeds with meaningful dynamics (not flatline / not degenerate)
2. Spectre run succeeds
3. Relative improvement vs baseline is significant: at least 20% reduction on the primary mismatch metric
4. No regression on lock behavior (lock-time delta and lock detect consistency remain acceptable)

If any condition fails, keep the non-idtmod baseline.

## Suggested Numeric Thresholds

Tune per project, but start with:

1. `primary_rmse_new <= 0.8 * primary_rmse_baseline`
2. `lock_time_delta_new <= lock_time_delta_baseline + 5% * t_lock_target`
3. Both simulators must report non-empty and non-constant key outputs

## Important Caveat

If EVAS implementation status for `idt/idtmod` is changing across versions, do not rely on parse success alone.
Always verify runtime behavior (waveform is dynamic and physically plausible).
