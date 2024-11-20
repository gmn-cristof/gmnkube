import numpy as np
import tensorflow as tf
from collections import deque
import random
import logging
import re

NODE_COUNT = 10
POD_COUNT = 30

class DDQNScheduler:
    def __init__(self, node_controller):
        # 初始化调度器
        self.config = {
            'gamma': 0.95,  # 折扣因子
            'epsilon': 1.0,  # 初始探索率
            'epsilon_min': 0.01,  # 最小探索率
            'epsilon_decay': 0.995,  # 探索率衰减
            'learning_rate': 0.001,  # 学习率
            'batch_size': 8  # 批次大小
        }
        self.node_controller = node_controller  # 节点控制器
        self.state_size = NODE_COUNT * 9  # 状态大小，包含节点和 Pod 的资源信息
        self.action_size = NODE_COUNT #len(self.node_controller.nodes)  
        # 动作大小，即节点数量
        self.memory = deque(maxlen=2000)  # 经验回放内存
        self.model = self._build_model()  # 主模型
        self.target_model = self._build_model()  # 目标模型
        self.update_target_frequency = 10  # 更新目标网络的频率
        self.update_counter = 0  # 更新计数器

    def _update_action_size(self):
        # 更新 action_size 和模型的输出层大小
        self.action_size = len(self.node_controller.nodes)  # 动态获取节点数
        self.model = self._build_model()  # 重新构建模型
        self.target_model = self._build_model()  # 重新构建目标模型

    def _build_model(self):
        # 计算 state_size（节点数 * 每个节点的特征数量）
        #self.state_size = len(self.node_controller.nodes) * 9  # 每个节点 9 个特征

        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Input(shape=(self.state_size,)))  # 输入层
        model.add(tf.keras.layers.Dense(4, activation='relu'))  # 隐藏层1
        model.add(tf.keras.layers.Dense(8, activation='relu'))  # 隐藏层2
        model.add(tf.keras.layers.Dense(self.action_size, activation='linear'))  # 输出层
        model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(learning_rate=self.config['learning_rate']))  # 编译模型
        return model


    @tf.function
    def train_model(self, state, target_f):
        # 训练模型
        with tf.GradientTape() as tape:  # 记录梯度
            loss_fn = tf.keras.losses.MeanSquaredError()
            loss = loss_fn(target_f, self.model(state))  # 计算损失
        grads = tape.gradient(loss, self.model.trainable_variables)  # 计算梯度
        self.model.optimizer.apply_gradients(zip(grads, self.model.trainable_variables))  # 应用梯度更新
        return loss

    @tf.function
    def predict(self, state):
        # 使用模型进行预测
        return self.model(state)


    def remember(self, state, action, reward, next_state, done):
        # 存储经历到经验回放内存
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        # 根据当前状态选择动作
        if self.action_size == 0:
            logging.error("No nodes available for scheduling.")
            return 0  # 或者可以返回一个默认值，或者抛出异常
        if np.random.rand() <= self.config['epsilon']:  # 选择最佳动作
            return self.select_best_node(state)
        act_values = self.predict(state)  # 使用模型预测动作值
        return np.argmax(act_values[0])  # 选择最大动作值对应的动作

    def replay(self):
        if len(self.memory) < self.config['batch_size']:
            return
        minibatch = random.sample(self.memory, self.config['batch_size'])
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                next_state_prediction = self.target_model.predict(next_state)
                target += self.config['gamma'] * np.amax(next_state_prediction)
            
            # 确保 target_f 是一个可变的 NumPy 数组
            target_f = tf.Variable(self.predict(state))
            target_f = tf.reshape(target_f, (1, -1))
            target_f = target_f.numpy()  # 转为 NumPy 数组
            target_f[0][action] = target  # 更新动作值

            # 训练模型
            self.train_model(
                tf.convert_to_tensor(state, dtype=tf.float32),
                tf.convert_to_tensor(target_f, dtype=tf.float32)
            )
        
        # 更新 epsilon
        if self.config['epsilon'] > self.config['epsilon_min']:
            self.config['epsilon'] *= self.config['epsilon_decay']
        
        # 更新目标网络
        self.update_counter += 1
        if self.update_counter % self.update_target_frequency == 0:
            self.update_target_network()


    def update_target_network(self):
        # 更新目标网络的权重
        self.target_model.set_weights(self.model.get_weights())

    def schedule_pod(self, pod):
        # 调度 Pod 到节点
        #print(89898989898)
        if self.action_size != len(self.node_controller.nodes):
            self._update_action_size()  # 每次调度前动态更新 action_size
        
        #print(123123123123123)
        state = self._get_state(pod)  # 获取当前状态，传入 Pod
        #print("aaaaaaaaaa")
        action = self.act(state)  # 选择动作
        #print(565656565656)
        node_name = self._get_node_from_action(action)  # 根据动作获取节点名称
        
        # 记录调度信息
        logging.info(f"[DDQN-Scheduler-INFO]: Trying to schedule Pod {pod.name} to Node {node_name}. Action: {action}")
        #print(6666666666666666666666)
        try:
            # 尝试将 Pod 调度到选定的节点
            self.node_controller.schedule_pod_to_node(pod, node_name)
            next_state = self._get_state(pod)  # 获取下一个状态
            reward = self._calculate_reward(node_name, pod)  # 计算奖励
            
            # 记录奖励信息
            logging.info(f"[DDQN-Scheduler-INFO]: Pod {pod.name} scheduled to Node {node_name} with reward: {reward}")
            
            done = False  # 结束标志
            self.remember(state, action, reward, next_state, done)  # 记住经历
            self.replay()  # 进行回放训练
        
        except Exception as e:
            logging.error(f"[DDQN-Scheduler-ERROR]: Failed to schedule Pod {pod.name} to Node {node_name}: {e}")  # 记录错误

        return node_name

    def _get_state(self, pod):
        # 获取当前系统状态，并加入 Pod 的资源需求
        states = []
        required_cpu = self.parse_cpu(pod.resources.get('requests', {}).get('cpu', 0)) 
        required_memory = self.parse_memory(pod.resources.get('requests', {}).get('memory', 0)) 
        required_gpu = self.parse_gpu(pod.resources.get('requests', {}).get('gpu', 0) )
        for node in self.node_controller.nodes.values():
            states.append([
                node.allocated_cpu,
                node.allocated_memory,
                node.allocated_gpu,
                node.total_cpu - node.allocated_cpu,
                node.total_memory - node.allocated_memory,
                node.total_gpu - node.allocated_gpu,
                required_cpu,  # Pod 所需 CPU
                required_memory,  # Pod 所需内存
                required_gpu   # Pod 所需 GPU
            ])
        return np.array(states).reshape(1, -1)

    def _get_node_from_action(self, action):
        # 根据动作获取节点名称
        node_names = list(self.node_controller.nodes.keys())
        return node_names[action]

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
    
    
    def parse_cpu(self, cpu_str):
        """解析 CPU 请求，返回核心数"""
        if isinstance(cpu_str, str):
            match = re.match(r"(\d+)(m|)", cpu_str)
            if match:
                cpu_value, unit = match.groups()
                cpu_value = float(cpu_value)
                if unit == 'm':  # 如果是毫核，转换为核心数
                    return cpu_value / 1000  # 毫核转换为核心数
                else:
                    return cpu_value  # 核心数本身
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

    def calculate_score(self, state):
        """
        根据状态计算节点负载评分
        :param state: 单个节点的状态向量
        :return: 节点的评分（数值越低越优），如果无法满足需求返回正无穷大
        """
        (
            allocated_cpu, allocated_memory, allocated_gpu,
            free_cpu, free_memory, free_gpu,
            required_cpu, required_memory, required_gpu
        ) = state

        # 检查节点是否能满足需求
        if free_cpu < required_cpu or free_memory < required_memory or free_gpu < required_gpu:
            return float('inf')

        # 避免除零问题，并计算总资源量
        total_cpu = max(allocated_cpu + free_cpu, 1)
        total_memory = max(allocated_memory + free_memory, 1)
        total_gpu = max(allocated_gpu + free_gpu, 1)

        # 简单评分逻辑：综合资源占用率和剩余资源比例
        utilization_score = (allocated_cpu / total_cpu) + (allocated_memory / total_memory) + (allocated_gpu / total_gpu)
        remaining_score = (free_cpu - required_cpu) / total_cpu + (free_memory - required_memory) / total_memory + (free_gpu - required_gpu) / total_gpu

        # 分数越低越优，直接相加即可
        score = utilization_score - remaining_score

        return score

    def select_best_node(self, states):
        """
        选择最佳节点
        :param states: 所有节点的状态二维数组 (1, nodes_length * features)
        :return: 最佳节点的序号（0 到 nodes_length-1）
        """
        # 将二维数组转化为单节点状态列表
        num_nodes = states.shape[1] // 9  # 每个节点状态有 9 个特征
        reshaped_states = states.reshape(num_nodes, 9)

        best_node_index = -1
        best_score = float('inf')  # 初始化为正无穷

        for index, state in enumerate(reshaped_states):
            score = self.calculate_score(state)
            if score < best_score:
                best_score = score
                best_node_index = index

        return best_node_index

