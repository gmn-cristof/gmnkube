import logging
from node.node_controller import NodeController
from pod.pod import Pod

# 配置 logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Kube_Scheduler_Plus:
    def __init__(self, node_controller : NodeController, weights=None):
        """
        初始化 KubeSchedulerPlus，连接 etcd 并加载节点信息。
        :param etcd_host: etcd 主机
        :param etcd_port: etcd 端口
        :param config_file: 配置文件路径
        :param weights: 资源权重字典（例如: {'cpu': 1.0, 'gpu': 2.0, 'memory': 1.5}）
        """
        self.node_controller = node_controller
        self.weights = weights or {
            'cpu': 1.0,
            'gpu': 1.0,
            'memory': 1.0,
            'io': 1.0,
            'network': 1.0
        }

    def filter_nodes(self, required_resources):
        """过滤可用节点，检查状态和资源是否充足。"""
        available_nodes = []
        for node in self.node_controller.list_nodes().values():
            if node['status'] != 'Ready':
                continue
            if self._has_sufficient_resources(node, required_resources):
                available_nodes.append(node)
        return available_nodes

    def _has_sufficient_resources(self, node, required_resources):
        """检查节点是否有足够的资源。"""
        return all(
            node['total_resources'][resource] >= required_resources.get(resource, 0)
            for resource in required_resources
        )

    def calculate_score(self, node):
        """计算节点的资源负载综合评分。"""
        total_score = 0
        for resource in ['cpu', 'gpu', 'memory', 'io', 'network']:
            total = node['total_resources'].get(resource, 1)  # 防止除以0
            used = node['used_resources'].get(resource, 0)
            usage_ratio = used / total
            total_score += usage_ratio * self.weights.get(resource, 1.0)
        return total_score

    def prioritize_nodes(self, available_nodes):
        """对可用节点进行优选。"""
        return sorted(available_nodes, key=self.calculate_score)

    def schedule_pod(self, pod : Pod, required_resources):
        """为 Pod 选择合适的节点。"""
        available_nodes = self.filter_nodes(required_resources)
        if not available_nodes:
            logging.error("No available nodes with sufficient resources.")
            raise Exception("No available nodes with sufficient resources.")

        prioritized_nodes = self.prioritize_nodes(available_nodes)
        selected_node = prioritized_nodes[0]
        logging.info(f"Scheduled Pod {pod.name} on node {selected_node['name']}.")
        self.node_controller.schedule_pod_to_node(pod, selected_node['name'])
  

# 示例配置文件格式 (config.yaml):
# scheduler:
#   nodes:
#     - name: "node-1"
#       status: "Ready"
#       total_resources:
#         cpu: 16
#         memory: 32768
#         gpu: 2
#         io: 5000
#         network: 10000
#       used_resources:
#         cpu: 4
#         memory: 8192
#         gpu: 0
#         io: 1000
#         network: 2000
#     - name: "node-2"
#       status: "Ready"
#       total_resources:
#         cpu: 8
#         memory: 16384
#         gpu: 1
#         io: 3000
#         network: 8000
#       used_resources:
#         cpu: 2
#         memory: 4096
#         gpu: 1
#         io: 500
#         network: 1000
