class Pod:
    def __init__(self, name: str, containers: list, namespace: str = 'default', volumes=None):
        self.name = name
        self.namespace = namespace
        self.containers = containers  # List of Container objects
        self.volumes = volumes or {}
        self.status = 'Pending'

    def start(self):
        """Start all containers in the Pod"""
        self.status = 'Running'
        for container in self.containers:
            container.start()
        print(f"Pod '{self.name}' in namespace '{self.namespace}' is now running with containers: {[c.name for c in self.containers]}.")

    def stop(self):
        """Stop all containers in the Pod"""
        self.status = 'Stopped'
        for container in self.containers:
            container.stop()
        print(f"Pod '{self.name}' in namespace '{self.namespace}' has been stopped.")

    def add_container(self, container: Container):
        """Add a new container to the Pod"""
        self.containers.append(container)
        print(f"Container '{container.name}' added to Pod '{self.name}' in namespace '{self.namespace}'.")

    def remove_container(self, container_name: str):
        """Remove a container from the Pod"""
        self.containers = [c for c in self.containers if c.name != container_name]
        print(f"Container '{container_name}' removed from Pod '{self.name}' in namespace '{self.namespace}'.")

    def get_status(self):
        """Get the current status of the Pod and its containers"""
        container_statuses = {c.name: c.status for c in self.containers}
        return {
            'pod_name': self.name,
            'namespace': self.namespace,
            'pod_status': self.status,
            'containers': container_statuses
        }

