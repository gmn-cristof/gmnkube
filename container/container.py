class Container:
    def __init__(self, name, image, resources=None, ports=None):
        """
        初始化容器对象。
        
        :param name: 容器名称
        :param image: 容器镜像
        :param resources: 资源限制（可选）
        :param ports: 公开的端口列表（可选）
        """
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
