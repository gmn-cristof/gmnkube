import unittest
from unittest.mock import MagicMock
import logging
from node.node import Node  # 确保你的 Node 类在 node.py 文件中

class TestNode(unittest.TestCase):

    def setUp(self):
        self.node = Node(name="test-node", total_cpu=8, total_memory=16000, total_gpu=2)

        # 创建一个模拟 Pod 对象
        self.pod = MagicMock()
        self.pod.name = "test-pod"
        self.pod.resources = {
            "cpu": 2,
            "memory": 2048,
            "gpu": 1,
            "io": 0,
            "net": 0
        }

    def test_add_pod_success(self):
        self.node.add_pod(self.pod)
        self.assertIn(self.pod, self.node.pods)
        self.assertEqual(self.node.allocated_cpu, 2)
        self.assertEqual(self.node.allocated_memory, 2048)
        logging.info("Test passed: Pod added successfully.")

    def test_add_pod_insufficient_resources(self):
        self.node.allocated_cpu = 8  # 模拟已分配资源已满
        with self.assertRaises(Exception) as context:
            self.node.add_pod(self.pod)
        self.assertTrue("Not enough resources" in str(context.exception))
        logging.info("Test passed: Insufficient resources correctly raised an exception.")

    def test_remove_pod_success(self):
        self.node.add_pod(self.pod)
        self.node.remove_pod(self.pod)
        self.assertNotIn(self.pod, self.node.pods)
        self.assertEqual(self.node.allocated_cpu, 0)
        self.assertEqual(self.node.allocated_memory, 0)
        logging.info("Test passed: Pod removed successfully.")

    def test_remove_nonexistent_pod(self):
        with self.assertLogs(logging.getLogger(), level='WARNING') as log:
            self.node.remove_pod(self.pod)
            self.assertIn("WARNING:root:Attempted to remove non-existent Pod test-pod from Node test-node.", log.output)
        logging.info("Test passed: Nonexistent pod removal logged a warning.")

    def test_can_schedule_success(self):
        can_schedule = self.node.can_schedule(2, 2048, 1, 0, 0)
        self.assertTrue(can_schedule)
        logging.info("Test passed: Can schedule returns True with sufficient resources.")

    def test_can_schedule_insufficient_resources(self):
        self.node.allocated_cpu = 8  # 模拟已分配资源已满
        can_schedule = self.node.can_schedule(2, 2048, 1, 0, 0)
        self.assertFalse(can_schedule)
        logging.info("Test passed: Can schedule returns False with insufficient resources.")

    def test_set_status(self):
        self.node.set_status("NotReady")
        self.assertEqual(self.node.status, "NotReady")
        logging.info("Test passed: Node status updated successfully.")

    def test_to_dict(self):
        self.node.add_pod(self.pod)
        node_dict = self.node.to_dict()
        self.assertEqual(node_dict['name'], "test-node")
        self.assertEqual(node_dict['allocated_cpu'], 2)
        self.assertIn("test-pod", node_dict['pods'])
        logging.info("Test passed: Node information converted to dictionary successfully.")

if __name__ == '__main__':
    unittest.main()
