#!/bin/bash

_SETVARS_DIR="$(cd "$(dirname "${BASH_SOURCE:-$0}")" && pwd)"
export PYTHONPATH="$(cd "${_SETVARS_DIR}/../.." && pwd):${_SETVARS_DIR}:$PYTHONPATH"
export IMPACTX_REFP_EXTENSION=.0
