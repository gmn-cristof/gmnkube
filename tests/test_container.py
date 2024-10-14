import unittest
from container.container_manager import ContainerManager

class TestContainerManager(unittest.TestCase):
    def setUp(self):
        self.manager = ContainerManager()

    def test_create_container(self):
        result = self.manager.create_container("nginx", "test_container")
        self.assertIsNotNone(result)

    def test_delete_container(self):
        result = self.manager.delete_container("test_container")
        self.assertIsNotNone(result)

if __name__ == "__main__":
    unittest.main()
