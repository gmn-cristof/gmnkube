#!/bin/bash
export PYTHONPATH=/mnt/d/gmnkube:$PYTHONPATH
export TF_ENABLE_ONEDNN_OPTS=0
python3 api/api_server_master.py
