class Pod:
    def __init__(self, name, namespace, containers, labels=None, annotations=None):
        """
        初始化 Pod 对象。
        
        :param name: Pod 名称
        :param namespace: Pod 所在的命名空间
        :param containers: 容器列表，包含容器的定义
        :param labels: Pod 的标签（可选）
        :param annotations: Pod 的注释（可选）
        """
        self.name = name
        self.namespace = namespace
        self.containers = containers  # 这个应该是一个容器对象的列表
        self.labels = labels or {}
        self.annotations = annotations or {}
        self.status = "Pending"  # 初始状态
        self.creation_timestamp = None  # 创建时间戳

    def start(self):
        """Start the Pod"""
        self.status = 'Running'
        print(f"Pod '{self.name}' is now running.")

    def stop(self):
        """Stop the Pod"""
        self.status = 'Stopped'
        print(f"Pod '{self.name}' has been stopped.")
    
    def set_status(self, status):
        """设置 Pod 的状态。"""
        self.status = status

    def add_label(self, key, value):
        """添加标签。"""
        self.labels[key] = value

    def add_annotation(self, key, value):
        """添加注释。"""
        self.annotations[key] = value

    def to_dict(self):
        """将 Pod 转换为字典，以便于序列化。"""
        return {
            "name": self.name,
            "namespace": self.namespace,
            "containers": [container.to_dict() for container in self.containers],
            "labels": self.labels,
            "annotations": self.annotations,
            "status": self.status,
            "creation_timestamp": self.creation_timestamp,
        }