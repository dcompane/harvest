#!/usr/bin/env bash
# run-harvest-env.sh
# Usage: ./run-harvest-env.sh dev|test|prod

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 dev|test|prod"
  exit 1
fi

ENV="$1"

## Remember that base URLs for SaaS environments have the "-aapi" suffix in the host name
##    and that you do not need to specify the port number as it uses standard HTTPS port 443.

case "$ENV" in
  dev)
    BASE_URL="https://dev-aapi.example.com:8443/automation-api"
    API_KEY="<YOUR_DEV_API_KEY>"
    INCLUDE="deploy,config,auth"
    OUTPUT="dev_ctm_inventory"
    ;;
  test)
    BASE_URL="https://test-aapi.example.com:8444/automation-api"
    API_KEY="<YOUR_TEST_API_KEY>"
    INCLUDE="deploy,config,auth"
    OUTPUT="test_ctm_inventory"
    ;;
  prod)
    BASE_URL="https://prod-aapi.example.com:8444/automation-api"
    API_KEY="<YOUR_PROD_API_KEY>"
    INCLUDE="deploy,config,auth"
    OUTPUT="prod_ctm_inventory"
    ;;
  *)
    echo "Usage: $0 dev|test|prod"
    exit 1
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python "$SCRIPT_DIR/harvest.py" \
  --base-url "$BASE_URL" \
  --api-key "$API_KEY" \
  --include "$INCLUDE" \
  --output "$OUTPUT" \
  --debug True

echo "Finished harvesting for $ENV environment."
