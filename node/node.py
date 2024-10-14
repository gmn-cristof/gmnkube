class Node:
    def __init__(self, name, total_cpu, total_memory, labels=None, annotations=None):
        """
        初始化 Node 对象。
        
        :param name: 节点名称
        :param total_cpu: 节点总 CPU 资源（单位：核）
        :param total_memory: 节点总内存资源（单位：MB）
        :param labels: 节点标签（可选）
        :param annotations: 节点注释（可选）
        """
        self.name = name
        self.total_cpu = total_cpu  # 总 CPU 资源
        self.total_memory = total_memory  # 总内存资源
        self.labels = labels or {}  # 标签
        self.annotations = annotations or {}  # 注释
        self.allocated_cpu = 0  # 已分配的 CPU 资源
        self.allocated_memory = 0  # 已分配的内存资源
        self.pods = []  # 当前运行的 Pods 列表
        self.status = "Ready"  # 初始状态：Ready

    def add_pod(self, pod):
        """在节点上运行一个新的 Pod，并更新资源分配。"""
        required_cpu = pod.resources.get("cpu", 0)
        required_memory = pod.resources.get("memory", 0)

        if self.can_schedule(required_cpu, required_memory):
            self.pods.append(pod)
            self.allocated_cpu += required_cpu
            self.allocated_memory += required_memory
            print(f"Pod {pod.name} scheduled on Node {self.name}.")
        else:
            raise Exception(f"Not enough resources on Node {self.name} to schedule Pod {pod.name}.")

    def remove_pod(self, pod):
        """从节点上移除一个 Pod，并释放相应资源。"""
        if pod in self.pods:
            self.pods.remove(pod)
            self.allocated_cpu -= pod.resources.get("cpu", 0)
            self.allocated_memory -= pod.resources.get("memory", 0)
            print(f"Pod {pod.name} removed from Node {self.name}.")

    def can_schedule(self, required_cpu, required_memory):
        """检查节点是否有足够的资源调度 Pod。"""
        available_cpu = self.total_cpu - self.allocated_cpu
        available_memory = self.total_memory - self.allocated_memory
        return available_cpu >= required_cpu and available_memory >= required_memory

    def set_status(self, status):
        """更新节点状态。"""
        self.status = status

    def to_dict(self):
        """将节点信息转换为字典形式，便于序列化。"""
        return {
            "name": self.name,
            "total_cpu": self.total_cpu,
            "total_memory": self.total_memory,
            "allocated_cpu": self.allocated_cpu,
            "allocated_memory": self.allocated_memory,
            "pods": [pod.name for pod in self.pods],
            "status": self.status,
            "labels": self.labels,
            "annotations": self.annotations,
        }
