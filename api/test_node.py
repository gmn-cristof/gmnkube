import requests

# 添加节点
node_data = {
    "name": "node1",
    "ip_address": "127.0.0.1",
    "total_cpu": 4,
    "total_memory": 8192,
    "total_gpu": 2,
    "total_io": 1000,
    "total_net": 1000,
    "labels": {
        "zone": "us-west",
        "environment": "production"
    },
    "annotations": {
        "description": "This is a worker node."
    }
}

response = requests.post('http://localhost:8001/nodes', json=node_data)
print(response.json())


