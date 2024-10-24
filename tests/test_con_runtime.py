import unittest
from unittest.mock import patch, MagicMock
import subprocess
from container.container_runtime import ContainerRuntime  
from container.container_manager import ContainerManager

class TestContainerRuntime(unittest.TestCase):

    @patch('subprocess.run')
    def test_start_container_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        runtime = ContainerRuntime()
        runtime.start_container('test-container')
        mock_run.assert_called_with(
            ['ctr', 'task', 'start', 'test-container'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_start_container_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='Error starting container')
        runtime = ContainerRuntime()
        runtime.start_container('test-container')
        mock_run.assert_called_with(
            ['ctr', 'task', 'start', 'test-container'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_stop_container_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        runtime = ContainerRuntime()
        runtime.stop_container('test-container')
        mock_run.assert_called_with(
            ['ctr', 'task', 'kill', 'test-container'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_stop_container_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='Error stopping container')
        runtime = ContainerRuntime()
        runtime.stop_container('test-container')
        mock_run.assert_called_with(
            ['ctr', 'task', 'kill', 'test-container'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_list_containers_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='container1\ncontainer2\n')
        runtime = ContainerRuntime()
        runtime.list_containers()
        mock_run.assert_called_with(
            ['ctr', 'containers', 'ls'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_list_containers_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='Error listing containers')
        runtime = ContainerRuntime()
        runtime.list_containers()
        mock_run.assert_called_with(
            ['ctr', 'containers', 'ls'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_remove_container_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        runtime = ContainerRuntime()
        runtime.remove_container('test-container')
        mock_run.assert_called_with(
            ['ctr', 'containers', 'rm', 'test-container'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_remove_container_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='Error removing container')
        runtime = ContainerRuntime()
        runtime.remove_container('test-container')
        mock_run.assert_called_with(
            ['ctr', 'containers', 'rm', 'test-container'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_inspect_container_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='Container info...')
        runtime = ContainerRuntime()
        runtime.inspect_container('test-container')
        mock_run.assert_called_with(
            ['ctr', 'containers', 'info', 'test-container'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_inspect_container_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='Error inspecting container')
        runtime = ContainerRuntime()
        runtime.inspect_container('test-container')
        mock_run.assert_called_with(
            ['ctr', 'containers', 'info', 'test-container'],
            capture_output=True,
            text=True
        )

if __name__ == '__main__':
    # manager = ContainerManager()
    # manager.create_container('docker.m.daocloud.io/library/alpine:latest', 'test-container')
    unittest.main()
