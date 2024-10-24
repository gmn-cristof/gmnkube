import json

class Container:
    def __init__(self, name: str, image: str, resources=None, ports=None):
        """
        初始化容器对象。
        
        :param name: 容器名称
        :param image: 容器镜像
        :param resources: 资源限制（可选）
        :param ports: 公开的端口列表（可选）
        """
        if not isinstance(name, str) or not name:
            raise ValueError("Container name must be a non-empty string.")
        if not isinstance(image, str) or not image:
            raise ValueError("Container image must be a non-empty string.")
        
        self.name = name
        self.image = image
        self.resources = resources or {}
        self.ports = ports or []

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

    def update_resources(self, resources):
        """更新资源限制。"""
        self.resources.update(resources)

    def add_port(self, port):
        """添加端口。"""
        if port not in self.ports:
            self.ports.append(port)

    def remove_port(self, port):
        """移除端口。"""
        if port in self.ports:
            self.ports.remove(port)
