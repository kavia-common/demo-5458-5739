#!/bin/bash
cd /home/kavia/workspace/code-generation/demo-5458-5739/BackendAPIService
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

