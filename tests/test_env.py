import requests
import random
import time

BASE_URL = "http://localhost:8001"
NODE_COUNT = 10
POD_COUNT = 25

IMAGES = [
    "docker.m.daocloud.io/library/nginx:latest",
    "docker.m.daocloud.io/library/busybox:latest",
    "docker.m.daocloud.io/library/alpine:latest",
    "docker.m.daocloud.io/library/tomcat:latest"
]

# 创建节点
for i in range(1, NODE_COUNT + 1):
    node_data = {
        "name": f"node{i}",
        "ip_address": f"192.168.1.{i}",
        "total_cpu": random.choice([  4, 8]),
        "total_memory": random.choice([ 4, 8]) * 1024 * 1024 * 1024,
        "total_gpu": random.choice([ 2, 4]),
        "labels": {
            "zone": random.choice(["us-west", "us-east", "eu-central"]),
            "environment": random.choice(["production", "development"])
        },
        "annotations": {
            "description": f"This is worker node {i}."
        }
    }
    response = requests.post(f"{BASE_URL}/nodes", json=node_data)
    print(f"Node {i} creation status: {response.status_code}")

time.sleep(1)

# 创建 Pods 并进行调度
for j in range(1, POD_COUNT + 1):
    # 随机生成 1 到 3 个容器
    container_count = random.randint(1, 3)
    containers = [
        {
            "name": f"container-{j}-{k}",
            "image": random.choice(IMAGES),
            "ports": [{"containerPort": random.choice([80, 8080, 443])}],
            "resources": {
                "requests": {
                    "cpu": f"{random.choice([100, 200, 500])}m",
                    "memory": f"{random.choice([128, 256, 512])}Mi",
                    "gpu": f"{random.choice([0, 0, 0, 0, 1])}"
                },
                "limits": {
                    "cpu": f"{random.choice([500, 1000])}m",
                    "memory": f"{random.choice([536, 1024])}Mi",
                    "gpu": "1"
                }
            }
        }
        for k in range(1, container_count + 1)
    ]
    
    pod_data = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": f"example-pod-{j}",
            "namespace": "default",
            "status": "pending"
        },
        "spec": {
            "containers": containers,
            "volumes": [
                {
                    "name": "my-pvc",
                    "persistentVolumeClaim": {"claimName": "my-pvc"}
                }
            ]
        }
    }
    response = requests.post(f"{BASE_URL}/pods", json=pod_data)
    print(f"Pod {j} creation status: {response.status_code}")
    time.sleep(1)

    schedule_data = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": f"example-pod-{j}",
            "namespace": "default",
            "status": "pending"
        }
    }
    response = requests.post(f"{BASE_URL}/DDQN_schedule", json=schedule_data)
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "No message provided")
        print(f"Pod {j} scheduling status: {response.status_code}, Message: {message}")
    else:
        try:
            error_details = response.json()
        except ValueError:
            error_details = response.text
        print(f"Pod {j} scheduling failed with status code {response.status_code}: {error_details}")
