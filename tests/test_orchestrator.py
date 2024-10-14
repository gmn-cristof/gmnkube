import unittest
from orchestrator.scheduler import Scheduler

class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = Scheduler()

    def test_schedule(self):
        node = self.scheduler.schedule_container("test_container")
        self.assertIn(node, ["node1", "node2", "node3"])

if __name__ == "__main__":
    unittest.main()
