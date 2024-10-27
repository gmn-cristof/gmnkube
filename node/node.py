class Node:
    def __init__(self, name, total_cpu, total_memory, total_gpu=0, total_io=0, total_net=0, labels=None, annotations=None):
        """
        初始化 Node 对象。
        
        :param name: 节点名称
        :param total_cpu: 节点总 CPU 资源（单位：核）
        :param total_memory: 节点总内存资源（单位：MB）
        :param total_gpu: 节点总 GPU 资源（单位：个数）
        :param total_io: 节点总 IO 资源（单位：MB/s）
        :param total_net: 节点总网络带宽（单位：MB/s）
        :param labels: 节点标签（可选）
        :param annotations: 节点注释（可选）
        """
        self.name = name
        self.total_cpu = total_cpu  # 总 CPU 资源
        self.total_memory = total_memory  # 总内存资源
        self.total_gpu = total_gpu  # 总 GPU 资源
        self.total_io = total_io  # 总 IO 资源
        self.total_net = total_net  # 总网络带宽
        self.labels = labels or {}  # 标签
        self.annotations = annotations or {}  # 注释
        self.allocated_cpu = 0  # 已分配的 CPU 资源
        self.allocated_memory = 0  # 已分配的内存资源
        self.allocated_gpu = 0  # 已分配的 GPU 资源
        self.allocated_io = 0  # 已分配的 IO 资源
        self.allocated_net = 0  # 已分配的网络带宽
        self.pods = []  # 当前运行的 Pods 列表
        self.status = "Ready"  # 初始状态：Ready

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
            print(f"Pod {pod.name} scheduled on Node {self.name}.")
        else:
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
            print(f"Pod {pod.name} removed from Node {self.name}.")

    def can_schedule(self, required_cpu, required_memory, required_gpu, required_io, required_net):
        """检查节点是否有足够的资源调度 Pod。"""
        available_cpu = self.total_cpu - self.allocated_cpu
        available_memory = self.total_memory - self.allocated_memory
        available_gpu = self.total_gpu - self.allocated_gpu
        available_io = self.total_io - self.allocated_io
        available_net = self.total_net - self.allocated_net
        
        return (available_cpu >= required_cpu and
                available_memory >= required_memory and
                available_gpu >= required_gpu and
                available_io >= required_io and
                available_net >= required_net)

    def set_status(self, status):
        """更新节点状态。"""
        self.status = status

    def to_dict(self):
        """将节点信息转换为字典形式，便于序列化。"""
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
            "pods": [pod.name for pod in self.pods],
            "status": self.status,
            "labels": self.labels,
            "annotations": self.annotations,
        }
