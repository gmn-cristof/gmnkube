import unittest
from unittest.mock import MagicMock
from orchestrator.kube_scheduler_plus import Kube_Scheduler_Plus

class TestKubeSchedulerPlus(unittest.TestCase):

    def setUp(self):
        """测试前的设置，初始化 Kube_Scheduler_Plus 实例。"""
        self.scheduler = Kube_Scheduler_Plus()
        self.scheduler.node_controller = MagicMock()

    def test_filter_nodes_no_ready_nodes(self):
        """测试没有 'Ready' 状态节点的情况。"""
        self.scheduler.node_controller.list_nodes.return_value = {
            'node1': {'status': 'NotReady', 'total_resources': {}},
            'node2': {'status': 'NotReady', 'total_resources': {}},
        }
        available_nodes = self.scheduler.filter_nodes({})
        self.assertEqual(available_nodes, [])

    def test_filter_nodes_insufficient_resources(self):
        """测试节点资源不足的情况。"""
        self.scheduler.node_controller.list_nodes.return_value = {
            'node1': {'status': 'Ready', 'total_resources': {'cpu': 1}, 'used_resources': {}},
        }
        required_resources = {'cpu': 2}
        available_nodes = self.scheduler.filter_nodes(required_resources)
        self.assertEqual(available_nodes, [])

    def test_filter_nodes_sufficient_resources(self):
        """测试节点资源充足的情况。"""
        self.scheduler.node_controller.list_nodes.return_value = {
            'node1': {'status': 'Ready', 'total_resources': {'cpu': 2}, 'used_resources': {}},
        }
        required_resources = {'cpu': 1}
        available_nodes = self.scheduler.filter_nodes(required_resources)
        self.assertEqual(len(available_nodes), 1)

    def test_calculate_score(self):
        """测试节点评分计算。"""
        node = {
            'total_resources': {'cpu': 4, 'gpu': 2, 'memory': 8, 'io': 10, 'network': 100},
            'used_resources': {'cpu': 2, 'gpu': 1, 'memory': 4, 'io': 2, 'network': 10},
        }
        score = self.scheduler.calculate_score(node)
        self.assertIsInstance(score, float)

    def test_schedule_pod_no_available_nodes(self):
        """测试没有可用节点的情况。"""
        self.scheduler.node_controller.list_nodes.return_value = {}
        with self.assertRaises(Exception):
            self.scheduler.schedule_pod('test-pod', {'cpu': 1})

def test_schedule_pod_success(self):
    """测试成功调度 Pod 的情况。"""
    self.scheduler.node_controller.list_nodes.return_value = {
        'node1': {
            'name': 'node1',
            'status': 'Ready',
            'total_resources': {'cpu': 2},
            'used_resources': {}
        },
    }
    self.scheduler.node_controller.schedule_pod_to_node = MagicMock()
    self.scheduler.schedule_pod('test-pod', {'cpu': 1})
    self.scheduler.node_controller.schedule_pod_to_node.assert_called_once_with('test-pod', 'node1')


if __name__ == '__main__':
    unittest.main()
