import unittest
from pod.pod_controller import PodController

class TestPodController(unittest.TestCase):
    def setUp(self):
        self.controller = PodController()

    def test_create_pod(self):
        self.controller.create_pod("test-pod", "nginx")
        self.assertIn("test-pod", self.controller.list_pods())

    def test_delete_pod(self):
        self.controller.create_pod("test-pod", "nginx")
        self.controller.delete_pod("test-pod")
        self.assertNotIn("test-pod", self.controller.list_pods())

    def test_get_pod(self):
        self.controller.create_pod("test-pod", "nginx")
        pod = self.controller.get_pod("test-pod")
        self.assertIsNotNone(pod)
        self.assertEqual(pod.name, "test-pod")

if __name__ == "__main__":
    unittest.main()
