import unittest
from unittest.mock import MagicMock
from orchestrator.DDQN_scheduler import DDQNScheduler
import numpy as np

class TestDDQNScheduler(unittest.TestCase):
    def setUp(self):
        # 创建一个模拟的 NodeController
        self.node_controller = MagicMock()
        self.node_controller.nodes = {
            'node1': MagicMock(allocated_cpu=0, allocated_memory=0, allocated_gpu=0, total_cpu=4, total_memory=16, total_gpu=2, status='Ready'),
            'node2': MagicMock(allocated_cpu=0, allocated_memory=0, allocated_gpu=0, total_cpu=4, total_memory=16, total_gpu=2, status='Ready')
        }
        self.scheduler = DDQNScheduler(self.node_controller)

    def test_model_creation(self):
        self.assertIsNotNone(self.scheduler.model)
        self.assertIsNotNone(self.scheduler.target_model)

    def test_action_selection(self):
        state = np.array([[0, 0, 0, 2, 4, 16]])  # 假设的状态
        action = self.scheduler.act(state)
        self.assertIn(action, [0, 1])  # 确保选择的动作在可用动作范围内

    def test_memory_remember(self):
        initial_memory_size = len(self.scheduler.memory)
        state = np.array([[0, 0, 0, 2, 4, 16]])
        self.scheduler.remember(state, 0, 1, state, False)
        self.assertEqual(len(self.scheduler.memory), initial_memory_size + 1)

    def test_schedule_pod(self):
        pod = MagicMock(name='pod')
        pod.name = 'test_pod'
        
        # 调度 Pod 到节点并确保没有抛出异常
        try:
            self.scheduler.schedule_pod(pod)
        except Exception as e:
            self.fail(f"schedule_pod raised Exception: {str(e)}")

        # 确保调度方法被调用
        self.node_controller.schedule_pod_to_node.assert_called()

if __name__ == '__main__':
    unittest.main()
