# Container Engine

This project is a Python-based container control engine built on top of containerd. It includes container management, orchestration, and API interfaces, and supports optional Kubernetes compatibility.

## Features
- Container creation and deletion
- Image handling (pull, list)
- Resource scheduling
- REST API
- Kubernetes compatibility (optional)

## Installation
1. Install dependencies: `pip install -r requirements.txt`
2. Configure settings in `config/config.yaml`
3. Run API server: `python api/api_server.py`

## Usage
- API for managing containers and images
- Scheduler for efficient resource management

## Develop Environment
- visual studio code (remote connected with wsl Ubuntu)
- WSl Ubuntu 23.04
- python 3.11
- gcc g++ 13.1.0
- 
