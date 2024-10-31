import numpy as np
import tensorflow as tf
from collections import deque
import random
import logging

class DDQNScheduler:
    def __init__(self, node_controller, config = {}):
        """
        初始化 DDQN 调度器。

        :param node_controller: NodeController 实例，用于节点管理
        :param state_size: 状态空间大小
        :param action_size: 动作空间大小
        :param config: 配置字典，包含超参数
        """
        # 配置超参数
        self.config = {
            'gamma': 0.95,
            'epsilon': 1.0,
            'epsilon_min': 0.01,
            'epsilon_decay': 0.995,
            'learning_rate': 0.001,
            'batch_size': 32
        }
        self.node_controller = node_controller
        self.state_size = 6  # 动态计算状态大小  self._calculate_state_size()
        self.action_size = len(self.node_controller.nodes)  # 根据节点数量动态设置动作大小
        self.gamma = config.get('gamma', 0.95)
        self.epsilon = config.get('epsilon', 1.0)
        self.epsilon_min = config.get('epsilon_min', 0.01)
        self.epsilon_decay = config.get('epsilon_decay', 0.995)
        self.learning_rate = config.get('learning_rate', 0.001)
        self.memory = deque(maxlen=2000)
        self.model = self._build_model()
        self.target_model = self._build_model()  # 目标网络
        self.batch_size = config.get('batch_size', 32)
        self.update_target_frequency = 10  # 目标网络更新频率
        self.update_counter = 0  # 记录更新次数

    def _build_model(self):
        """构建深度 Q 网络模型。"""
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.Dense(64, input_dim=self.state_size, activation='relu'))
        model.add(tf.keras.layers.Dense(64, activation='relu'))
        model.add(tf.keras.layers.Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate))
        return model

    def remember(self, state, action, reward, next_state, done):
        """将经历存储到记忆中。"""
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        """根据当前状态选择动作。"""
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])  # 返回最大 Q 值的动作

    def replay(self):
        """从记忆中抽样并训练模型。"""
        if len(self.memory) < self.batch_size:
            return
        minibatch = random.sample(self.memory, self.batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target += self.gamma * np.amax(self.target_model.predict(next_state)[0])  # 使用目标网络
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        # 更新目标网络
        self.update_counter += 1
        if self.update_counter % self.update_target_frequency == 0:
            self.update_target_network()

    def update_target_network(self):
        """更新目标网络的权重。"""
        self.target_model.set_weights(self.model.get_weights())

    def schedule_pod(self, pod):
        """为 Pod 调度选择节点。"""
        state = self._get_state()  # 从节点获取当前状态
        action = self.act(state)
        node_name = self._get_node_from_action(action)

        # 调度 Pod
        try:
            self.node_controller.schedule_pod_to_node(pod, node_name)
            next_state = self._get_state()  # 获取下一个状态
            reward = self._calculate_reward(node_name)  # 计算调度的奖励
            done = False  # 根据需要设定完成条件
            self.remember(state, action, reward, next_state, done)
            self.replay()
        except Exception as e:
            logging.error(f"Failed to schedule Pod {pod.name} to Node {node_name}: {e}")

    def _get_state(self):
        """获取当前系统状态，返回状态向量。"""
        states = []
        for node in self.node_controller.nodes.values():
            states.append([
                node.allocated_cpu,
                node.allocated_memory,
                node.allocated_gpu,
                node.total_gpu - node.allocated_gpu, #剩余  GPU
                node.total_cpu - node.allocated_cpu,  # 剩余 CPU
                node.total_memory - node.allocated_memory  # 剩余内存
            ])
        return np.array(states).reshape(1, -1)

    def _get_node_from_action(self, action):
        """根据动作选择节点名称。"""
        node_names = list(self.node_controller.nodes.keys())
        return node_names[action]

    def _calculate_reward(self, node_name):
        """计算调度的奖励，可以根据节点资源利用率、Pod 性能等因素设计。"""
        node = self.node_controller.get_node(node_name)
        
        # 成功调度
        if node.status == "Ready":
            # 计算资源利用率
            cpu_usage_ratio = node.allocated_cpu / node.total_cpu if node.total_cpu > 0 else 0
            memory_usage_ratio = node.allocated_memory / node.total_memory if node.total_memory > 0 else 0
            gpu_usage_ratio = node.allocated_gpu / node.total_gpu if node.total_gpu > 0 else 0

            # 计算基础奖励
            reward = 1 - (cpu_usage_ratio + memory_usage_ratio + gpu_usage_ratio) / 3  # 利用率越低，奖励越高

            # 计算所有节点的资源利用率
            cpu_utilizations = [n.allocated_cpu / n.total_cpu if n.total_cpu > 0 else 0 for n in self.node_controller.nodes.values()]
            memory_utilizations = [n.allocated_memory / n.total_memory if n.total_memory > 0 else 0 for n in self.node_controller.nodes.values()]
            gpu_utilizations = [n.allocated_gpu / n.total_gpu if n.total_gpu > 0 else 0 for n in self.node_controller.nodes.values()]

            # 负载均衡考量
            cpu_load_balance_factor = 1 / (1 + np.std(cpu_utilizations))
            memory_load_balance_factor = 1 / (1 + np.std(memory_utilizations))
            gpu_load_balance_factor = 1 / (1 + np.std(gpu_utilizations))

            # 加权负载均衡影响
            reward += (cpu_load_balance_factor + memory_load_balance_factor + gpu_load_balance_factor) / 3 * 0.5

            return reward
        return -1