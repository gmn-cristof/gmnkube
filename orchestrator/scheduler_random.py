import random
import yaml

class Scheduler:
    def __init__(self):
        with open('config/config.yaml', 'r') as config_file:
            config = yaml.safe_load(config_file)
            self.nodes = config['scheduler']['nodes']

    def schedule_container(self, container_name: str):
        """Selects a node to schedule the container"""
        if not self.nodes:
            raise Exception("No available nodes for scheduling.")
        selected_node = random.choice(self.nodes)
        print(f"Scheduled container {container_name} on node {selected_node}.")
        return selected_node
