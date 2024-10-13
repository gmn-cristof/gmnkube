import yaml

class kube_Scheduler:
    def __init__(self):
        # 从配置文件中加载节点信息
        with open('config/config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
            self.nodes = config['scheduler']['nodes']

    def filter_nodes(self, required_resources):
        """
        过滤不可用节点，根据节点是否有足够的资源和状态是否为 'Ready'。
        
        :param required_resources: 要求的资源字典 (例如: {'cpu': 2, 'memory': 1024})
        :return: 可用节点的列表
        """
        available_nodes = []
        for node in self.nodes:
            # 假设每个节点有 'resources' 和 'status' 两个字段
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

    def prioritize_nodes(self, available_nodes):
        """
        对节点进行优选，选择资源使用率最低的节点。
        
        :param available_nodes: 过滤后的可用节点列表
        :return: 根据负载排序的节点列表
        """
        def resource_usage(node):
            # 计算资源使用率，越低越好，假设每个节点有 'used_resources' 和 'total_resources' 字段
            total_usage = 0
            for resource in node['total_resources']:
                used = node['used_resources'].get(resource, 0)
                total = node['total_resources'][resource]
                total_usage += (used / total) if total > 0 else 0
            return total_usage

        # 根据资源使用率进行升序排序，使用率最低的节点优先
        return sorted(available_nodes, key=resource_usage)

    def schedule_container(self, container_name: str, required_resources):
        """
        根据过滤和优选的步骤调度容器。
        
        :param container_name: 容器名称
        :param required_resources: 容器所需的资源字典
        :return: 被选中的节点
        """
        # 1. 过滤节点
        available_nodes = self.filter_nodes(required_resources)
        if not available_nodes:
            raise Exception("No available nodes with sufficient resources.")
        
        # 2. 优选节点
        prioritized_nodes = self.prioritize_nodes(available_nodes)
        
        # 选择优选列表中的第一个节点（资源最空闲的节点）
        selected_node = prioritized_nodes[0]
        
        print(f"Scheduled container {container_name} on node {selected_node['name']}.")
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
