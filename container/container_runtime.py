import subprocess
import logging
from etcd.etcd_client import EtcdClient  

# Configure logging
logging.basicConfig(level=logging.INFO)

class ContainerRuntime:
    def __init__(self):
        self.etcd_client = EtcdClient()  # 初始化 etcd 客户端

    def start_container(self, name: str):
        """Starts a container and updates etcd status."""
        try:
            result = subprocess.run(
                ['ctr', 'task', 'start', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error starting container: {result.stderr.strip()}")
            logging.info(f"Container {name} started successfully.")
            # 更新 etcd 中的容器状态
            self.etcd_client.put(f"/containers/{name}/status", "running")
        except Exception as e:
            logging.error(f"Failed to start container {name}: {e}")

    def stop_container(self, name: str):
        """Stops a container and updates etcd status."""
        try:
            result = subprocess.run(
                ['ctr', 'task', 'kill', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error stopping container: {result.stderr.strip()}")
            logging.info(f"Container {name} stopped successfully.")
            # 更新 etcd 中的容器状态
            self.etcd_client.put(f"/containers/{name}/status", "stopped")
        except Exception as e:
            logging.error(f"Failed to stop container {name}: {e}")

    def list_containers(self):
        """Lists all containers and optionally syncs with etcd."""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'ls'], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error listing containers: {result.stderr.strip()}")
            logging.info(f"Containers:\n{result.stdout}")
            # 可选：将容器列表与 etcd 同步
            containers = result.stdout.splitlines()
            for container in containers:
                container_name = container.split()[0]  # 假设第一个字段是容器名称
                self.etcd_client.put(f"/containers/{container_name}/status", "listed")
        except Exception as e:
            logging.error(f"Failed to list containers: {e}")

    def remove_container(self, name: str):
        """Removes a container and updates etcd."""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'rm', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error removing container: {result.stderr.strip()}")
            logging.info(f"Container {name} removed successfully.")
            # 从 etcd 中删除容器记录
            self.etcd_client.delete(f"/containers/{name}")
        except Exception as e:
            logging.error(f"Failed to remove container {name}: {e}")

    def inspect_container(self, name: str):
        """Inspects a container and syncs data with etcd."""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'info', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error inspecting container: {result.stderr.strip()}")
            container_info = result.stdout.strip()
            logging.info(f"Container {name} info:\n{container_info}")
            # 将容器信息同步到 etcd
            self.etcd_client.put(f"/containers/{name}/info", container_info)
        except Exception as e:
            logging.error(f"Failed to inspect container {name}: {e}")
