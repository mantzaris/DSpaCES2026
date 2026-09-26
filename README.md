# DSpaCES 2026 research papers

Each paper lives in its own project directory. Git history and the `main` branch
are shared at this repository root.

| Project | Paper and files |
|---|---|
| [regional-energy-twin](regional-energy-twin/) | **From Detail to Decisions in Regional Energy Twins** - [PDF](regional-energy-twin/manuscript/regional_twin_study.pdf), [project README](regional-energy-twin/README.md), [build instructions](regional-energy-twin/manuscript/README.md) |

Create a new paper as a sibling of `regional-energy-twin/`, with its own source,
manuscript, configuration, results and data-access rules. The existing project's
held-out outcomes, resource limits and disabled study entry points remain intact.

## Compile the regional energy paper

From this repository root:

```bash
cd regional-energy-twin
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error manuscript/regional_twin_study.tex
```

To regenerate its figures, tables and document checks from saved outputs, use
the full build command in the [paper's build README](regional-energy-twin/manuscript/README.md).
The output is `regional-energy-twin/manuscript/regional_twin_study.pdf`.
Local datasets, dependencies and caches also live inside that project's directory
and remain excluded from git.
