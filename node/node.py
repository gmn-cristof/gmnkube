import logging,re
import psutil
import GPUtil


class Node:
    def __init__(self, name, ip_address, total_cpu, total_memory, total_gpu, total_io, total_net, labels=None, annotations=None):
        """
        初始化 Node 对象。
        """
        # print(total_cpu)
        if total_cpu==0:
            total_cpu, total_memory,total_gpu,total_io,total_net =self._fetch_resource_info()

        # 确保资源值不为 None，使用 0 作为默认值
        self.name = name
        self.ip_address = ip_address
        self.total_cpu = total_cpu   # 默认值为 0
        self.total_memory = total_memory   # 默认值为 0
        self.total_gpu = total_gpu   # 默认值为 0
        self.total_io = total_io   # 默认值为 0
        self.total_net = total_net   # 默认值为 0
        self.labels = labels or {}
        self.annotations = annotations or {}
        total_cpu, total_memory,total_gpu,total_io,total_net =self._fetch_resource_info()

        # 初始化分配资源和状态
        self.allocated_cpu = 0
        self.allocated_memory = 0
        self.allocated_gpu = 0
        self.allocated_io = 0
        self.allocated_net = 0
        self.pods = []
        self.status = "Ready"



    def _fetch_resource_info(self):
        """
        获取系统资源信息，包括 CPU、内存、GPU、IO 和网络总量。
        """
        total_cpu = psutil.cpu_count(logical=True)  # 获取逻辑 CPU 数量
        total_memory = psutil.virtual_memory().total  # 获取总内存
        total_gpu = len(GPUtil.getGPUs())  # 获取 GPU 数量
        total_io = self._get_total_io()  # 自定义方法获取 IO 信息
        total_net = self._get_total_net()  # 自定义方法获取网络信息

        return total_cpu, total_memory, total_gpu, total_io, total_net

    def _get_total_io(self):
        """
        获取系统总 IO 信息（可以根据具体需求修改）。
        """
        # 示例：获取当前磁盘 IO 读写速率
        io_stats = psutil.disk_io_counters()
        total_io = io_stats.read_bytes + io_stats.write_bytes
        return total_io

    def _get_total_net(self):
        """
        获取系统总网络信息（可以根据具体需求修改）。
        """
        # 示例：获取所有网络接口的字节数
        net_io = psutil.net_io_counters()
        total_net = net_io.bytes_sent + net_io.bytes_recv
        return total_net
    
    def add_pod(self, pod):
        """在节点上运行一个新的 Pod，并更新资源分配。

        :param pod: 要添加的 Pod 对象
        """
        resources=pod.resources.get("requests", {})
        resources=self.convert_resources(resources)
        
        required_cpu = resources.get("cpu", 0)
        required_memory = resources.get("memory", 0)
        required_gpu = resources.get("gpu", 0)
        required_io = resources.get("io", 0)
        required_net = resources.get("net", 0)

        if self.can_schedule(required_cpu, required_memory, required_gpu, required_io, required_net):
            self.pods.append(pod)  # 添加 Pod 到节点
            # 更新已分配的资源
            self.allocated_cpu += required_cpu
            self.allocated_memory += required_memory
            self.allocated_gpu += required_gpu
            self.allocated_io += required_io
            self.allocated_net += required_net
            self._log_resource_warning()
        else:
            logging.error(f"Not enough resources on Node {self.name} to schedule Pod {pod.name}.")
            raise Exception(f"Not enough resources on Node {self.name} to schedule Pod {pod.name}.")
    
    def convert_resources(self,resource_dict):
        # CPU转换（假设单位是m，即毫核）
        cpu_str = resource_dict.get('cpu', '0m')
        if 'm' in cpu_str:
            cpu_value = int(cpu_str.replace('m', '')) / 1000  # 转换为核
        else:
            cpu_value = float(cpu_str)  # 如果没有m，直接转为浮动数值

        # 内存转换（假设单位是Mi）
        memory_str = resource_dict.get('memory', '0Mi')
        if 'Mi' in memory_str:
            memory_value = int(memory_str.replace('Mi', '')) * 1024 * 1024  # 转换为字节
        else:
            memory_value = int(memory_str)  # 其他单位可以按需转换

        # GPU转换（假设单位是个数）
        gpu_str = resource_dict.get('gpu', '0')
        gpu_value = int(gpu_str)  # 转换为整数

        return {
            'cpu': cpu_value,
            'memory': memory_value,
            'gpu': gpu_value
        }

# 示例
# resource_requests = {
#     'cpu': '100m',  # 100 毫核
#     'memory': '256Mi',  # 256 Mi 内存
#     'gpu': '1'  # 1 个 GPU
# }

