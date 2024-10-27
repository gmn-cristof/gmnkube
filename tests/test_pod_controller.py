import unittest
from unittest.mock import patch, MagicMock
from pod.pod_controller import PodController
from container.container import Container
import logging

class TestPodController(unittest.TestCase):

    def setUp(self):
        self.controller = PodController()
        self.container = MagicMock(name='Container1', spec=Container)
        self.container.name = 'container1'
        self.container.image = 'docker.m.daocloud.io/library/alpine:latest'

    @patch('logging.info')
    @patch('pod.pod.Pod.start')
    def test_create_pod_success(self, mock_start, mock_logging):
        mock_start.return_value = None
        self.controller.create_pod('test-pod', [self.container])
        self.assertIn('test-pod', self.controller.pods)
        mock_logging.assert_called_with("Pod 'test-pod' created successfully with containers: ['container1'].")

    @patch('logging.error')
    def test_create_existing_pod(self, mock_logging):
        self.controller.create_pod('test-pod', [self.container])
        with self.assertRaises(ValueError):
            self.controller.create_pod('test-pod', [self.container])
        mock_logging.assert_called_with("Pod 'test-pod' already exists.")

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='''\
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
    - name: container1
      image: docker.m.daocloud.io/library/alpine:latest
''')
    @patch('pod.pod.Pod.start')
    def test_create_pod_from_yaml_success(self, mock_start, mock_open):
        mock_start.return_value = None
        self.controller.create_pod_from_yaml('pod.yaml')
        self.assertIn('test-pod', self.controller.pods)

    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('logging.error')
    def test_create_pod_from_yaml_file_not_found(self, mock_logging, mock_open):
        with self.assertRaises(FileNotFoundError):
            self.controller.create_pod_from_yaml('nonexistent.yaml')
        mock_logging.assert_called()

    @patch('logging.error')
    def test_delete_pod_success(self, mock_logging):
        self.controller.create_pod('test-pod', [self.container])
        self.controller.delete_pod('test-pod')
        self.assertNotIn('test-pod', self.controller.pods)

    @patch('logging.error')
    def test_delete_nonexistent_pod(self, mock_logging):
        with self.assertRaises(ValueError):
            self.controller.delete_pod('nonexistent-pod')
        mock_logging.assert_called_with("Pod 'nonexistent-pod' not found.")

    @patch('logging.error')
    def test_get_pod(self, mock_logging):
        self.controller.create_pod('test-pod', [self.container])
        pod = self.controller.get_pod('test-pod')
        self.assertIsNotNone(pod)

    @patch('logging.error')
    def test_get_nonexistent_pod(self, mock_logging):
        pod = self.controller.get_pod('nonexistent-pod')
        self.assertIsNone(pod)
        mock_logging.assert_called_with("Pod 'nonexistent-pod' not found.")

    @patch('logging.info')
    def test_list_pods(self, mock_logging):
        self.controller.create_pod('test-pod1', [self.container])
        self.controller.create_pod('test-pod2', [self.container])
        pods = self.controller.list_pods()
        self.assertEqual(pods, ['test-pod1', 'test-pod2'])

    @patch('pod.pod.Pod.stop')
    @patch('logging.info')
    def test_stop_pod_success(self, mock_logging, mock_stop):
        mock_stop.return_value = None
        self.controller.create_pod('test-pod', [self.container])
        self.controller.stop_pod('test-pod')
        mock_logging.assert_called_with("Pod 'test-pod' stopped successfully.")

    @patch('logging.error')
    def test_stop_nonexistent_pod(self, mock_logging):
        with self.assertRaises(ValueError):
            self.controller.stop_pod('nonexistent-pod')
        mock_logging.assert_called_with("Pod 'nonexistent-pod' not found.")

    @patch('pod.pod.Pod.stop')
    @patch('pod.pod.Pod.start')
    @patch('logging.info')
    def test_restart_pod_success(self, mock_logging, mock_start, mock_stop):
        mock_start.return_value = None
        mock_stop.return_value = None
        self.controller.create_pod('test-pod', [self.container])
        self.controller.restart_pod('test-pod')
        mock_logging.assert_called_with("Pod 'test-pod' restarted successfully.")

    @patch('logging.error')
    def test_restart_nonexistent_pod(self, mock_logging):
        with self.assertRaises(ValueError):
            self.controller.restart_pod('nonexistent-pod')
        mock_logging.assert_called_with("Pod 'nonexistent-pod' not found.")

if __name__ == '__main__':
    unittest.main()
