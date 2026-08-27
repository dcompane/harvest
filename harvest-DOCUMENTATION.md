# harvest — Control-M Inventory Harvester (AAPI)

**Repo:** `dcompane/harvest` · **Status:** Pre-release `0.1.2` · **License:** included · **Language:** Python 95.6% / Batch 2.7% / Shell 1.7%

Harvest extracts Control-M configuration and deployment metadata through the **Automation API (AAPI)** and writes it to a timestamped Excel workbook for inventory, audit, and governance use.

---

## 1. What it does

- Connects to a Control-M/Enterprise Manager AAPI endpoint using an admin API token.
- Pulls one or more **datasets**: `deploy`, `config`, `auth` (default: all three).
- Optionally filters **z/OS deploy data** by library name (mainframe support). (NOT IMPLEMENTED))
- Writes results to `controlm_inventory_YYYYMMDD_HHMMSS.xlsx` in the working directory.
- Ships as both a runnable Python script and a packaged Windows `harvest.exe`.

> Metadata and Config Servers are **always** included regardless of `--include`.

---

## 2. Repository layout

| File                                             | Purpose                                                    |
| ------------------------------------------------ | ---------------------------------------------------------- |
| `harvest.py`                                   | Main entry point / CLI argument handling and orchestration |
| `controlm_api.py`                              | AAPI client — authentication and REST calls to Control-M  |
| `ExcelWriter.py`                               | Formats and writes the harvested datasets to`.xlsx`      |
| `Utility.py`                                   | Shared helper functions                                    |
| `config.py`                                    | Configuration / defaults                                   |
| `api_deploy_code.py`                           | Deploy-related API helpers (initial commit)                |
| `run-harvest-env.bat` / `run-harvest-env.sh` | Environment runners (dev / test / prod)                    |
| `harvest.spec`                                 | PyInstaller spec used to build`harvest.exe`              |
| `zip-create.bat` / `zip-expand.bat`          | Packaging helpers for the distributable zip                |
| `dist/`                                        | Built distributable (`harvest.zip` / `harvest.exe`)    |
| `APIs.md`                                      | Notes on the AAPI endpoints used                           |

---

## 3. Installation

### Option A — Run the packaged executable (Windows)

```
tar -zxvf harvest.zip          # expands harvest.exe
harvest.exe --base-url https://<aapi-host>:8443/automation-api [--api-key "<key>"]
```

> Note: download the zip from the file icon on GitHub (the "Save as" right-click option will not work). Some organizations block downloading `.exe` files.

### Option B — Run from source (Linux / Windows)

Requires Python plus:

```
pip install requests urllib3 openpyxl
```

```
python harvest.py --base-url https://<aapi-host>:8443/automation-api [--api-key "<key>"]
```

---

## 4. Command-line reference

### Required

| Parameter      | Description                                                         |
| -------------- | ------------------------------------------------------------------- |
| `--base-url` | AAPI base URL, e.g.`https://aapi.example.com:8443/automation-api` |
| `--api-key`  | AAPI key with admin permissions. If omitted, prompted interactively |

### Optional

| Parameter         | Default                | Description                                            |
| ----------------- | ---------------------- | ------------------------------------------------------ |
| `--include`     | `deploy,config,auth` | Comma-separated datasets to collect                    |
| `--zos-library` | none                   | Filter deploy data to a z/OS library (mainframe)       |
| `--server`      | all                    | Target a named Control-M server; repeatable            |
| `--timeout`     | `60`                 | HTTP request timeout (seconds)                         |
| `--output`      | `controlm_inventory` | Base name for the Excel file (timestamp appended)      |
| `--debug`       | `False`              | Enable debug logging                                   |
| `--folderlimit` | —                     | Defined but**NOT implemented** as of last commit |

### Example

```
python harvest.py \
  --base-url https://dc01:8444/automation-api \
  --api-key "b25QcmVtOjMxMmY2NWZmL...NzA1==" \
  --output controlm_inventory
# -> controlm_inventory_20260707_123456.xlsx
```

---

## 5. Environment runners

`run-harvest-env.bat` (Windows) and `run-harvest-env.sh` (Bash) wrap the script for `dev` / `test` / `prod`:

```
run-harvest-env.bat prod
./run-harvest-env.sh prod
```

Each environment carries its own `BASE_URL`, `API_KEY`, and output prefix.

> Update the placeholder API keys before running. Scripts run from the repo root; can be re-pointed at `harvest.exe`.

---

## 6. Security & operational notes

- Requires a **full admin AAPI token** — treat as a privileged credential.
- **Interactive prompting (recommended):** if `--api-key` is omitted, the token is requested at runtime and lives only in memory for that session — no key in command history, scripts, or files at rest. This is the preferred mode for regulated / shared environments.
- Only the bundled **runner scripts** (`run-harvest-env.bat/.sh`) store keys in plaintext. For unattended / scheduled runs, source the token from an env var or secret store instead of embedding it. For ad-hoc runs, prefer interactive prompting.
- `--folderlimit` is a no-op today; there is currently no throttle on inventory size.
- Excel output is subject to the ~1,048,576-row-per-sheet limit of `.xlsx`.
- Single contributor, pre-release; no published releases, tests, or CI as of `0.1.2`.
