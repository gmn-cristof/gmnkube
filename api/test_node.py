import requests

# 添加节点
node_data = {
    "name": "node1",
    "ip_address": "127.0.0.1",
    "total_cpu": 0,
    "total_memory": 0,
    "total_gpu": 0,
    "total_io": 0,
    "total_net": 0,
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


