import logging
from pod.pod import Pod
from pod.pod_controller import PodController
from etcd.etcd_client import EtcdClient  # 假设有 etcd 客户端类

class Node:
    def __init__(self, name, total_cpu, total_memory, total_gpu=0, total_io=0, total_net=0, labels=None, annotations=None):
        """
        初始化 Node 对象。
        """
        self.name = name
        self.total_cpu = total_cpu
        self.total_memory = total_memory
        self.total_gpu = total_gpu
        self.total_io = total_io
        self.total_net = total_net
        self.labels = labels or {}
        self.annotations = annotations or {}
        self.allocated_cpu = 0
        self.allocated_memory = 0
        self.allocated_gpu = 0
        self.allocated_io = 0
        self.allocated_net = 0
        self.pods = []
        self.status = "Ready"
        self.etcd_client = EtcdClient()

    def add_pod(self, pod):
        """在节点上运行一个新的 Pod，并更新资源分配。"""
        required_cpu = pod.resources.get("cpu", 0)
        required_memory = pod.resources.get("memory", 0)
        required_gpu = pod.resources.get("gpu", 0)
        required_io = pod.resources.get("io", 0)
        required_net = pod.resources.get("net", 0)

        if self.can_schedule(required_cpu, required_memory, required_gpu, required_io, required_net):
            self.pods.append(pod)
            self.allocated_cpu += required_cpu
            self.allocated_memory += required_memory
            self.allocated_gpu += required_gpu
            self.allocated_io += required_io
            self.allocated_net += required_net
            self._log_resource_warning()
            logging.info(f"Pod {pod.name} scheduled on Node {self.name}.")
            # 同步状态至 etcd
            self.etcd_client.put(f"/nodes/{self.name}/pods/{pod.name}", "Running")
        else:
            logging.error(f"Not enough resources on Node {self.name} to schedule Pod {pod.name}.")
            raise Exception(f"Not enough resources on Node {self.name} to schedule Pod {pod.name}.")

    def remove_pod(self, pod):
        """从节点上移除一个 Pod，并释放相应资源。"""
        if pod in self.pods:
            self.pods.remove(pod)
            self.allocated_cpu -= pod.resources.get("cpu", 0)
            self.allocated_memory -= pod.resources.get("memory", 0)
            self.allocated_gpu -= pod.resources.get("gpu", 0)
            self.allocated_io -= pod.resources.get("io", 0)
            self.allocated_net -= pod.resources.get("net", 0)
            logging.info(f"Pod {pod.name} removed from Node {self.name}.")
            # 更新 etcd 中的节点状态
            self.etcd_client.delete(f"/nodes/{self.name}/pods/{pod.name}")
        else:
            logging.warning(f"Attempted to remove non-existent Pod {pod.name} from Node {self.name}.")

    def can_schedule(self, required_cpu, required_memory, required_gpu, required_io, required_net):
        """检查节点是否有足够的资源调度 Pod。"""
        return (self.total_cpu - self.allocated_cpu >= required_cpu and
                self.total_memory - self.allocated_memory >= required_memory and
                self.total_gpu - self.allocated_gpu >= required_gpu and
                self.total_io - self.allocated_io >= required_io and
                self.total_net - self.allocated_net >= required_net)

    def set_status(self, status):
        """更新节点状态并同步至 etcd。"""
        self.status = status
        logging.info(f"Node {self.name} status updated to {status}.")
        self.etcd_client.put(f"/nodes/{self.name}/status", status)

    def to_dict(self):
        """将节点信息转换为字典形式，包含资源使用比例，便于序列化。"""
        return {
            "name": self.name,
            "total_cpu": self.total_cpu,
            "total_memory": self.total_memory,
            "total_gpu": self.total_gpu,
            "total_io": self.total_io,
            "total_net": self.total_net,
            "allocated_cpu": self.allocated_cpu,
            "allocated_memory": self.allocated_memory,
            "allocated_gpu": self.allocated_gpu,
            "allocated_io": self.allocated_io,
            "allocated_net": self.allocated_net,
            "cpu_usage_ratio": self.allocated_cpu / self.total_cpu if self.total_cpu > 0 else 0,
            "memory_usage_ratio": self.allocated_memory / self.total_memory if self.total_memory > 0 else 0,
            "pods": [pod.name for pod in self.pods],
            "status": self.status,
            "labels": self.labels,
            "annotations": self.annotations,
        }

    def _log_resource_warning(self):
        """检查资源使用比例，如果接近上限，则记录告警日志。"""
        if self.allocated_cpu / self.total_cpu > 0.8:
            logging.warning(f"Node {self.name} CPU usage above 80%.")
        if self.allocated_memory / self.total_memory > 0.8:
            logging.warning(f"Node {self.name} memory usage above 80%.")
