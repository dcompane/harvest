
# harvest

Harvest Control-M Data using the AAPI

User: generate user instructions to run harvest.py from command line with parameter documentation

GitHub Copilot: Optimized tool selectionChecking the command-line options in harvest.py and any existing README docs so I can provide accurate usage instructions.

Read [](file:///c%3A/Users/dcompane/OneDrive/git_repos/harvest/harvest.py#1-1), lines 1 to 220

Read [](file:///c%3A/Users/dcompane/OneDrive/git_repos/harvest/README.md)

## Run harvest.py from the command line

From the `harvest` repository root:

```bash
python harvest.py --base-url https://<aapi-host>:8443/automation-api --api-key "<your-api-key>"
```

---

## Required parameters

- `--base-url`

  - Control-M Automation API base URL
  - Example: `https://aapi.example.com:8443/automation-api`
- `--api-key`

  - Control-M Automation API key with appropriate permissions
  - Example: `--api-key "b25QcmVtOjMxMmY2NWZmLTI1MTEtNDY4ZC04NzdmLThmZTVlMjk2NDcwNQ=="`
  - NOTE: If the parameter is not added, it will be requested interactively.

---

## Optional parameters

- `--include`

  - Comma-separated list of datasets to include
  - Supported values: `deploy`, `config`, `auth`
  - Default: `deploy,config,auth`
- `--zos-library`

  - Optional z/OS library name to filter deploy data for z/OS environments
  - Default: none
- `--timeout`

  - HTTP request timeout in seconds
  - Default: `60`
- `--output`

  - Base name for the output Excel file
  - A timestamp suffix is appended automatically
  - Default: `controlm_inventory`
  - Output file will be written as `controlm_inventory_YYYYMMDD_HHMMSS.xlsx`
- `--server`

  - Optional Control-M server name to target
  - Can be specified multiple times
  - Example: `--server server1 --server server2`
- `--debug`

  - Enable debug mode
  - Default: `False`
- `--folderlimit`

  - Limit number of folders included in the inventory
  - NOTE: marked `NOT IMPLEMENTED` in the script

---

## Example command

```bash
python harvest.py \
  --base-url https://dc01:8444/automation-api \
  --api-key "b25QcmVtOjMxMmY2NWZmLTI1MTEtNDY4ZC04NzdmLThmZTVlMjk2NDcwNQ==" \
  --include deploy,config \
  --output controlm_inventory \
  --debug True
```

This writes an Excel workbook to the current working directory, for example:

```text
controlm_inventory_20260707_123456.xlsx
```

---

## Notes

- `Metadata` and `Config Servers` are always included.
- The tool uses current working directory for output.
- `--folderlimit` is defined but not actually implemented in harvest.py

---

## Environment runner scripts

Two helper scripts are included to run `harvest.py` against dev, test, and prod environments:

- `run-harvest-env.bat` — Windows batch script
- `run-harvest-env.sh` — Bash shell script

### Usage

Windows CMD:

```cmd
run-harvest-env.bat dev
run-harvest-env.bat test
run-harvest-env.bat prod
```

Bash:

```bash
./run-harvest-env.sh dev
./run-harvest-env.sh test
./run-harvest-env.sh prod
```

### Notes

- Update the placeholder API keys in each script before running.
- Each environment has its own `BASE_URL`, `API_KEY`, and default output prefix.
- The scripts invoke `harvest.py` from the repository directory so they work from the repo root.