# converted_resources = convert_resources(resource_requests)
# print(converted_resources)


    def remove_pod(self, pod):
        """从节点上移除一个 Pod，并释放相应资源。

        :param pod: 要移除的 Pod 对象
        """
        if pod in self.pods:
            self.pods.remove(pod)  # 从节点中移除 Pod
            # 释放相应资源
            THRESHOLD = 1e-6  # 定义误差阈值

            # 释放相应资源
            self.allocated_cpu -= self.parse_cpu(pod.resources.get('requests', {}).get('cpu', 0))
            self.allocated_cpu = 0.0 if abs(self.allocated_cpu) < THRESHOLD else self.allocated_cpu

            self.allocated_memory -= self.parse_memory(pod.resources.get('requests', {}).get('memory', 0))
            self.allocated_memory = 0.0 if abs(self.allocated_memory) < THRESHOLD else self.allocated_memory

            self.allocated_gpu -= self.parse_gpu(pod.resources.get('requests', {}).get('gpu', 0))
            self.allocated_gpu = 0.0 if abs(self.allocated_gpu) < THRESHOLD else self.allocated_gpu

            self.allocated_io -= pod.resources.get("requests", {}).get("io", 0)
            self.allocated_io = 0.0 if abs(self.allocated_io) < THRESHOLD else self.allocated_io

            self.allocated_net -= pod.resources.get("requests", {}).get("net", 0)
            self.allocated_net = 0.0 if abs(self.allocated_net) < THRESHOLD else self.allocated_net



            logging.info(f"Pod {pod.name} removed from Node {self.name}.")
            # 更新 etcd 中的节点状态
            #self.etcd_client.delete(f"/nodes/{self.name}/pods/{pod.name}")
        else:
            logging.warning(f"Attempted to remove non-existent Pod {pod.name} from Node {self.name}.")


    def can_schedule(self, required_cpu, required_memory, required_gpu, required_io, required_net):
        """检查节点是否有足够的资源调度 Pod。"""
        return (self.total_cpu - self.allocated_cpu >= required_cpu and
                self.total_memory - self.allocated_memory >= required_memory and
                self.total_gpu - self.allocated_gpu >= required_gpu and
                self.total_io - self.allocated_io >= required_io and
                self.total_net - self.allocated_net >= required_net)

    def set_status(self, status):
        """更新节点状态并同步至 etcd。"""
        self.status = status
        logging.info(f"Node {self.name} status updated to {status}.")
        # self.etcd_client.put(f"/nodes/{self.name}/status", status)

    def to_dict(self):
        """将节点信息转换为字典形式，包含资源使用比例，便于序列化。"""
        return {
            "name": self.name,
            "ip_address": self.ip_address,
            "total_cpu": self.total_cpu,
            "total_memory": self.total_memory,
            "total_gpu": self.total_gpu,
            "total_io": self.total_io,
            "total_net": self.total_net,
            "allocated_cpu": self.allocated_cpu,
            "allocated_memory": self.allocated_memory,
            "allocated_gpu": self.allocated_gpu,
            "allocated_io": self.allocated_io,
            "allocated_net": self.allocated_net,
            "cpu_usage_ratio": self.allocated_cpu / self.total_cpu if self.total_cpu > 0 else 0,
            "memory_usage_ratio": self.allocated_memory / self.total_memory if self.total_memory > 0 else 0,
            "pods": [pod.to_dict() for pod in self.pods],
            "status": self.status,
            "labels": self.labels,
            "annotations": self.annotations,
        }

    def _log_resource_warning(self):
        """检查资源使用比例，如果接近上限，则记录告警日志。"""
        if self.allocated_cpu / self.total_cpu > 0.8:
            logging.warning(f"Node {self.name} CPU usage above 80%.")
        if self.allocated_memory / self.total_memory > 0.8:
            logging.warning(f"Node {self.name} memory usage above 80%.")

    def get_node_info(self):
        """获取本机的 CPU、内存、GPU、IO 和网络资源信息。"""
        cpu_info = psutil.cpu_count(logical=True)  # 逻辑 CPU 数量
        memory_info = psutil.virtual_memory()  # 内存信息
        net_info = psutil.net_if_addrs()  # 网络接口信息
        io_info = psutil.disk_io_counters()  # IO 信息
        gpus = GPUtil.getGPUs()  # 获取 GPU 信息

        gpu_info = len(gpus)  # GPU 数量
        total_io = io_info.read_bytes + io_info.write_bytes  # 总 IO 读写字节
        total_net = sum([net.address for net in net_info.values()])  # 计算网络带宽总和（假设处理）

        return {
            "cpu": cpu_info,
            "memory": memory_info.total,
            "gpu": gpu_info,
            "io": total_io,
            "net": total_net,
        }

    def load_node_info(self):
        """将获取的资源信息加载到节点对象中。"""
        node_info = self.get_node_info()
        self.total_cpu = node_info['cpu']
        self.total_memory = node_info['memory']
        self.total_gpu = node_info['gpu']
        self.total_io = node_info['io']
        self.total_net = node_info['net']

        logging.info(f"Node {self.name} loaded resources: {node_info}")

    def parse_cpu(self, cpu_str):
        """解析 CPU 请求，返回核心数"""
        if isinstance(cpu_str, str):
            # 使用正则表达式捕获数字部分和单位（m 或空）
            match = re.match(r"(\d+(\.\d+)?)(m|)", cpu_str.strip())  # 加强正则表达式的匹配，允许小数部分
            if match:
                cpu_value, _, unit = match.groups()
                cpu_value = float(cpu_value)  # 转换为浮动数

                if unit == 'm':  # 如果是毫核，转换为核心数
                    return round(cpu_value / 1000, 6)  # 将毫核转换为核心数并控制精度
                else:
                    return round(cpu_value, 6)  # 核心数本身，控制精度
        return 0.0

    def parse_memory(self, mem_str):
        """解析内存请求，返回字节数"""
        if isinstance(mem_str, str):
            match = re.match(r"(\d+)(Ki|Mi|Gi|Ti)", mem_str)
            if match:
                mem_value, unit = match.groups()
                mem_value = float(mem_value)
                if unit == 'Ki':  # KiB -> 字节
                    return int(mem_value * 1024)
                elif unit == 'Mi':  # MiB -> 字节
                    return int(mem_value * 1024 * 1024)
                elif unit == 'Gi':  # GiB -> 字节
                    return int(mem_value * 1024 * 1024 * 1024)
                elif unit == 'Ti':  # TiB -> 字节
                    return int(mem_value * 1024 * 1024 * 1024 * 1024)
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
