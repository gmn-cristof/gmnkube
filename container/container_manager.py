import subprocess
import logging,json
from .container import Container
#from etcd.etcd_client import EtcdClient  # 假设你有一个 etcd 客户端类

# Configure logging
logging.basicConfig(level=logging.INFO)

class ContainerManager:
    def __init__(self, etcd_client):
        self.etcd_client = etcd_client  # 初始化 etcd 客户端

    def create_container(self, container: Container):
        """Creates a container using containerd and updates etcd"""
        try:
            # 构造创建命令
            cmd = ['sudo', 'ctr', 'container', 'create', container.image, container.name]
            if container.command:
                cmd.extend(container.command)
            if container.ports:
                cmd.extend(['--ports', json.dumps(container.ports)])
            if container.resources:
                # 处理资源限制，如 requests 和 limits
                for limit_type, resources in container.resources.items():
                    for resource, value in resources.items():
                        cmd.extend([f"--{limit_type}-{resource}", value])

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Error creating container: {result.stderr.strip()}")

            logging.info(f"Container {container.name} created successfully.")
            # 将容器信息写入 etcd
            self.etcd_client.put(f"/containers/{container.name}", {
                "image": container.image,
                "command": container.command,
                "ports": container.ports,
                "resources": container.resources,
                "status": "created"
            })
        except Exception as e:
            logging.error(f"Failed to create container {container.name}: {e}")
            raise

    def delete_container(self, name: str):
        """Deletes a container using containerd and updates etcd"""
        try:
            result = subprocess.run(
                ['sudo', 'ctr', 'containers', 'delete', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error deleting container: {result.stderr.strip()}")

            logging.info(f"Container {name} deleted successfully.")
            # 从 etcd 中删除容器记录
            self.etcd_client.delete(f"/containers/{name}")
        except Exception as e:
            logging.error(f"Failed to delete container {name}: {e}")
            raise

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
