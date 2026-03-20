# Requirements

This repository has one core writing skill and two optional local-verification paths.

## Required

### `veriloga`

No external dependencies.

`veriloga` is a documentation/reference skill for writing Verilog-A behavioral models. An agent can
use it directly by reading the files in this repository.

## Optional Local Verification

Local verification is optional. The required tools depend on the modeling style used in the `.va`
module.

### Voltage-Domain Verification: EVAS

Use this path for modules built around voltage-domain behavioral constructs such as:

- `V() <+`
- `@(cross(...))`
- `transition()`

Typical examples:

- SAR logic
- DFF / digital state machines
- counters
- simple comparators
- data generators

Requirements:

- `uv`
- `evas-sim`

Install:

```bash
uv tool install evas-sim
```

See:

- `evas-sim/SKILL.md`

### Current-Domain Verification: OpenVAF + ngspice

Use this path for modules that rely on analog solver constructs such as:

- `I() <+`
- `ddt()`
- `idt()`
- `idtmod()`
- `laplace_nd()`

Typical examples:

- opamps
- RLC networks
- VCO cores
- filters
- LDO-style analog blocks

Requirements:

- OpenVAF
- ngspice with OSDI support
- On Windows, Visual C++ Build Tools may also be required

See:

- `openvaf/references/install.md`
- `openvaf/SKILL.md`

## Notes

- Most users only need `veriloga`.
- Install verification tooling only if you want to simulate locally.
- If a module mixes voltage-domain and current-domain constructs, split it into smaller modules
  before choosing a verification path.
- Project-level skill installation is the default recommended setup; see `README.md`.
