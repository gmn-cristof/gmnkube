import logging
import json

class Pod:
    def __init__(self, name: str, containers: list = None, namespace: str = 'default', volumes=None):
        self.name = name
        self.namespace = namespace
        self.containers = containers or []
        self.resources = {
            'requests': {},
            'limits': {}
        }
        self.volumes = volumes or {}
        self.status = 'Pending'
        self._aggregate_resources()

    def _aggregate_resources(self):
        """从所有容器中提取资源并计算总量。"""
        for container in self.containers:
            if not hasattr(container, 'resources'):
                logging.warning(f"Container {container} has no 'resources' attribute.")
                continue

            requests = container.resources.get('requests', {})
            limits = container.resources.get('limits', {})

            self._add_resource_totals(self.resources['requests'], requests)
            self._add_resource_totals(self.resources['limits'], limits)

    def _add_resource_totals(self, total_resources, container_resources):
        """合并容器资源到总资源。"""
        for resource_type, value in container_resources.items():
            if not isinstance(value, str):
                logging.warning(f"Invalid resource value for {resource_type}: {value}. Expected string.")
                continue

            if resource_type not in total_resources:
                total_resources[resource_type] = value
            else:
                total_resources[resource_type] = self._combine_resources(
                    total_resources[resource_type],
                    value,
                    resource_type
                )

    def _combine_resources(self, current, new, resource_type):
        """合并两种资源值，支持 CPU、内存、GPU。"""
        if resource_type == 'cpu':
            return f"{self._parse_cpu(current) + self._parse_cpu(new)}m"
        elif resource_type == 'memory':
            return f"{self._parse_memory(current) + self._parse_memory(new)}Mi"
        elif resource_type == 'gpu':
            return str(self._parse_gpu(current) + self._parse_gpu(new))
        else:
            logging.warning(f"Unknown resource type: {resource_type}.")
            return current

    def _parse_cpu(self, cpu_str):
        """解析 CPU 值，支持 'm' 单位。"""
        if cpu_str.endswith('m'):
            return int(cpu_str[:-1])  # 转换为 millicores
        return int(cpu_str) * 1000  # 假设为 cores，转换为 millicores

    def _parse_memory(self, memory_str):
        """解析内存值，支持 'Mi' 和 'Gi' 单位。"""
        if memory_str.endswith('Gi'):
            return int(memory_str[:-2]) * 1024  # 转换为 Mi
        elif memory_str.endswith('Mi'):
            return int(memory_str[:-2])  # 保留 Mi
        logging.warning(f"Unexpected memory format: {memory_str}. Defaulting to 0.")
        return 0

    def _parse_gpu(self, gpu_str):
        """解析 GPU 值，确保返回整数。"""
        try:
            return int(gpu_str)
        except ValueError:
            logging.warning(f"Invalid GPU format: {gpu_str}. Defaulting to 0.")
            return 0

    def to_dict(self):
        return {
            'name': self.name,
            'namespace': self.namespace,
            'containers': [container.to_dict() for container in self.containers],
            'resources': self.resources,
            'volumes': self.volumes,
            'status': self.status
        }

    def add_container(self, container):
        """Add a new container to the Pod if it is not running, and update etcd"""
        if self.status == 'Running':
            logging.error(f"Cannot add container '{container.name}' to running Pod '{self.name}'.")
            return
        self.containers.append(container)
        logging.info(f"Container '{container.name}' added to Pod '{self.name}' in namespace '{self.namespace}'.")
        # 将新的容器状态写入 etcd
        #self.etcd_client.put(f"/pods/{self.name}/containers/{container.name}/status", "Pending")

    def remove_container(self, container_name: str):
        """Remove a container from the Pod if it is not running, and update etcd"""
        if self.status == 'Running':
            logging.error(f"Cannot remove container '{container_name}' from running Pod '{self.name}'.")
            return
        self.containers = [c for c in self.containers if c.name != container_name]
        logging.info(f"Container '{container_name}' removed from Pod '{self.name}' in namespace '{self.namespace}'.")
        # 从 etcd 中删除该容器的状态记录
        #self.etcd_client.delete(f"/pods/{self.name}/containers/{container_name}")

    def get_status(self):
        """Get the current status of the Pod and its containers."""
        container_statuses = {c.name: c.to_dict() for c in self.containers}
        return {
            'pod_name': self.name,
            'namespace': self.namespace,
            'pod_status': self.status,
            'containers': container_statuses
        }
    def to_json(self):
        """将容器转换为 JSON 字符串。"""
        return json.dumps(self.to_dict())
    
    
    # def sync_to_etcd(self):
    #     """同步 Pod 状态到 etcd。"""
    #     key = f"/pods/{self.namespace}/{self.name}"  # 采用命名空间来组织
    #     value = self.to_json()  # 将 Pod 转换为 JSON 格式
    #     self.etcd_client.put(key, value)  # 将数据写入 etcd
