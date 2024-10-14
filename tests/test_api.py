import unittest
from sanic import Sanic
from sanic_testing import TestManager
from api.routes import configure_routes

class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 创建 Sanic 应用并配置路由
        cls.app = Sanic("TestAPI")
        TestManager(cls.app)
        configure_routes(cls.app)

    def test_create_container(self):
        # 测试创建容器的 API
        request, response = self.app.test_client.post('/api/containers', json={
            'image': 'busybox',
            'name': 'test-container'
        })
        self.assertEqual(response.status, 201)
        self.assertEqual(response.json['status'], 'created')

    def test_delete_container(self):
        # 测试删除容器的 API
        request, response = self.app.test_client.delete('/api/containers/test-container')
        self.assertEqual(response.status, 204)

    def test_pull_image(self):
        # 测试拉取镜像的 API
        request, response = self.app.test_client.post('/api/images', json={
            'image': 'busybox'
        })
        self.assertEqual(response.status, 201)
        self.assertEqual(response.json['status'], 'pulled')

    def test_list_images(self):
        # 测试列出所有镜像的 API
        request, response = self.app.test_client.get('/api/images')
        self.assertEqual(response.status, 200)
        self.assertIsInstance(response.json, list)

    def test_create_pod(self):
        # 测试创建 Pod 的 API
        request, response = self.app.test_client.post('/api/pods', json={
            'name': 'test-pod',
            'image': 'busybox'
        })
        self.assertEqual(response.status, 201)
        self.assertEqual(response.json['status'], 'created')

    def test_list_pods(self):
        # 测试列出所有 Pods 的 API
        request, response = self.app.test_client.get('/api/pods')
        self.assertEqual(response.status, 200)
        self.assertIsInstance(response.json, list)

    def test_add_node(self):
        # 测试添加节点的 API
        request, response = self.app.test_client.post('/api/nodes', json={
            'name': 'test-node',
            'total_cpu': 4,
            'total_memory': 8192
        })
        self.assertEqual(response.status, 201)
        self.assertEqual(response.json['status'], 'Node created')

    def test_list_nodes(self):
        # 测试列出所有节点的 API
        request, response = self.app.test_client.get('/api/nodes')
        self.assertEqual(response.status, 200)
        self.assertIsInstance(response.json, dict)

    def test_get_node(self):
        # 测试获取单个节点的 API
        request, response = self.app.test_client.get('/api/nodes/test-node')
        self.assertEqual(response.status, 200)

if __name__ == '__main__':
    unittest.main()
