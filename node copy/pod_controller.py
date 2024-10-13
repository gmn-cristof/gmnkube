from .pod import Pod

class PodController:
    def __init__(self):
        self.pods = {}

    def create_pod(self, name: str, image: str):
        """Creates a new Pod"""
        if name in self.pods:
            raise ValueError(f"Pod '{name}' already exists.")
        pod = Pod(name, image)
        pod.start()
        self.pods[name] = pod
        print(f"Pod '{name}' created with image '{image}'.")

    def delete_pod(self, name: str):
        """Deletes a Pod"""
        if name not in self.pods:
            raise ValueError(f"Pod '{name}' not found.")
        pod = self.pods.pop(name)
        pod.stop()
        print(f"Pod '{name}' deleted.")

    def get_pod(self, name: str):
        """Get Pod details"""
        return self.pods.get(name, None)

    def list_pods(self):
        """List all Pods"""
        return list(self.pods.keys())
