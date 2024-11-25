#!/bin/bash
export PYTHONPATH=/mnt/d/gmnkube:$PYTHONPATH
export TF_ENABLE_ONEDNN_OPTS=0
python3 tests/test_env.py
curl -X GET http://localhost:8001/DDQN_schedule_history


