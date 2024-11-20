import logging
from .node import Node
from pod.pod import Pod
import json
#from etcd.etcd_client import EtcdClient

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NodeController:
    def __init__(self, etcd_client):
        """初始化 NodeController，管理多个节点的操作，并连接 etcd 服务."""
        self.nodes = {}
        self.etcd_client = etcd_client

    def add_node(self, name, ip_address, total_cpu, total_memory, total_gpu, total_io, total_net, labels=None, annotations=None):
        """添加一个新的节点，并在 etcd 中保存其信息."""
        if name in self.nodes:
            logging.error(f"Node '{name}' already exists.")
            raise Exception(f"Node '{name}' already exists.")
        
        #默认值处理：0 作为初始化值
        total_cpu = total_cpu if total_cpu != 0 else 0  # 0表示没有分配资源
        total_memory = total_memory if total_memory != 0 else 0
        total_gpu = total_gpu if total_gpu != 0 else 0
        total_io = total_io if total_io != 0 else 100
        total_net = total_net if total_net != 0 else 100
        
        # 默认值处理：确保 labels 和 annotations 是字典类型
        labels = labels if labels is not None else {}
        annotations = annotations if annotations is not None else {}

        # 创建节点对象并保存
        node = Node(name, ip_address, total_cpu, total_memory, total_gpu, total_io, total_net, labels, annotations)
        self.nodes[name] = node


        # 将节点信息存储到 etcd
        self._update_etcd_node(node)

    def remove_node(self, name):
        """移除一个节点，并在 etcd 中删除其信息.
        :param name: 节点名称
        """
        if name not in self.nodes:
            logging.error(f"Node '{name}' does not exist.")
            raise Exception(f"Node '{name}' does not exist.")
        
        node = self.nodes[name]
        del self.nodes[name]

        # 从 etcd 中删除节点信息
        self.etcd_client.delete(f"nodes/{name}")
        logging.info(f"Node '{name}' removed.")

    def list_nodes(self):
        """列出所有节点的信息.
        :return: 返回所有节点的字典"""
        node_info_list = {}
        try:
            logging.info("Attempting to get nodes with prefix 'nodes/'")
            response = self.etcd_client.get("nodes/", prefix=True)  # 确保使用前缀获取
            logging.info(f"Response received: {response}")

            if response is None :
                logging.warning("No nodes found in etcd.")
                return node_info_list  # 返回空字典

            for node in response.kvs:  # 遍历返回的键值对
                node_key = node.key.decode()
                if node_key.startswith("nodes/"):  # 检查前缀
                    node_info = node.value.decode()  # 处理字节编码
                    node_info_list[node_key.split('/')[-1]] = node_info  # 以节点名称为键
                    logging.info(f"Node '{node_key.split('/')[-1]}': {node_info}")
        except Exception as e:
            logging.error(f"Failed to list nodes from etcd: {e}")
            raise

        return node_info_list

    def get_node(self, name):
        """获取一个节点的详细信息.
        :param name: 节点名称
        :return: 节点对象
        """
        if name not in self.nodes:
            logging.error(f"Node '{name}' does not exist.")
            raise Exception(f"Node '{name}' does not exist.")
        
        return self.nodes[name]

    def schedule_pod_to_node(self, pod, node_name):
        """将一个 Pod 调度到指定节点.
        :param pod: Pod 对象
        :param node_name: 节点名称
        """
        self._check_node_existence(node_name)
        
        node = self.nodes[node_name]
        node.add_pod(pod)

        # 更新节点信息到 etcd
        self._update_etcd_node(node)

    def remove_pod_from_node(self, pod, node_name):
        """从指定节点移除一个 Pod.
        :param pod: Pod 对象
        :param node_name: 节点名称
        """
        self._check_node_existence(node_name)

        node = self.nodes[node_name]
        node.remove_pod(pod)

        # 更新节点信息到 etcd
        self._update_etcd_node(node)

    def update_node_status(self, node_name, status):
        """更新节点的状态.
        
        :param node_name: 节点名称
        :param status: 节点状态（例如："Ready", "NotReady", "Maintenance"）
        """
        self._check_node_existence(node_name)
        
        node = self.nodes[node_name]
        node.set_status(status)

        # 更新节点状态到 etcd
        self._update_etcd_node(node)
        logging.info(f"Node '{node_name}' status updated to '{status}'.")

    def _update_etcd_node(self, node):
        """更新节点信息到 etcd."""
        try:
            # 将字典转换为 JSON 字符串
            node_data = json.dumps(node.to_dict())
            self.etcd_client.put(f"nodes/{node.name}", node_data)
            logging.info(f"Node '{node.name}' updated in etcd.")
        except Exception as e:
            logging.error(f"Failed to update node '{node.name}' in etcd: {e}")
            raise

    def _check_node_existence(self, node_name):
        """检查节点是否存在, 若不存在则抛出异常."""
        if node_name not in self.nodes:
            logging.error(f"Node '{node_name}' does not exist.")
            raise Exception(f"Node '{node_name}' does not exist.")
        
    def get_all_nodes(self):
        """获取所有节点的信息"""
        try:
            node_values = self.etcd_client.get_with_prefix("nodes/")  # 使用 EtcdClient 的方法
            node_info_list = {}

            for value in node_values:
                node_data = json.loads(value)  # 解析 JSON 字符串
                node_name = node_data['name']  # 获取节点名称
                node_info_list[node_name] = node_data  # 存储节点数据

            logging.info(f"Retrieved all nodes: {node_info_list}")
            return node_info_list
        except Exception as e:
            logging.error(f"Failed to get all nodes: {e}")
            return {}
        
    def add_pod_to_node(self, pod , node_name):
        """Schedule and add a Pod to a specified node if resources are sufficient.

        :param pod: The Pod object to add
        :param node_name: The name of the target node
        """
        node = self.nodes.get(node_name)
        if not node:
            logging.error(f"Node {node_name} does not exist.")
            raise ValueError(f"Node {node_name} does not exist.")
            # 尝试启动 Pod
        try:
            node.add_pod(pod)
            self.etcd_client.put(f"/pods/{pod.namespace}/{pod.name}/status", "Running")
            logging.info(f"Pod {pod.name} scheduled on Node {node.name}.")
        except Exception as e:
            logging.error(f"Failed to add Pod '{pod.name}': {e}")

    def remove_pod_from_node(self, pod, node_name):
        """Remove a Pod from a specified node and release resources.

        :param pod: The Pod object to remove
        :param node_name: The name of the target node
        """
        node = self.nodes.get(node_name)
        if not node:
            logging.error(f"Node {node_name} does not exist.")
            raise ValueError(f"Node {node_name} does not exist.")
        self.etcd_client.delete(f"/nodes/{self.name}/pods/{pod.name}")
        node.remove_pod(pod)
    
    def change_node_status(self, status, node_name):
        """change node status of a specified node
                :param node_name: The name of the target node
        """
        node = self.nodes.get(node_name)
        if not node:
            logging.error(f"Node {node_name} does not exist.")
            raise ValueError(f"Node {node_name} does not exist.")
        self.etcd_client.put(f"/nodes/{self.name}/status", status)
        node.set_status(status)
        
        
        
        
         

