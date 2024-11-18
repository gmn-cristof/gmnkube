import logging
import re
from node.node_controller import NodeController

# 配置 logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Kube_Scheduler_Plus:
    def __init__(self, node_controller: NodeController, weights=None):
        """
        初始化 KubeSchedulerPlus，连接 NodeController 并加载节点信息。
        :param node_controller: NodeController 实例
        :param weights: 资源权重字典（例如: {'cpu': 1.0, 'gpu': 2.0, 'memory': 1.5}）
        """
        self.node_controller = node_controller
        self.weights = weights or {
            'cpu': 1.0,
            'gpu': 1.0,
            'memory': 1.0
        }

    def filter_nodes(self, required_resources):
        """过滤可用节点，检查状态和资源是否充足。"""
        available_nodes = []
        for node in self.node_controller.list_nodes().values():
            if node.get('status') != 'Ready':
                continue
            if self._has_sufficient_resources(node, required_resources):
                available_nodes.append(node)
        return available_nodes

    def _has_sufficient_resources(self, node, required_resources):
        """检查节点是否有足够的资源。"""
        for resource, required in required_resources.items():
            total = node['total_resources'].get(resource, 0)
            used = node['used_resources'].get(resource, 0)
            available = total - used
            if available < required:
                return False
        return True

    def calculate_score(self, node):
        """计算节点的资源负载综合评分。"""
        total_score = 0
        for resource in ['cpu', 'gpu', 'memory']:
            total = node['total_resources'].get(resource, 1)  # 防止除以 0
            used = node['used_resources'].get(resource, 0)
            usage_ratio = used / total if total > 0 else 1.0  # 若总量为 0，使用率设为 1.0
            total_score += usage_ratio * self.weights.get(resource, 1.0)
        return total_score

    def prioritize_nodes(self, available_nodes):
        """对可用节点进行优选排序。"""
        return sorted(available_nodes, key=self.calculate_score)

    def schedule_pod(self, pod):
        """为 Pod 选择合适的节点。"""
        # 从 Pod 中获取资源需求
        required_resources = {
            'cpu': self.parse_cpu(pod.resources.get('requests', {}).get('cpu', "0")),
            'memory': self.parse_memory(pod.resources.get('requests', {}).get('memory', "0")),
            'gpu': pod.resources.get('requests', {}).get('gpu', 0)
        }

        # 过滤节点，找到满足资源需求的可用节点
        available_nodes = self.filter_nodes(required_resources)
        if not available_nodes:
            logging.error("No available nodes with sufficient resources.")
            raise Exception("No available nodes with sufficient resources.")

        # 根据负载评分对节点进行优先级排序
        prioritized_nodes = self.prioritize_nodes(available_nodes)

        # 选择优先级最高的节点
        selected_node = prioritized_nodes[0]

        logging.info(f"Scheduled Pod {pod.name} on node {selected_node['name']}.")

        # 调用 NodeController 将 Pod 调度到目标节点
        self.node_controller.schedule_pod_to_node(pod, selected_node['name'])

    def parse_cpu(self, cpu_str):
        """解析 CPU 请求，返回核心数"""
        if isinstance(cpu_str, str):
            match = re.match(r"(\d+)(m|)", cpu_str)
            if match:
                cpu_value, unit = match.groups()
                cpu_value = float(cpu_value)
                if unit == 'm':  # 如果是毫核，转换为核心数
                    return cpu_value / 1000
                return cpu_value
        logging.warning(f"Invalid CPU format: {cpu_str}")
        return 0.0

    def parse_memory(self, mem_str):
        """解析内存请求，返回字节数"""
        if isinstance(mem_str, str):
            match = re.match(r"(\d+)(Ki|Mi|Gi|Ti|)", mem_str)
            if match:
                mem_value, unit = match.groups()
                mem_value = float(mem_value)
                unit_conversion = {
                    'Ki': 1024,
                    'Mi': 1024 ** 2,
                    'Gi': 1024 ** 3,
                    'Ti': 1024 ** 4,
                }
                return int(mem_value * unit_conversion.get(unit, 1))  # 默认为字节
        logging.warning(f"Invalid memory format: {mem_str}")
        return 0

  

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
