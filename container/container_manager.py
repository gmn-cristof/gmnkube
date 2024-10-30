import subprocess
import logging
from etcd.etcd_client import EtcdClient  # 假设你有一个 etcd 客户端类

# Configure logging
logging.basicConfig(level=logging.INFO)

class ContainerManager:
    def __init__(self):
        self.etcd_client = EtcdClient()  # 初始化 etcd 客户端

    def create_container(self, image: str, name: str):
        """Creates a container using containerd and updates etcd"""
        try:
            result = subprocess.run(
                ['ctr', 'create', image, name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error creating container: {result.stderr.strip()}")

            logging.info(f"Container {name} created successfully.")
            # 将容器信息写入 etcd
            self.etcd_client.put(f"/containers/{name}", {"image": image, "status": "created"})
        except Exception as e:
            logging.error(f"Failed to create container {name}: {e}")
            raise  # 显式抛出异常

    def delete_container(self, name: str):
        """Deletes a container using containerd and updates etcd"""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'delete', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error deleting container: {result.stderr.strip()}")

            logging.info(f"Container {name} deleted successfully.")
            # 从 etcd 中删除容器记录
            self.etcd_client.delete(f"/containers/{name}")
        except Exception as e:
            logging.error(f"Failed to delete container {name}: {e}")
            raise  # 显式抛出异常

    def list_containers(self):
        """Lists all containers using containerd"""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'list'], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error listing containers: {result.stderr.strip()}")

            logging.info("Containers:\n" + result.stdout)
        except Exception as e:
            logging.error(f"Failed to list containers: {e}")
            raise  # 显式抛出异常

    def container_info(self, name: str):
        """Retrieves information about a specific container and syncs with etcd"""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'info', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error getting container info: {result.stderr.strip()}")

            container_data = result.stdout.strip()
            logging.info(f"Container info for {name}:\n" + container_data)

            # 更新 etcd 中的容器信息
            self.etcd_client.put(f"/containers/{name}", container_data)
        except Exception as e:
            logging.error(f"Failed to get info for container {name}: {e}")
            raise  # 显式抛出异常
