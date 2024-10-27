import unittest
from unittest.mock import patch, MagicMock
from pod.pod import Pod  # 确保你正确导入 Pod 类
from container.container import Container
import logging
class TestPod(unittest.TestCase):

    def setUp(self):
        self.container1 = MagicMock(name='Container1')
        self.container1.name = 'container1'
        self.container1.status = 'Pending'
        
        self.container2 = MagicMock(name='Container2')
        self.container2.name = 'container2'
        self.container2.status = 'Pending'

        self.pod = Pod(name='test-pod', containers=[self.container1, self.container2])

    def test_start_success(self):
        self.pod.start()
        self.assertEqual(self.pod.status, 'Running')
        self.container1.start.assert_called_once()
        self.container2.start.assert_called_once()

    def test_start_already_running(self):
        self.pod.status = 'Running'
        self.pod.start()
        # 这里可以验证某个状态或调用，而不是依赖于 logging

    def test_stop_success(self):
        self.pod.status = 'Running'
        self.pod.stop()
        self.assertEqual(self.pod.status, 'Stopped')
        self.container1.stop.assert_called_once()
        self.container2.stop.assert_called_once()

    def test_stop_not_running(self):
        self.pod.status = 'Stopped'
        self.pod.stop()
        # 验证状态或调用

    def test_add_container(self):
        new_container = MagicMock(name='Container3')
        new_container.name = 'container3'
        self.pod.add_container(new_container)
        self.assertIn(new_container, self.pod.containers)

    def test_add_container_to_running_pod(self):
        self.pod.status = 'Running'
        new_container = MagicMock(name='Container3')
        new_container.name = 'container3'
        self.pod.add_container(new_container)
        # 验证状态或调用

    def test_remove_container(self):
        self.pod.remove_container('container1')
        self.assertNotIn(self.container1, self.pod.containers)

    def test_remove_container_from_running_pod(self):
        self.pod.status = 'Running'
        self.pod.remove_container('container1')
        # 验证状态或调用

    def test_get_status(self):
        self.pod.status = 'Running'
        expected_status = {
            'pod_name': 'test-pod',
            'namespace': 'default',
            'pod_status': 'Running',
            'containers': {
                'container1': self.container1.status,
                'container2': self.container2.status,
            }
        }
        self.assertEqual(self.pod.get_status(), expected_status)

if __name__ == '__main__':
    unittest.main()