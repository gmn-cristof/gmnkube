import logging
import re,datetime
from node.node_controller import NodeController
import numpy as np
import matplotlib.pyplot as plt
import os


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
        self.schedule_history = []  # 每次调度的 Pod 名称、目标节点、奖励和时间戳

    def filter_nodes(self, required_resources):
        """过滤可用节点，检查状态和资源是否充足。"""
        available_nodes = []
        for node in self.node_controller.nodes.values():
            if node.status != 'Ready':
                continue
            if self._has_sufficient_resources(node, required_resources):
                available_nodes.append(node)
        return available_nodes

    def _has_sufficient_resources(self, node, required_resources):
        """
        检查节点是否有足够的资源以满足要求。
        :param node: 节点实例
        :param required_resources: 需要的资源字典 {'cpu': x, 'memory': y, 'gpu': z}
        :return: True 如果资源充足，否则返回 False
        """
        required_cpu = required_resources.get('cpu', 0)
        required_memory = required_resources.get('memory', 0)
        required_gpu = required_resources.get('gpu', 0)

        # 检查 CPU、内存、GPU 是否足够
        if (node.total_cpu - node.allocated_cpu) < required_cpu or \
           (node.total_memory - node.allocated_memory) < required_memory or \
           (node.total_gpu - node.allocated_gpu) < required_gpu:

            return False  # 资源不足，返回 False
        return True  # 资源充足，返回 True

    def calculate_score(self, node):
        """计算节点的资源负载综合评分。"""
        total_score = 0
        cpu_ratio=node.allocated_cpu / node.total_cpu if node.total_cpu > 0 else 0
        total_score += cpu_ratio * self.weights.get('cpu', 1.0)
        gpu_ratio=node.allocated_gpu / node.total_gpu if node.total_gpu > 0 else 0
        total_score += gpu_ratio * self.weights.get('gpu', 1.0)
        mem_ratio=node.allocated_memory / node.total_memory if node.total_memory > 0 else 0
        total_score += mem_ratio * self.weights.get('mem', 1.0)
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
            'gpu': self.parse_gpu(pod.resources.get('requests', {}).get('gpu', 0))
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

        logging.info(f"Scheduled Pod {pod.name} on node {selected_node.name}.")

        # 调用 NodeController 将 Pod 调度到目标节点
        reward=self._calculate_reward(selected_node.name,pod)
        self.node_controller.schedule_pod_to_node(pod, selected_node.name)
        
        self.schedule_history.append({
            'pod_name': pod.name,
            'node_name': selected_node.name,
            'reward': reward,
            'timestamp': datetime.datetime.now()
        })
        logging.info(f"[DDQN-Scheduler-INFO]: Pod {pod.name} scheduled to Node {selected_node.name} with reward: {reward}")
        return selected_node.name

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
    
    def parse_gpu(self, gpu_str):
        """解析 GPU 请求，返回 GPU 数量"""
        if isinstance(gpu_str, str):
            match = re.match(r"(\d+)(Gpu|)", gpu_str, re.IGNORECASE)  # 匹配数字和 'Gpu' 或空
            if match:
                gpu_value, unit = match.groups()
                gpu_value = int(gpu_value)
                if unit.lower() == 'gpu':  # 如果单位为 'GPU'，直接返回数量
                    return gpu_value
                else:
                    return gpu_value  # 如果没有单位，也直接返回数量
        return 0  # 默认返回 0，表示没有请求 GPU
    
    def _calculate_reward(self, node_name, pod):
        # 计算调度到指定节点的奖励
        node = self.node_controller.get_node(node_name)  # 获取节点信息
        if node.status == "Ready":  # 如果节点状态为就绪
            # 检查节点是否能满足 Pod 的资源需求
            required_cpu = self.parse_cpu(pod.resources.get('requests', {}).get('cpu', 0)) 
            required_memory = self.parse_memory(pod.resources.get('requests', {}).get('memory', 0)) 
            required_gpu = self.parse_gpu(pod.resources.get('requests', {}).get('gpu', 0) )
            if (node.total_cpu - node.allocated_cpu) < required_cpu or \
               (node.total_memory - node.allocated_memory) < required_memory or \
               (node.total_gpu - node.allocated_gpu) < required_gpu:
                print(f"Node {node.name} insufficient resources:")
                print(f"Remaining CPU: {node.total_cpu - node.allocated_cpu}, Required: {required_cpu}")
                print(f"Remaining Memory: {node.total_memory - node.allocated_memory}, Required: {required_memory}")
                print(f"Remaining GPU: {node.total_gpu - node.allocated_gpu}, Required: {required_gpu}")
                return -1  # 资源不足，给予负奖励
            
            cpu_usage_ratio = node.allocated_cpu / node.total_cpu if node.total_cpu > 0 else 0
            memory_usage_ratio = node.allocated_memory / node.total_memory if node.total_memory > 0 else 0
            gpu_usage_ratio = node.allocated_gpu / node.total_gpu if node.total_gpu > 0 else 0
            
            reward = 1 - (cpu_usage_ratio + memory_usage_ratio + gpu_usage_ratio) / 3  # 计算基础奖励

            # 负载均衡因子
            cpu_utilizations = [n.allocated_cpu / n.total_cpu if n.total_cpu > 0 else 0 for n in self.node_controller.nodes.values()]
            memory_utilizations = [n.allocated_memory / n.total_memory if n.total_memory > 0 else 0 for n in self.node_controller.nodes.values()]
            gpu_utilizations = [n.allocated_gpu / n.total_gpu if n.total_gpu > 0 else 0 for n in self.node_controller.nodes.values()]
            
            cpu_load_balance_factor = 1 / (1 + np.std(cpu_utilizations))  # CPU 负载均衡因子
            memory_load_balance_factor = 1 / (1 + np.std(memory_utilizations))  # 内存负载均衡因子
            gpu_load_balance_factor = 1 / (1 + np.std(gpu_utilizations))  # GPU 负载均衡因子

            # 加权综合奖励
            reward += (cpu_load_balance_factor + memory_load_balance_factor + gpu_load_balance_factor) / 3 * 0.5

            return reward  # 返回计算的奖励
        return -1  # 如果节点不就绪，返回惩罚
    
    def get_schedule_history(self):
        return self.schedule_history
    
    def save_schedule_history(self, file_path="schedule_history.png"):
        """
        将调度历史记录可视化并保存为图片。
        :param file_path: 保存的文件路径，默认为 'schedule_history.png'
        """
        # 检查是否有历史记录
        if not self.schedule_history:
            print("No scheduling history available for visualization.")
            return

        # 提取数据
        timestamps = [record['timestamp'] for record in self.schedule_history]
        pod_names = [record['pod_name'] for record in self.schedule_history]
        node_names = [record['node_name'] for record in self.schedule_history]
        rewards = [record['reward'] for record in self.schedule_history]

        # 转换时间戳为数字格式
        time_numeric = [ts.timestamp() for ts in timestamps]

        # 创建图形
        plt.figure(figsize=(12, 6))

        # 子图1：节点分布
        plt.subplot(2, 1, 1)
        plt.scatter(time_numeric, node_names, c='blue', alpha=0.7, label='Scheduled Nodes')
        plt.yticks(rotation=45)
        plt.xlabel("Time")
        plt.ylabel("Node Names")
        plt.title("Pod Scheduling History")
        plt.legend()

        # 子图2：奖励值趋势
        plt.subplot(2, 1, 2)
        plt.plot(time_numeric, rewards, '-o', color='green', label='Reward Trend')
        plt.xlabel("Time")
        plt.ylabel("Reward")
        plt.title("Reward Over Time")
        plt.legend()

        # 调整布局并保存图形
        plt.tight_layout()
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保文件目录存在
        plt.savefig(file_path)
        plt.close()
        print(f"Schedule history visualization saved to {file_path}.")

  

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
