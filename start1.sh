#!/bin/bash
export PYTHONPATH=/mnt/d/gmnkube:$PYTHONPATH
export TF_ENABLE_ONEDNN_OPTS=0
python3 tests/test_env.py

