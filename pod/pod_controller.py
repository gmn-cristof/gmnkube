import logging
from pod.pod import Pod
from container.container import Container

class PodController:
    def __init__(self):
        self.pods = {}

    def create_pod(self, name: str, containers: list):
        """Creates a new Pod with a list of containers"""
        if name in self.pods:
            logging.error(f"Pod '{name}' already exists.")
            raise ValueError(f"Pod '{name}' already exists.")

        pod = Pod(name=name, containers=containers)
        try:
            pod.start()
            self.pods[name] = pod
            logging.info(f"Pod '{name}' created successfully with containers: {[c.name for c in containers]}.")
        except Exception as e:
            logging.error(f"Failed to create Pod '{name}': {e}")
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
