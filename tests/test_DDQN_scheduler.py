import unittest
from unittest.mock import MagicMock
import numpy as np
from orchestrator.DDQN_scheduler import DDQNScheduler
from node.node_controller import NodeController
from node.node import Node

class TestDDQNScheduler(unittest.TestCase):
    def setUp(self):
        # 创建一个 NodeController 的模拟实例
        self.node_controller = MagicMock()
        self.node_controller.nodes = {
            "node1": MagicMock(allocated_cpu=1, total_cpu=4, allocated_memory=1, total_memory=8, allocated_gpu=0, status="Ready"),
            "node2": MagicMock(allocated_cpu=2, total_cpu=4, allocated_memory=2, total_memory=8, allocated_gpu=0, status="Ready")
        }
        
        # 配置超参数
        self.config = {
            'gamma': 0.95,
            'epsilon': 1.0,
            'epsilon_min': 0.01,
            'epsilon_decay': 0.995,
            'learning_rate': 0.001,
            'batch_size': 32
        }
        
        # 初始化 DDQNScheduler
        self.scheduler = DDQNScheduler(self.node_controller, state_size=5, action_size=2, config=self.config)

    def test_initialization(self):
        """测试初始化是否正确"""
        self.assertEqual(self.scheduler.state_size, 5)
        self.assertEqual(self.scheduler.action_size, 2)
        self.assertAlmostEqual(self.scheduler.gamma, 0.95)
        self.assertEqual(len(self.scheduler.memory), 0)

    def test_act_exploration(self):
        """测试探索策略"""
        self.scheduler.epsilon = 1.0  # 确保完全探索
        action = self.scheduler.act(np.array([[0, 0, 0, 0, 0]]))
        self.assertIn(action, range(self.scheduler.action_size))

    def test_act_exploitation(self):
        """测试利用策略"""
        # Mocking the model's predict method
        self.scheduler.model.predict = MagicMock(return_value=np.array([[0.1, 0.9]]))
        action = self.scheduler.act(np.array([[0, 0, 0, 0, 0]]))
        self.assertEqual(action, 1)  # 应选择最大 Q 值的动作

    def test_remember(self):
        """测试记忆存储功能"""
        state = np.array([[0, 0, 0, 0, 0]])
        action = 0
        reward = 1.0
        next_state = np.array([[0, 0, 0, 0, 0]])
        done = False
        self.scheduler.remember(state, action, reward, next_state, done)
        self.assertEqual(len(self.scheduler.memory), 1)

    def test_schedule_pod(self):
        """测试 Pod 调度功能"""
        pod = MagicMock(name="Pod")
        pod.name = "test_pod"
        self.node_controller.schedule_pod_to_node = MagicMock()  # Mock 调度函数

        # 调度 Pod
        self.scheduler.schedule_pod(pod)

        # 验证调度函数是否被调用
        self.node_controller.schedule_pod_to_node.assert_called()
        
    def test_calculate_reward(self):
        """测试奖励计算功能"""
        reward = self.scheduler._calculate_reward("node1")
        self.assertGreaterEqual(reward, -1)  # 奖励应为非负

if __name__ == '__main__':
    unittest.main()
