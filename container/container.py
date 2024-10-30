import json
from etcd.etcd_client import EtcdClient  # 确保导入你的 Etcd 客户端

class Container:
    def __init__(self, name: str, image: str, resources=None, ports=None, etcd_client=None):
        """
        初始化容器对象。
        
        :param name: 容器名称
        :param image: 容器镜像
        :param resources: 资源限制（可选）
        :param ports: 公开的端口列表（可选）
        :param etcd_client: Etcd 客户端（用于数据同步）
        """
        if not isinstance(name, str) or not name:
            raise ValueError("Container name must be a non-empty string.")
        if not isinstance(image, str) or not image:
            raise ValueError("Container image must be a non-empty string.")
        
        self.name = name
        self.image = image
        self.resources = resources or {}
        self.ports = ports or []
        self.etcd_client = etcd_client or EtcdClient()  # 初始化 Etcd 客户端
        self.sync_to_etcd()  # 同步初始状态到 etcd

    def to_dict(self):
        """将容器转换为字典。"""
        return {
            "name": self.name,
            "image": self.image,
            "resources": self.resources,
            "ports": self.ports,
        }

    def to_json(self):
        """将容器转换为 JSON 字符串。"""
        return json.dumps(self.to_dict())

    def __str__(self):
        return f"Container(name={self.name}, image={self.image}, resources={self.resources}, ports={self.ports})"

    def sync_to_etcd(self):
        """同步容器状态到 etcd。"""
        key = f"/containers/{self.name}"
        value = self.to_json()
        self.etcd_client.put(key, value)

    def update_resources(self, resources):
        """更新资源限制。"""
        self.resources.update(resources)
        self.sync_to_etcd()  # 更新后同步到 etcd

    def add_port(self, port):
        """添加端口。"""
        if port not in self.ports:
            self.ports.append(port)
            self.sync_to_etcd()  # 更新后同步到 etcd

    def remove_port(self, port):
        """移除端口。"""
        if port in self.ports:
            self.ports.remove(port)
            self.sync_to_etcd()  # 更新后同步到 etcd
