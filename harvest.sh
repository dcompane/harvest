#! /bin/bash 

set -x

clear

python harvest.py \
  --base-url https://dc01:8444/automation-api \
  --include config \
  --api-key b25QcmVtOjMxMmY2NWZmLTI1MTEtNDY4ZC04NzdmLThmZTVlMjk2NDcwNQ== \
  --output prod_ctm_inventory.xlsx \
  --timeout 120 \
  --server dc01 \
  --debug True

