import unittest
from sanic import Sanic
from sanic_testing import SanicTestManager
from sanic.response import json
from api.routes import configure_routes



class TestAPIServer(unittest.TestCase):
    def setUp(self):
        """初始化测试应用程序和路由"""
        self.app = Sanic("TestApp")
        configure_routes(self.app)
        self.manager = Manager(self.app)

    def test_create_container(self):
        """测试创建容器路由"""
        response = self.manager.post('/containers', json={'image': 'test_image', 'name': 'test_container'})
        self.assertEqual(response.status, 201)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Container created successfully.')

    def test_delete_container(self):
        """测试删除容器路由"""
        response = self.manager.delete('/containers/test_container')
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Container deleted successfully.')

    def test_list_containers(self):
        """测试列出所有容器路由"""
        response = self.manager.get('/containers')
        self.assertEqual(response.status, 200)
        self.assertIn('containers', response.json)
        self.assertIsInstance(response.json['containers'], list)

    def test_get_container_info(self):
        """测试获取容器信息路由"""
        response = self.manager.get('/containers/test_container')
        self.assertEqual(response.status, 200)
        self.assertIn('container_info', response.json)
        self.assertEqual(response.json['container_info']['name'], 'test_container')

    def test_start_container(self):
        """测试启动容器路由"""
        response = self.manager.post('/containers/test_container/start')
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Container started successfully.')

    def test_stop_container(self):
        """测试停止容器路由"""
        response = self.manager.post('/containers/test_container/stop')
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Container stopped successfully.')

    def test_pull_image(self):
        """测试拉取镜像路由"""
        response = self.manager.post('/images/pull', json={'image': 'test_image'})
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Image pulled successfully.')

    def test_list_images(self):
        """测试列出所有镜像路由"""
        response = self.manager.get('/images')
        self.assertEqual(response.status, 200)
        self.assertIn('images', response.json)
        self.assertIsInstance(response.json['images'], list)

    def test_remove_image(self):
        """测试移除镜像路由"""
        response = self.manager.delete('/images/remove', json={'image': 'test_image'})
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Image removed successfully.')

    def test_create_pod(self):
        """测试创建 Pod 路由"""
        response = self.manager.post('/pods', json={'name': 'test_pod', 'containers': ['test_container']})
        self.assertEqual(response.status, 201)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Pod created successfully.')

    def test_delete_pod(self):
        """测试删除 Pod 路由"""
        response = self.manager.delete('/pods/test_pod')
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Pod deleted successfully.')

    def test_get_pod(self):
        """测试获取 Pod 信息路由"""
        response = self.manager.get('/pods/test_pod')
        self.assertEqual(response.status, 200)
        self.assertIn('pod', response.json)
        self.assertEqual(response.json['pod']['name'], 'test_pod')

    def test_list_pods(self):
        """测试列出所有 Pod 路由"""
        response = self.manager.get('/pods')
        self.assertEqual(response.status, 200)
        self.assertIn('pods', response.json)
        self.assertIsInstance(response.json['pods'], list)

    def test_add_node(self):
        """测试添加节点路由"""
        response = self.manager.post('/nodes', json={
            'name': 'test_node',
            'ip_address': '192.168.0.1',
            'total_cpu': 4,
            'total_memory': 16,
            'total_gpu': 1
        })
        self.assertEqual(response.status, 201)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Node added successfully.')

    def test_remove_node(self):
        """测试移除节点路由"""
        response = self.manager.delete('/nodes/test_node')
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Node removed successfully.')

    def test_list_nodes(self):
        """测试列出所有节点路由"""
        response = self.manager.get('/nodes')
        self.assertEqual(response.status, 200)
        self.assertIn('nodes', response.json)
        self.assertIsInstance(response.json['nodes'], list)

    def test_get_node(self):
        """测试获取节点信息路由"""
        response = self.manager.get('/nodes/test_node')
        self.assertEqual(response.status, 200)
        self.assertIn('node', response.json)
        self.assertEqual(response.json['node']['name'], 'test_node')

    def test_schedule_pod(self):
        """测试在节点上调度 Pod 路由"""
        response = self.manager.post('/nodes/test_node/schedule', json={'pod': 'test_pod'})
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Pod scheduled successfully.')

    def test_ddqn_schedule(self):
        """测试 DDQN 调度路由"""
        response = self.manager.post('/DDQN/schedule', json={'pod': {'name': 'test_ddqn_pod'}})
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Pod scheduled with DDQN successfully.')

    def test_get_ddqn_scheduler_state(self):
        """测试获取 DDQN 调度器状态路由"""
        response = self.manager.get('/DDQN/scheduler/state')
        self.assertEqual(response.status, 200)
        self.assertIn('scheduler_state', response.json)

    def test_update_scheduler_config(self):
        """测试更新调度器配置路由"""
        response = self.manager.post('/DDQN/scheduler/update', json={'learning_rate': 0.001})
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Scheduler configuration updated successfully.')

    def test_get_memory_size(self):
        """测试获取内存大小路由"""
        response = self.manager.get('/DDQN/scheduler/memory')
        self.assertEqual(response.status, 200)
        self.assertIn('memory_size', response.json)

    def test_kube_schedule(self):
        """测试 Kubernetes 调度路由"""
        response = self.manager.post('/kube/schedule', json={'pod_name': 'test_kube_pod', 'required_resources': {'cpu': 2}})
        self.assertEqual(response.status, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], 'Pod scheduled with Kubernetes successfully.')

    def test_filter_nodes(self):
        """测试节点过滤路由"""
        response = self.manager.post('/kube/nodes/filter', json={'required_resources': {'cpu': 2}})
        self.assertEqual(response.status, 200)
        self.assertIn('available_nodes', response.json)
        self.assertIsInstance(response.json['available_nodes'], list)

if __name__ == '__main__':
    unittest.main()
