import requests
# 创建 Pod
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
          "image": "nginx:latest",
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
          "image": "busybox",
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
print(response.json())