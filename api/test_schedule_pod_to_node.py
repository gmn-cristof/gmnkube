import requests

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

node_data = {
    "name": "node2",
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

# 创建 Pod
pod_data = { 
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
      "name": "example-pod",
      "namespace": "default",
      "status": "pending"
    },
    "spec": {
      "containers": [
        {
          "name": "nginx-container",
          "image": "docker.m.daocloud.io/library/nginx:latest",
          "ports": [
            {
              "containerPort": 80
            }
          ],
          "resources": {
            "requests": {
              "cpu": "100m",
              "memory": "256Mi",
              "gpu": "1"  # 添加 GPU 请求
            },
            "limits": {
              "cpu": "200m",
              "memory": "512Mi",
              "gpu": "1"  # 添加 GPU 限制
            }
          }
        },
        {
          "name": "busybox-container",
          "image": "docker.m.daocloud.io/library/busybox:latest",
          "command": ["sh", "-c", "sleep 3600"],
          "resources": {
            "requests": {
              "cpu": "50m",
              "memory": "128Mi",
              "gpu": "0"  # 添加 GPU 请求
            },
            "limits": {
              "cpu": "100m",
              "memory": "256Mi",
              "gpu": "0"  # 添加 GPU 限制
            }
          }
        }
      ],
      "volumes": [
        {
          "name": "my-pvc",
          "persistentVolumeClaim": {
            "claimName": "my-pvc"
          }
        }
      ]
    }
}


response = requests.post('http://localhost:8001/pods', json=pod_data)

pod_data ={
    "pod_name": "example-pod",
    "namespace": "default",
    "replica_count": 3
}

response = requests.post('http://localhost:8001/nodes/node1/schedule', json=pod_data)
print(response.json())