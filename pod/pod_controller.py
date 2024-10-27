import logging
import yaml
from .pod import Pod
from container.container import Container

class PodController:
    def __init__(self):
        self.pods = {}

    def create_pod(self, name: str, containers: list, namespace: str = 'default'):
        """Creates a new Pod with a list of containers"""
        if name in self.pods:
            logging.error(f"Pod '{name}' already exists.")
            raise ValueError(f"Pod '{name}' already exists.")

        pod = Pod(name=name, containers=containers, namespace=namespace)
        try:
            pod.start()
            self.pods[name] = pod
            logging.info(f"Pod '{name}' created successfully with containers: {[c.name for c in containers]}.")
        except Exception as e:
            logging.error(f"Failed to create Pod '{name}': {e}")
            raise

    def create_pod_from_yaml(self, yaml_file: str):
        """Creates a Pod from a YAML file"""
        try:
            with open(yaml_file, 'r') as file:
                pod_config = yaml.safe_load(file)
            
            # 确保 YAML 文件结构符合预期
            if pod_config['kind'] != 'Pod':
                raise ValueError("Invalid YAML file: kind must be 'Pod'")

            name = pod_config['metadata']['name']
            namespace = pod_config['metadata'].get('namespace', 'default')
            containers = [
                Container(
                    name=c['name'],
                    image=c['image'],
                    resources=c.get('resources', {}),
                    ports=c.get('ports', [])
                ) for c in pod_config['spec']['containers']
            ]

            self.create_pod(name, containers, namespace)
        
        except Exception as e:
            logging.error(f"Failed to create Pod from YAML '{yaml_file}': {e}")
            raise

    def delete_pod(self, name: str):
        """Deletes a Pod after stopping it"""
        if name not in self.pods:
            logging.error(f"Pod '{name}' not found.")
            raise ValueError(f"Pod '{name}' not found.")

        pod = self.pods[name]
        try:
            pod.stop()
            del self.pods[name]
            logging.info(f"Pod '{name}' deleted successfully.")
        except Exception as e:
            logging.error(f"Failed to delete Pod '{name}': {e}")
            raise

    def get_pod(self, name: str):
        """Get Pod details"""
        pod = self.pods.get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found.")
        return pod

    def list_pods(self):
        """List all Pod names"""
        pod_list = list(self.pods.keys())
        logging.info(f"Listing all pods: {pod_list}")
        return pod_list

    def stop_pod(self, name: str):
        """Stops a Pod"""
        pod = self.pods.get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found.")
            raise ValueError(f"Pod '{name}' not found.")
        
        try:
            pod.stop()
            logging.info(f"Pod '{name}' stopped successfully.")
        except Exception as e:
            logging.error(f"Failed to stop Pod '{name}': {e}")
            raise

    def restart_pod(self, name: str):
        """Restarts a Pod"""
        pod = self.pods.get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found.")
            raise ValueError(f"Pod '{name}' not found.")
        
        try:
            pod.stop()
            pod.start()
            logging.info(f"Pod '{name}' restarted successfully.")
        except Exception as e:
            logging.error(f"Failed to restart Pod '{name}': {e}")
            raise
