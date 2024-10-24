import unittest
from unittest.mock import patch, MagicMock
from container.image_handler import ImageHandler  # 假设ImageHandler定义在image_handler.py中
import subprocess

class TestImageHandler(unittest.TestCase):

    @patch('subprocess.run')
    def test_pull_image_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)  # 模拟成功返回
        handler = ImageHandler()
        result = handler.pull_image('docker.m.daocloud.io/library/alpine:latest')
        mock_run.assert_called_with(
            ['ctr', 'images', 'pull', 'docker.m.daocloud.io/library/alpine:latest'],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_pull_image_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd', stderr='Error pulling image')
        handler = ImageHandler()
        result = handler.pull_image('docker.m.daocloud.io/library/alpine:latest')
        mock_run.assert_called_with(
            ['ctr', 'images', 'pull', 'docker.m.daocloud.io/library/alpine:latest'],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_list_images_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='docker.m.daocloud.io/library/alpine:latest\nubuntu:latest\n')
        handler = ImageHandler()
        result = handler.list_images()
        mock_run.assert_called_with(
            ['ctr', 'images', 'list'],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(result, ['docker.m.daocloud.io/library/alpine:latest', 'ubuntu:latest'])

    @patch('subprocess.run')
    def test_list_images_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd', stderr='Error listing images')
        handler = ImageHandler()
        result = handler.list_images()
        mock_run.assert_called_with(
            ['ctr', 'images', 'list'],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertIsNone(result)

    @patch('subprocess.run')
    def test_remove_image_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)  # 模拟成功返回
        handler = ImageHandler()
        result = handler.remove_image('docker.m.daocloud.io/library/alpine:latest')
        mock_run.assert_called_with(
            ['ctr', 'images', 'rm', 'docker.m.daocloud.io/library/alpine:latest'],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_remove_image_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd', stderr='Error removing image')
        handler = ImageHandler()
        result = handler.remove_image('docker.m.daocloud.io/library/alpine:latest')
        mock_run.assert_called_with(
            ['ctr', 'images', 'rm', 'docker.m.daocloud.io/library/alpine:latest'],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
