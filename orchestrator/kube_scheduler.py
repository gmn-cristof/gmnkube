import logging
from node.node_controller import NodeController

# 配置 logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Kube_Scheduler:
    def __init__(self, etcd_host='localhost', etcd_port=2379):
        """
        初始化 KubeSchedulerCPUMem，连接 etcd 并加载节点信息。
        :param etcd_host: etcd 主机
        :param etcd_port: etcd 端口
        :param config_file: 配置文件路径
        """
        self.node_controller = NodeController(etcd_host, etcd_port)

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
        """检查节点是否有足够的 CPU 和内存资源。"""
        return (
            node['total_resources']['cpu'] >= required_resources.get('cpu', 0) and
            node['total_resources']['memory'] >= required_resources.get('memory', 0)
        )

    def calculate_score(self, node):
        """计算节点的 CPU 和内存负载综合评分。"""
        total_cpu = node['total_resources']['cpu']
        used_cpu = node['used_resources'].get('cpu', 0)
        cpu_usage_ratio = used_cpu / total_cpu

        total_memory = node['total_resources']['memory']
        used_memory = node['used_resources'].get('memory', 0)
        memory_usage_ratio = used_memory / total_memory

        # 评分计算，使用加权和
        return cpu_usage_ratio + memory_usage_ratio

    def prioritize_nodes(self, available_nodes):
        """对可用节点进行优选。"""
        return sorted(available_nodes, key=self.calculate_score)

    def schedule_pod(self, pod_name: str, required_resources):
        """为 Pod 选择合适的节点。"""
        available_nodes = self.filter_nodes(required_resources)
        if not available_nodes:
            logging.error("No available nodes with sufficient resources.")
            raise Exception("No available nodes with sufficient resources.")

        prioritized_nodes = self.prioritize_nodes(available_nodes)
        selected_node = prioritized_nodes[0]
        logging.info(f"Scheduled Pod {pod_name} on node {selected_node['name']}.")
        self.node_controller.schedule_pod_to_node(pod_name, selected_node['name'])



# 示例配置文件格式 (config.yaml):
# scheduler:
#   nodes:
#     - name: "node-1"
#       status: "Ready"
#       total_resources:
#         cpu: 16
#         memory: 32768
#         gpu: 2
#       used_resources:
#         cpu: 4
#         memory: 8192
#         gpu: 0
#     - name: "node-2"
#       status: "NotReady"
#       total_resources:
#         cpu: 8
#         memory: 16384
#         gpu: 1
#       used_resources:
#         cpu: 2
#         memory: 4096
#         gpu: 0
