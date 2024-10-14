# tests/test_hello.py
import unittest
from sanic import Sanic
from sanic_testing import TestManager
from api.hello import app  # 导入你创建的 Sanic 应用

class TestHelloWorldAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 创建 Sanic 测试管理器
        cls.app = app
        TestManager(cls.app)

    def test_hello(self):
        # 测试 /hello 路由
        request, response = self.app.test_client.get('/hello')
        self.assertEqual(response.status, 200)
        self.assertEqual(response.json['message'], 'Hello, World!')

if __name__ == '__main__':
    unittest.main()
