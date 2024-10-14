from .node import Node

class NodeController:
    def __init__(self):
        """
        初始化 NodeController 对象，管理多个节点的操作。
        """
        self.nodes = {}  # 存储所有节点的字典，键为节点名称，值为 Node 对象

    def add_node(self, name, total_cpu, total_memory, labels=None, annotations=None):
        """
        添加一个新的节点。
        
        :param name: 节点名称
        :param total_cpu: 节点总 CPU 资源
        :param total_memory: 节点总内存资源
        :param labels: 节点标签（可选）
        :param annotations: 节点注释（可选）
        """
        if name in self.nodes:
            raise Exception(f"Node {name} already exists.")
        
        node = Node(name, total_cpu, total_memory, labels, annotations)
        self.nodes[name] = node
        print(f"Node {name} added with {total_cpu} CPUs and {total_memory} MB of memory.")

    def remove_node(self, name):
        """
        移除一个节点。
        
        :param name: 节点名称
        """
        if name not in self.nodes:
            raise Exception(f"Node {name} does not exist.")
        
        del self.nodes[name]
        print(f"Node {name} removed.")

    def list_nodes(self):
        """
        列出所有节点的信息。
        
        :return: 返回所有节点的字典
        """
        for node_name, node in self.nodes.items():
            node_info = node.to_dict()
            print(f"Node {node_name}: {node_info}")
        return self.nodes

    def get_node(self, name):
        """
        获取一个节点的详细信息。
        
        :param name: 节点名称
        :return: 节点对象
        """
        if name not in self.nodes:
            raise Exception(f"Node {name} does not exist.")
        
        return self.nodes[name]

    def schedule_pod_to_node(self, pod, node_name):
        """
        将一个 Pod 调度到指定节点。
        
        :param pod: Pod 对象
        :param node_name: 节点名称
        """
        if node_name not in self.nodes:
            raise Exception(f"Node {node_name} does not exist.")
        
        node = self.nodes[node_name]
        node.add_pod(pod)

    def remove_pod_from_node(self, pod, node_name):
        """
        从指定节点移除一个 Pod。
        
        :param pod: Pod 对象
        :param node_name: 节点名称
        """
        if node_name not in self.nodes:
            raise Exception(f"Node {node_name} does not exist.")
        
        node = self.nodes[node_name]
        node.remove_pod(pod)

    def update_node_status(self, node_name, status):
        """
        更新节点的状态。
        
        :param node_name: 节点名称
        :param status: 节点状态（例如："Ready", "NotReady", "Maintenance"）
        """
        if node_name not in self.nodes:
            raise Exception(f"Node {node_name} does not exist.")
        
        node = self.nodes[node_name]
        node.set_status(status)
        print(f"Node {node_name} status updated to {status}.")
