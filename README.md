# Oxford Street Pedestrianization Analytics

## Installation & Setup

This project uses [Miniforge](https://github.com/conda-forge/miniforge) for environment management, with all packages sourced from `conda-forge`.

### Prerequisites

- [Miniforge3](https://github.com/conda-forge/miniforge#miniforge3) installed
- Git

### 1. Create the environment

```powershell
conda env create -f environment.yml
```

This creates the `spatial-analytics` environment with the following core packages:

- `geopandas`
- `osmnx`
- `cityseer`
- `momepy`
- `neatnet`
- `ipykernel`

### 2. Activate the environment

```powershell
conda activate spatial-analytics
```

### 3. Register the Jupyter kernel

```powershell
python -m ipykernel install --user --name spatial-analytics --display-name "Python (spatial-analytics)"
```

In VS Code, select **Python (spatial-analytics)** as the kernel for any notebook in this repo via **Select Kernel** (top-right of the notebook).

### Updating the environment

If `environment.yml` changes (new dependencies added):

```powershell
conda env update -f environment.yml --prune
```

To regenerate `environment.yml` after installing new packages manually:

```powershell
conda env export -n spatial-analytics --from-history > environment.yml
```

> **Note:** `--from-history` keeps the file to only explicitly requested packages, rather than pinning the full dependency tree — keeps it readable and portable across machines.