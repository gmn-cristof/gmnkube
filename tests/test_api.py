import pytest
from sanic import Sanic
from sanic_testing import SanicTestManager
from api.api_server_master import configure_routes  # 替换为您实际的模块
from node.node_controller import NodeController
from pod.pod_controller import PodController

# 初始化测试应用
app = Sanic("TestApp")
configure_routes(app)

@pytest.fixture
def test_client():
    return SanicTestManager(app)

def test_add_node(test_client):
    """测试添加节点的路由"""
    response = test_client.post("/nodes", json={
        "name": "test-node",
        "ip_address": "192.168.1.1",
        "total_cpu": 4,
        "total_memory": 8192,
        "total_gpu": 1,  # 添加 GPU 资源
    })
    assert response.status == 201
    assert response.json["message"] == "Node added successfully."

def test_add_existing_node(test_client):
    """测试添加已存在节点的情况"""
    test_client.post("/nodes", json={
        "name": "test-node",
        "ip_address": "192.168.1.1",
        "total_cpu": 4,
        "total_memory": 8192,
        "total_gpu": 1,
    })
    response = test_client.post("/nodes", json={
        "name": "test-node",
        "ip_address": "192.168.1.1",
        "total_cpu": 4,
        "total_memory": 8192,
        "total_gpu": 1,
    })
    assert response.status == 400
    assert "Node 'test-node' already exists." in response.json["error"]

def test_list_nodes(test_client):
    """测试列出节点的路由"""
    test_client.post("/nodes", json={
        "name": "test-node",
        "ip_address": "192.168.1.1",
        "total_cpu": 4,
        "total_memory": 8192,
        "total_gpu": 1,
    })
    response = test_client.get("/nodes")
    assert response.status == 200
    assert len(response.json["nodes"]) > 0

def test_create_pod(test_client):
    """测试创建 Pod 的路由"""
    test_client.post("/nodes", json={
        "name": "test-node",
        "ip_address": "192.168.1.1",
        "total_cpu": 4,
        "total_memory": 8192,
        "total_gpu": 1,
    })
    response = test_client.post("/pods", json={
        "metadata": {"name": "test-pod", "namespace": "default"},
        "spec": {
            "containers": [
                {
                    "name": "test-container",
                    "image": "nginx",
                    "command": ["nginx", "-g", "daemon off;"],
                    "ports": [{"containerPort": 80}],
                    "resources": {
                        "requests": {
                            "cpu": "100m",
                            "memory": "256Mi",
                            "gpu": 1  # 请求 GPU 资源
                        },
                        "limits": {
                            "cpu": "200m",
                            "memory": "512Mi",
                            "gpu": 1  # 限制 GPU 资源
                        },
                    },
                }
            ]
        }
    })
    assert response.status == 201
    assert "Pod 'test-pod' created successfully." in response.json["message"]

def test_list_pods(test_client):
    """测试列出 Pods 的路由"""
    test_client.post("/nodes", json={
        "name": "test-node",
        "ip_address": "192.168.1.1",
        "total_cpu": 4,
        "total_memory": 8192,
        "total_gpu": 1,
    })
    test_client.post("/pods", json={
        "metadata": {"name": "test-pod", "namespace": "default"},
        "spec": {
            "containers": [
                {
                    "name": "test-container",
                    "image": "nginx",
                    "command": ["nginx", "-g", "daemon off;"],
                    "ports": [{"containerPort": 80}],
                    "resources": {
                        "requests": {
                            "cpu": "100m",
                            "memory": "256Mi",
                            "gpu": 1
                        },
                        "limits": {
                            "cpu": "200m",
                            "memory": "512Mi",
                            "gpu": 1
                        },
                    },
                }
            ]
        }
    })
    response = test_client.get("/pods")
    assert response.status == 200
    assert len(response.json["pods"]) > 0

