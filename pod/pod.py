import logging
from container.container_runtime import ContainerRuntime
from container.container import Container
from etcd.etcd_client import EtcdClient  # 假设有一个 etcd 客户端类

containerRuntime = ContainerRuntime(EtcdClient())

class Pod:
    def __init__(self, name: str, containers: list = None, namespace: str = 'default', volumes=None):
        """
        初始化 Pod 对象。
        
        :param name: Pod 的名称
        :param containers: Pod 中的容器列表（默认为空）
        :param namespace: Pod 所在的命名空间（默认为 'default'）
        :param volumes: Pod 使用的卷（默认为空）
        """
        self.name = name
        self.namespace = namespace
        self.containers = containers or []  # List of Container objects
        self.resources = {
            'requests': {},  # 资源请求
            'limits': {}     # 资源限制
        }
        self.volumes = volumes or {}
        self.status = 'Pending'  # Pod 的初始状态
        self.etcd_client = EtcdClient()  # 初始化 Etcd 客户端
        # 自动提取容器资源
        self.extract_resources_from_containers()

    def extract_resources_from_containers(self):
        """
        从容器中提取资源请求和限制，并更新 Pod 的资源字典。
        """
        for container in self.containers:
            # 提取每个容器的请求和限制资源，并加到 Pod 的资源中
            self._add_resources(self.resources['requests'], container.resources.get('requests', {}))
            self._add_resources(self.resources['limits'], container.resources.get('limits', {}))

    def _add_resources(self, total_resources, container_resources):
        """
        将容器的资源添加到 Pod 的总资源中。
        
        :param total_resources: Pod 当前的总资源
        :param container_resources: 容器的资源
        """
        for resource_type, value in container_resources.items():
            # 使用 _sum_resources 方法将资源合并
            total_resources[resource_type] = self._sum_resources(total_resources.get(resource_type, {}), value)

    def _sum_resources(self, existing_resources, new_resources):
        """
        合并已有资源和新资源。
        
        :param existing_resources: 当前已有的资源
        :param new_resources: 新的资源
        :return: 合并后的资源
        """
        for key, amount in new_resources.items():
            existing_amount = existing_resources.get(key, 0)
            # 使用 _combine_resources 方法计算合并后的资源
            existing_resources[key] = self._combine_resources(existing_amount, amount, key)
        return existing_resources

    def _combine_resources(self, existing_amount, new_amount, resource_type):
        """
        计算并返回合并后的资源量。
        
        :param existing_amount: 当前已有的资源量
        :param new_amount: 新的资源量
        :param resource_type: 资源类型（如 CPU、内存、GPU）
        :return: 合并后的资源量
        """
        if resource_type == 'cpu':
            return f"{self._parse_cpu(existing_amount) + self._parse_cpu(new_amount)}m"  # 合并后的 CPU 量
        elif resource_type == 'memory':
            return f"{self._parse_memory(existing_amount) + self._parse_memory(new_amount)}Mi"  # 合并后的内存量
        elif resource_type == 'gpu':
            return self._parse_gpu(existing_amount) + self._parse_gpu(new_amount)  # 合并后的 GPU 量
        return existing_amount  # 默认返回已有量

    def _parse_cpu(self, cpu_str):
        """
        解析 CPU 字符串并转换为毫核心。
        
        :param cpu_str: CPU 字符串（如 "100m" 或 "1"）
        :return: 以毫核心为单位的 CPU 数量
        """
        return int(cpu_str[:-1]) if isinstance(cpu_str, str) and cpu_str.endswith('m') else int(cpu_str) * 1000

    def _parse_memory(self, memory_str):
        """
        解析内存字符串并转换为 Mi。
        
        :param memory_str: 内存字符串（如 "256Mi" 或 "1Gi"）
        :return: 以 Mi 为单位的内存数量
        """
        if isinstance(memory_str, str):
            if memory_str.endswith('Gi'):
                return int(memory_str[:-2]) * 1024  # 转换 Gi 到 Mi
            if memory_str.endswith('Mi'):
                return int(memory_str[:-2])  # 直接返回 Mi
        return int(memory_str)  # 如果是数字，直接返回

    def _parse_gpu(self, gpu_str):
        """
        解析 GPU 字符串并返回整数数量。
        
        :param gpu_str: GPU 字符串（假设为整数）
        :return: GPU 数量
        """
        return int(gpu_str) if isinstance(gpu_str, (int, str)) else 0

    def set_resources(self, requests=None, limits=None):
        """
        设置 Pod 的资源请求和限制，确保单位一致。
        
        :param requests: 请求资源字典
        :param limits: 限制资源字典
        """
        if requests:
            self.resources['requests'] = {
                'cpu': self._convert_cpu(requests.get('cpu', 0)),
                'memory': self._convert_memory(requests.get('memory', 0)),
                'gpu': requests.get('gpu', 0)  # 假设 GPU 数量不需要单位转换
            }
        if limits:
            self.resources['limits'] = {
                'cpu': self._convert_cpu(limits.get('cpu', 0)),
                'memory': self._convert_memory(limits.get('memory', 0)),
                'gpu': limits.get('gpu', 0)
            }

    def _convert_cpu(self, cpu):
        """
        转换 CPU 单位（例如，100m 转为 0.1 核心）。
        
        :param cpu: CPU 资源量
        :return: 转换后的核心数
        """
        return float(cpu[:-1]) / 1000.0 if isinstance(cpu, str) and cpu.endswith('m') else float(cpu)

    def _convert_memory(self, memory):
        """
        转换内存单位（例如，256Mi 转为 256）。
        
        :param memory: 内存资源量
        :return: 转换后的 Mi 数量
        """
        return float(memory[:-2]) if isinstance(memory, str) and memory.endswith('Mi') else float(memory)

        
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
