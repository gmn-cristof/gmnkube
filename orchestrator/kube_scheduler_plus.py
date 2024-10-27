import yaml
import logging

# 配置 logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KubeSchedulerPlus:
    def __init__(self, weights=None):
        """
        初始化调度器，并从配置文件加载节点信息。
        :param weights: 一个字典，定义每种资源的权重 (例如: {'cpu': 1.0, 'gpu': 2.0, 'memory': 1.5})
        """
        # 默认的权重，如果未传入，则使用平衡的权重
        self.weights = weights or {
            'cpu': 1.0,
            'gpu': 1.0,
            'memory': 1.0,
            'io': 1.0,
            'network': 1.0
        }
        with open('config/config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
            self.nodes = config['scheduler']['nodes']

    def filter_nodes(self, required_resources):
        """
        过滤节点，排除不满足资源需求或状态不可用的节点。
        :param required_resources: Pod 所需资源的字典（如 {'cpu': 2, 'gpu': 1, 'memory': 2048, 'io': 100, 'network': 1000}）
        :return: 过滤后可用节点的列表
        """
        available_nodes = []
        for node in self.nodes:
            if node['status'] != 'Ready':
                continue
            
            sufficient_resources = True
            for resource, amount in required_resources.items():
                if node['resources'].get(resource, 0) < amount:
                    sufficient_resources = False
                    break

            if sufficient_resources:
                available_nodes.append(node)
        
        return available_nodes

    def calculate_score(self, node):
        """
        计算节点的资源负载综合评分。分数越低，表示负载越低。
        :param node: 节点信息字典
        :return: 综合评分（浮点数）
        """
        total_score = 0
        for resource in ['cpu', 'gpu', 'memory', 'io', 'network']:
            total = node['total_resources'].get(resource, 1)  # 防止除以0
            used = node['used_resources'].get(resource, 0)
            usage_ratio = used / total
            # 根据权重调整每种资源的占比
            total_score += usage_ratio * self.weights.get(resource, 1.0)
        
        return total_score

    def prioritize_nodes(self, available_nodes):
        """
        对可用节点进行优选，选择资源使用率最低的节点。
        :param available_nodes: 过滤后的可用节点列表
        :return: 按照优选结果排序的节点列表
        """
        # 按照节点资源评分进行升序排序
        return sorted(available_nodes, key=self.calculate_score)

    def schedule_pod(self, pod_name: str, required_resources):
        """
        根据调度算法为 Pod 选择合适的节点。
        :param pod_name: Pod 名称
        :param required_resources: Pod 所需的资源字典
        :return: 被选中的节点
        """
        # 1. 过滤节点
        available_nodes = self.filter_nodes(required_resources)
        if not available_nodes:
            logging.error("No available nodes with sufficient resources.")
            raise Exception("No available nodes with sufficient resources.")

        # 2. 优选节点
        prioritized_nodes = self.prioritize_nodes(available_nodes)

        # 选择资源负载最低的节点
        selected_node = prioritized_nodes[0]
        logging.info(f"Scheduled Pod {pod_name} on node {selected_node['name']}.")
        return selected_node

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
