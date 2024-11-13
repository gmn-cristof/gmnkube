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
        self.extract_resources_from_containers()


    def extract_resources_from_containers(self):
        for container in self.containers:
            requests = container.resources.get('requests', {})
            limits = container.resources.get('limits', {})
            
            if isinstance(requests, dict):
                self._add_resources(self.resources['requests'], requests)
            else:
                logging.warning(f"Invalid requests format for container {container.name}: {requests}")

            if isinstance(limits, dict):
                self._add_resources(self.resources['limits'], limits)
            else:
                logging.warning(f"Invalid limits format for container {container.name}: {limits}")

    def _add_resources(self, total_resources, container_resources):
        for resource_type, value in container_resources.items():
            if not isinstance(value, str):  # 确保资源是字符串
                logging.warning(f"Invalid resource format for {resource_type}: {value}")
                continue
            
            # 直接将值存入总资源字典，而不是嵌套字典
            if resource_type not in total_resources:
                total_resources[resource_type] = value
            else:
                total_resources[resource_type] = self._combine_resources(
                    total_resources[resource_type],
                    value,
                    resource_type
                )

    def _combine_resources(self, existing_amount, new_amount, resource_type):
        if resource_type == 'cpu':
            return f"{self._parse_cpu(existing_amount) + self._parse_cpu(new_amount)}m"
        elif resource_type == 'memory':
            return f"{self._parse_memory(existing_amount) + self._parse_memory(new_amount)}Mi"
        elif resource_type == 'gpu':
            return self._parse_gpu(existing_amount) + self._parse_gpu(new_amount)
        return existing_amount

    def _parse_cpu(self, cpu_str):
        return int(cpu_str[:-1]) if isinstance(cpu_str, str) and cpu_str.endswith('m') else int(cpu_str) * 1000

    def _parse_memory(self, memory_str):
        if isinstance(memory_str, str):
            if memory_str.endswith('Gi'):
                return int(memory_str[:-2]) * 1024
            if memory_str.endswith('Mi'):
                return int(memory_str[:-2])
        return int(memory_str)

    def _parse_gpu(self, gpu_str):
        return int(gpu_str) if isinstance(gpu_str, (int, str)) else 0

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
