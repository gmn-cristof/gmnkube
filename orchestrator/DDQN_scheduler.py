import numpy as np
import tensorflow as tf
from collections import deque
import random
import logging

class DDQNScheduler:
    def __init__(self, node_controller):
        # 初始化调度器
        self.config = {
            'gamma': 0.95,  # 折扣因子
            'epsilon': 1.0,  # 初始探索率
            'epsilon_min': 0.01,  # 最小探索率
            'epsilon_decay': 0.995,  # 探索率衰减
            'learning_rate': 0.001,  # 学习率
            'batch_size': 4  # 批次大小
        }
        self.node_controller = node_controller  # 节点控制器
        self.state_size = 9  # 状态大小，包含节点和 Pod 的资源信息
        self.action_size = len(self.node_controller.nodes)  # 动作大小，即节点数量
        self.memory = deque(maxlen=2000)  # 经验回放内存
        self.model = self._build_model()  # 主模型
        self.target_model = self._build_model()  # 目标模型
        self.update_target_frequency = 10  # 更新目标网络的频率
        self.update_counter = 0  # 更新计数器

    def _build_model(self):
        # 构建深度学习模型
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
            loss = tf.keras.losses.mean_squared_error(target_f, self.model(state))  # 计算损失
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
        if np.random.rand() <= self.config['epsilon']:  # 随机选择动作
            return random.randrange(self.action_size)
        act_values = self.predict(state)  # 使用模型预测动作值
        return np.argmax(act_values[0])  # 选择最大动作值对应的动作

    def replay(self):
        # 从经验回放中采样并训练模型
        if len(self.memory) < self.config['batch_size']:  # 如果经验不足，返回
            return
        minibatch = random.sample(self.memory, self.config['batch_size'])  # 随机采样一批经历
        for state, action, reward, next_state, done in minibatch:
            target = reward  # 初始化目标值
            if not done:  # 如果未结束，更新目标值
                target += self.config['gamma'] * np.amax(self.target_model.predict(next_state)[0])  # 计算目标
            target_f = self.predict(state)  # 预测当前状态的目标值
            target_f[0][action] = target  # 更新目标值
            self.train_model(tf.convert_to_tensor(state, dtype=tf.float32), tf.convert_to_tensor(target_f, dtype=tf.float32))  # 训练模型

        # 更新探索率
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
        state = self._get_state(pod)  # 获取当前状态，传入 Pod
        action = self.act(state)  # 选择动作
        node_name = self._get_node_from_action(action)  # 根据动作获取节点名称

        try:
            # 尝试将 Pod 调度到选定的节点
            self.node_controller.schedule_pod_to_node(pod, node_name)
            next_state = self._get_state(pod)  # 获取下一个状态
            reward = self._calculate_reward(node_name, pod)  # 计算奖励
            done = False  # 结束标志
            self.remember(state, action, reward, next_state, done)  # 记住经历
            self.replay()  # 进行回放训练
        except Exception as e:
            logging.error(f"Failed to schedule Pod {pod.name} to Node {node_name}: {e}")  # 记录错误

    def _get_state(self, pod):
        # 获取当前系统状态，并加入 Pod 的资源需求
        states = []
        for node in self.node_controller.nodes.values():
            states.append([
                node.allocated_cpu,
                node.allocated_memory,
                node.allocated_gpu,
                node.total_cpu - node.allocated_cpu,
                node.total_memory - node.allocated_memory,
                node.total_gpu - node.allocated_gpu,
                pod.resources.get('requests', {}).get('cpu', 0),  # Pod 所需 CPU
                pod.resources.get('requests', {}).get('memory', 0),  # Pod 所需内存
                pod.resources.get('requests', {}).get('gpu', 0)   # Pod 所需 GPU
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
            if (node.total_cpu - node.allocated_cpu) < pod.required_cpu or \
               (node.total_memory - node.allocated_memory) < pod.required_memory or \
               (node.total_gpu - node.allocated_gpu) < pod.required_gpu:
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

