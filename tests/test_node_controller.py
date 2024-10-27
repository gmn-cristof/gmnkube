import unittest
from unittest.mock import MagicMock
from node.node_controller import NodeController
from node.node import Node
import logging

class TestNodeController(unittest.TestCase):
    def setUp(self):
        """在每个测试之前运行，初始化 NodeController 对象."""
        self.controller = NodeController()

    def test_add_node(self):
        """测试添加节点功能."""
        self.controller.add_node("node1", 4, 8192)
        self.assertIn("node1", self.controller.nodes)
        self.assertEqual(self.controller.nodes["node1"].total_cpu, 4)
        self.assertEqual(self.controller.nodes["node1"].total_memory, 8192)

    def test_add_existing_node(self):
        """测试添加已存在的节点."""
        self.controller.add_node("node1", 4, 8192)
        with self.assertRaises(Exception) as context:
            self.controller.add_node("node1", 4, 8192)
        self.assertEqual(str(context.exception), "Node node1 already exists.")

    def test_remove_node(self):
        """测试移除节点功能."""
        self.controller.add_node("node1", 4, 8192)
        self.controller.remove_node("node1")
        self.assertNotIn("node1", self.controller.nodes)

    def test_remove_non_existent_node(self):
        """测试移除不存在的节点."""
        with self.assertRaises(Exception) as context:
            self.controller.remove_node("node1")
        self.assertEqual(str(context.exception), "Node node1 does not exist.")

    def test_schedule_pod_to_node(self):
        """测试将 Pod 调度到节点功能."""
        pod_mock = MagicMock()
        pod_mock.name = "pod1"
        pod_mock.resources = {"cpu": 1, "memory": 1024}
        
        self.controller.add_node("node1", 4, 8192)
        self.controller.schedule_pod_to_node(pod_mock, "node1")
        self.assertIn(pod_mock, self.controller.nodes["node1"].pods)

    def test_schedule_pod_to_non_existent_node(self):
        """测试将 Pod 调度到不存在的节点."""
        pod_mock = MagicMock()
        pod_mock.name = "pod1"
        pod_mock.resources = {"cpu": 1, "memory": 1024}
        
        with self.assertRaises(Exception) as context:
            self.controller.schedule_pod_to_node(pod_mock, "non_existent_node")
        self.assertEqual(str(context.exception), "Node non_existent_node does not exist.")

    def test_update_node_status(self):
        """测试更新节点状态功能."""
        self.controller.add_node("node1", 4, 8192)
        self.controller.update_node_status("node1", "NotReady")
        self.assertEqual(self.controller.nodes["node1"].status, "NotReady")

    def test_update_non_existent_node_status(self):
        """测试更新不存在的节点状态."""
        with self.assertRaises(Exception) as context:
            self.controller.update_node_status("non_existent_node", "NotReady")
        self.assertEqual(str(context.exception), "Node non_existent_node does not exist.")

if __name__ == "__main__":
    unittest.main()
