import requests
import random
import time

BASE_URL = "http://localhost:8001"
NODE_COUNT = 10
POD_COUNT = 25
SCHEDULE_METHOD = "kube_schedule"

IMAGES = [
    "docker.m.daocloud.io/library/nginx:latest",
    "docker.m.daocloud.io/library/busybox:latest",
    "docker.m.daocloud.io/library/alpine:latest",
    "docker.m.daocloud.io/library/tomcat:latest"
]

class SystemTester:
    def __init__(self, base_url=BASE_URL, node_count=NODE_COUNT, pod_count=POD_COUNT, schedule_method=SCHEDULE_METHOD):
        self.base_url = base_url
        self.node_count = node_count
        self.pod_count = pod_count
        self.schedule_method = schedule_method

    def create_nodes(self):
        node_names = []
        for i in range(1, self.node_count + 1):
            node_name = f"Test_node{i}"
            node_names.append(node_name)
            node_data = {
                "name": node_name,
                "ip_address": f"192.168.1.{i}",
                "total_cpu": random.choice([4, 8]),
                "total_memory": random.choice([4, 8]) * 1024 * 1024 * 1024,
                "total_gpu": random.choice([2, 4]),
                "labels": {
                    "zone": random.choice(["us-west", "us-east", "eu-central"]),
                    "environment": random.choice(["production", "development"])
                },
                "annotations": {
                    "description": f"This is worker node {i}."
                }
            }
            response = requests.post(f"{self.base_url}/nodes", json=node_data)
            print(f"Node {node_name} creation status: {response.status_code}")
    
    def create_pods(self):
        pod_names = []
        for j in range(1, self.pod_count + 1):
            pod_name = f"example-pod-{j}"
            pod_names.append(pod_name)
            
            # 随机生成容器数量
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
                    "name": pod_name,
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
            response = requests.post(f"{self.base_url}/pods", json=pod_data)
            print(f"Pod {pod_name} creation status: {response.status_code}")
    
    def schedule_pods(self):
        for l in range(1, self.pod_count + 1):
            pod_name = f"example-pod-{l}"
            schedule_data = {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {
                    "name": pod_name,
                    "namespace": "default",
                    "status": "pending"
                }
            }
            response = requests.post(f"{self.base_url}/{self.schedule_method}", json=schedule_data)
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", "No message provided")
                print(f"Pod {pod_name} scheduling status: {response.status_code}, Message: {message}")
            else:
                try:
                    error_details = response.json()
                except ValueError:
                    error_details = response.text
                print(f"Pod {pod_name} scheduling failed with status code {response.status_code}: {error_details}")
            time.sleep(1)
    
    def save_schedule_history(self):
        try:
            response = requests.post(
                f"{self.base_url}/save_{self.schedule_method}",
                json={"file_path": f"output/{self.schedule_method}_history.png"}
            )
            response.raise_for_status()
            if 'application/json' in response.headers.get('Content-Type', ''):
                print("Response:", response.json())
            else:
                print("Response is not JSON:", response.text)
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while saving schedule: {e}")
    
    def cleanup(self):
        try:
            response = requests.delete(f"{self.base_url}/remove_all_pods", timeout=10)
            try:
                data = response.json()
            except ValueError:
                data = None

            response.raise_for_status()  
            print("Response:", data if data else response.text)

        except requests.exceptions.Timeout:
            print("The request timed out. Please try again later.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

    def run_test(self):
        self.create_nodes()
        self.create_pods()
        self.schedule_pods()
        self.save_schedule_history()
        self.cleanup()

