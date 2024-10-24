import unittest
from unittest.mock import patch, MagicMock
import subprocess
from container.container_manager import ContainerManager  # 假设 ContainerManager 在 container_manager.py 中定义

class TestContainerManager(unittest.TestCase):

    @patch('subprocess.run')
    def test_create_container_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        manager = ContainerManager()
        manager.create_container('docker.m.daocloud.io/library/alpine:latest', 'test-container')
        mock_run.assert_called_with(
            ['ctr', 'run', '--name', 'test-container', 'docker.m.daocloud.io/library/alpine:latest'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_create_container_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='Error creating container')
        manager = ContainerManager()
        with self.assertRaises(Exception) as context:
            manager.create_container('docker.m.daocloud.io/library/alpine:latest', 'test-container')
        self.assertIn('Error creating container', str(context.exception))
        mock_run.assert_called_with(
            ['ctr', 'run', '--name', 'test-container', 'docker.m.daocloud.io/library/alpine:latest'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_delete_container_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        manager = ContainerManager()
        manager.delete_container('test-container')
        mock_run.assert_called_with(
            ['ctr', 'containers', 'delete', 'test-container'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_delete_container_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='Error deleting container')
        manager = ContainerManager()
        with self.assertRaises(Exception) as context:
            manager.delete_container('test-container')
        self.assertIn('Error deleting container', str(context.exception))
        mock_run.assert_called_with(
            ['ctr', 'containers', 'delete', 'test-container'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_list_containers_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='container1\ncontainer2\n')
        manager = ContainerManager()
        manager.list_containers()
        mock_run.assert_called_with(
            ['ctr', 'containers', 'list'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_list_containers_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='Error listing containers')
        manager = ContainerManager()
        with self.assertRaises(Exception) as context:
            manager.list_containers()
        self.assertIn('Error listing containers', str(context.exception))
        mock_run.assert_called_with(
            ['ctr', 'containers', 'list'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_container_info_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='Container info...')
        manager = ContainerManager()
        manager.container_info('test-container')
        mock_run.assert_called_with(
            ['ctr', 'containers', 'info', 'test-container'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_container_info_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='Error getting container info')
        manager = ContainerManager()
        with self.assertRaises(Exception) as context:
            manager.container_info('test-container')
        self.assertIn('Error getting container info', str(context.exception))
        mock_run.assert_called_with(
            ['ctr', 'containers', 'info', 'test-container'],
            capture_output=True,
            text=True
        )

if __name__ == '__main__':
    unittest.main()