def test_delete_pod(test_client):
    """测试删除 Pod 的路由"""
    test_client.post("/nodes", json={
        "name": "test-node",
        "ip_address": "192.168.1.1",
        "total_cpu": 4,
        "total_memory": 8192,
        "total_gpu": 1,
    })
    test_client.post("/pods", json={
        "metadata": {"name": "test-pod", "namespace": "default"},
        "spec": {
            "containers": [
                {
                    "name": "test-container",
                    "image": "nginx",
                    "command": ["nginx", "-g", "daemon off;"],
                    "ports": [{"containerPort": 80}],
                    "resources": {
                        "requests": {
                            "cpu": "100m",
                            "memory": "256Mi",
                            "gpu": 1
                        },
                        "limits": {
                            "cpu": "200m",
                            "memory": "512Mi",
                            "gpu": 1
                        },
                    },
                }
            ]
        }
    })
    response = test_client.delete("/pods/test-pod")
    assert response.status == 200
    assert "Pod 'test-pod' deleted successfully." in response.json["message"]

def test_list_pods(test_client):
    """测试列出 Pod 的路由"""
    test_client.post("/pods", json={
        "metadata": {"name": "test-pod", "namespace": "default"},
        "spec": {
            "containers": [
                {
                    "name": "test-container",
                    "image": "nginx",
                }
            ]
        }
    })
    response = test_client.get("/pods")
    assert response.status == 200
    assert len(response.json["pods"]) > 0

def test_start_stop_pod(test_client):
    """测试启动和停止 Pod 的路由"""
    test_client.post("/pods", json={
        "metadata": {"name": "test-pod", "namespace": "default"},
        "spec": {
            "containers": [
                {
                    "name": "test-container",
                    "image": "nginx",
                }
            ]
        }
    })
    response_start = test_client.post("/pods/test-pod/start")
    assert response_start.status == 200
    assert "Pod 'test-pod' started successfully." in response_start.json["message"]

    response_stop = test_client.post("/pods/test-pod/stop")
    assert response_stop.status == 200
    assert "Pod 'test-pod' stopped successfully." in response_stop.json["message"]

def test_restart_pod(test_client):
    """测试重启 Pod 的路由"""
    test_client.post("/pods", json={
        "metadata": {"name": "test-pod", "namespace": "default"},
        "spec": {
            "containers": [
                {
                    "name": "test-container",
                    "image": "nginx",
                }
            ]
        }
    })
    response = test_client.post("/pods/test-pod/restart")
    assert response.status == 200
    assert "Pod 'test-pod' restarted successfully." in response.json["message"]

def test_schedule_pod(test_client):
    """测试调度 Pod 的路由"""
    test_client.post("/nodes", json={
        "name": "test-node",
        "ip_address": "192.168.1.1",
        "total_cpu": 4,
        "total_memory": 8192,
        "total_gpu": 1,
        "total_io": 1000,
        "total_net": 1000
    })
    test_client.post("/pods", json={
        "metadata": {"name": "test-pod", "namespace": "default"},
        "spec": {
            "containers": [
                {
                    "name": "test-container",
                    "image": "nginx",
                }
            ]
        }
    })
    response = test_client.post("/nodes/test-node/schedule", json={
        "pod_name": "test-pod"
    })
    assert response.status == 200
    assert "Pod 'test-pod' scheduled to Node 'test-node' successfully." in response.json["message"]

# DDQN 调度测试
def test_ddqn_schedule_pod(test_client):
    """测试 DDQN 调度 Pod 的路由"""
    test_client.post("/nodes", json={
        "name": "test-node",
        "ip_address": "192.168.1.1",
        "total_cpu": 4,
        "total_memory": 8192,
        "total_gpu": 1,
        "total_io": 1000,
        "total_net": 1000
    })
    response = test_client.post("/DDQN_schedule", json={
        "metadata": {"name": "ddqn-pod", "namespace": "default"},
        "spec": {
            "containers": [
                {
                    "name": "ddqn-container",
                    "image": "nginx",
                    "resources": {
                        "requests": {"cpu": "1", "memory": "512Mi","gpu": 0.5},
                        "limits": {"cpu": "2", "memory": "1Gi","gpu": 0.5},
                    },
                }
            ],
            "volumes": []
        }
    })
    assert response.status == 200
    assert "Pod 'ddqn-pod' scheduled successfully." in response.json["message"]

if __name__ == "__main__":
    pytest.main()