import logging
from .node import Node

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NodeController:
    def __init__(self):
        """
        初始化 NodeController 对象，管理多个节点的操作。
        """
        self.nodes = {}  # 存储所有节点的字典，键为节点名称，值为 Node 对象

    def add_node(self, name, total_cpu, total_memory, total_gpu=0, total_io=0, total_net=0, labels=None, annotations=None):
        """
        添加一个新的节点。
        
        :param name: 节点名称
        :param total_cpu: 节点总 CPU 资源
        :param total_memory: 节点总内存资源
        :param total_gpu: 节点总 GPU 资源（可选）
        :param total_io: 节点总 IO 资源（可选）
        :param total_net: 节点总网络带宽（可选）
        :param labels: 节点标签（可选）
        :param annotations: 节点注释（可选）
        """
        if name in self.nodes:
            logging.error(f"Node {name} already exists.")
            raise Exception(f"Node {name} already exists.")
        
        node = Node(name, total_cpu, total_memory, total_gpu, total_io, total_net, labels, annotations)
        self.nodes[name] = node
        logging.info(f"Node {name} added with {total_cpu} CPUs, {total_memory} MB of memory, "
                    f"{total_gpu} GPUs, {total_io} MB/s IO, and {total_net} MB/s net.")

    def remove_node(self, name):
        """
        移除一个节点。
        
        :param name: 节点名称
        """
        if name not in self.nodes:
            logging.error(f"Node {name} does not exist.")
            raise Exception(f"Node {name} does not exist.")
        
        del self.nodes[name]
        logging.info(f"Node {name} removed.")

    def list_nodes(self):
        """
        列出所有节点的信息。
        
        :return: 返回所有节点的字典
        """
        node_info_list = {}
        for node_name, node in self.nodes.items():
            node_info = node.to_dict()
            logging.info(f"Node {node_name}: {node_info}")
            node_info_list[node_name] = node_info
        return node_info_list

    def get_node(self, name):
        """
        获取一个节点的详细信息。
        
        :param name: 节点名称
        :return: 节点对象
        """
        if name not in self.nodes:
            logging.error(f"Node {name} does not exist.")
            raise Exception(f"Node {name} does not exist.")
        
        return self.nodes[name]

    def schedule_pod_to_node(self, pod, node_name):
        """
        将一个 Pod 调度到指定节点。
        
        :param pod: Pod 对象
        :param node_name: 节点名称
        """
        if node_name not in self.nodes:
            logging.error(f"Node {node_name} does not exist.")
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
            logging.error(f"Node {node_name} does not exist.")
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
            logging.error(f"Node {node_name} does not exist.")
            raise Exception(f"Node {node_name} does not exist.")
        
        node = self.nodes[node_name]
        node.set_status(status)
        logging.info(f"Node {node_name} status updated to {status}.")
