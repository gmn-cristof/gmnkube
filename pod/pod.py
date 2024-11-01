import logging
from container.container_runtime import ContainerRuntime
from container.container import Container
from etcd.etcd_client import EtcdClient  # 假设有一个 etcd 客户端类

containerRuntime = ContainerRuntime()

class Pod:
    def __init__(self, name: str, containers: list = None, namespace: str = 'default', volumes=None):
        self.name = name
        self.namespace = namespace
        self.containers = containers or [Container]  # List of Container objects
        self.volumes = volumes or {}
        self.status = 'Pending'
        self.etcd_client = EtcdClient()  # 初始化 etcd 客户端
        
    def to_dict(self):
        """将 Pod 对象转换为字典格式."""
        return {
            'name': self.name,
            'namespace': self.namespace,
            'containers': [container.to_dict() for container in self.containers],
            'volumes': self.volumes,
            'status': self.status
        }

    def start(self):
        """Start all containers in the Pod and update etcd status"""
        if self.status != 'Pending' and self.status != 'Stopped':
            logging.error(f"Pod '{self.name}' is already running or terminated.")
            return
        
        all_started = True
        for container in self.containers:
            try:
                containerRuntime.start_container(container.name)
                logging.info(f"Container '{container.name}' started successfully.")
                # 将容器状态更新到 etcd
                self.etcd_client.put(f"/pods/{self.name}/containers/{container.name}/status", "Running")
            except Exception as e:
                logging.error(f"Failed to start container '{container.name}': {e}")
                all_started = False
        
        if all_started:
            self.status = 'Running'
            logging.info(f"Pod '{self.name}' in namespace '{self.namespace}' is now running.")
            # 更新 Pod 状态到 etcd
            self.etcd_client.put(f"/pods/{self.name}/status", "Running")
        else:
            logging.error(f"Pod '{self.name}' failed to start all containers.")

    def stop(self):
        """Stop all containers in the Pod and update etcd status"""
        if self.status != 'Running':
            logging.error(f"Pod '{self.name}' is not running.")
            return
        
        all_stopped = True
        for container in self.containers:
            try:
                containerRuntime.stop_container(container.name)
                logging.info(f"Container '{container.name}' stopped successfully.")
                # 将容器状态更新到 etcd
                self.etcd_client.put(f"/pods/{self.name}/containers/{container.name}/status", "Stopped")
            except Exception as e:
                logging.error(f"Failed to stop container '{container.name}': {e}")
                all_stopped = False

        if all_stopped:
            self.status = 'Stopped'
            logging.info(f"Pod '{self.name}' in namespace '{self.namespace}' has been stopped.")
            # 更新 Pod 状态到 etcd
            self.etcd_client.put(f"/pods/{self.name}/status", "Stopped")

    def add_container(self, container):
        """Add a new container to the Pod if it is not running, and update etcd"""
        if self.status == 'Running':
            logging.error(f"Cannot add container '{container.name}' to running Pod '{self.name}'.")
            return
        self.containers.append(container)
        logging.info(f"Container '{container.name}' added to Pod '{self.name}' in namespace '{self.namespace}'.")
        # 将新的容器状态写入 etcd
        self.etcd_client.put(f"/pods/{self.name}/containers/{container.name}/status", "Pending")

    def remove_container(self, container_name: str):
        """Remove a container from the Pod if it is not running, and update etcd"""
        if self.status == 'Running':
            logging.error(f"Cannot remove container '{container_name}' from running Pod '{self.name}'.")
            return
        self.containers = [c for c in self.containers if c.name != container_name]
        logging.info(f"Container '{container_name}' removed from Pod '{self.name}' in namespace '{self.namespace}'.")
        # 从 etcd 中删除该容器的状态记录
        self.etcd_client.delete(f"/pods/{self.name}/containers/{container_name}")

    def get_status(self):
        """Get the current status of the Pod and its containers."""
        container_statuses = {c.name: c.to_dict() for c in self.containers}
        return {
            'pod_name': self.name,
            'namespace': self.namespace,
            'pod_status': self.status,
            'containers': container_statuses
        }
