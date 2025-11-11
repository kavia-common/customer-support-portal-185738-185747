#!/bin/bash
cd /home/kavia/workspace/code-generation/customer-support-portal-185738-185747/customer_service_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

