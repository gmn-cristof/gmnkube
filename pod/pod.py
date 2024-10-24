import logging

class Pod:
    def __init__(self, name: str, containers: list, namespace: str = 'default', volumes=None):
        self.name = name
        self.namespace = namespace
        self.containers = containers  # List of Container objects
        self.volumes = volumes or {}
        self.status = 'Pending'

    def start(self):
        """Start all containers in the Pod"""
        if self.status != 'Pending' and self.status != 'Stopped':
            logging.error(f"Pod '{self.name}' is already running or terminated.")
            return
        
        all_started = True
        for container in self.containers:
            try:
                container.start()
                logging.info(f"Container '{container.name}' started successfully.")
            except Exception as e:
                logging.error(f"Failed to start container '{container.name}': {e}")
                all_started = False
        
        if all_started:
            self.status = 'Running'
            logging.info(f"Pod '{self.name}' in namespace '{self.namespace}' is now running.")
        else:
            logging.error(f"Pod '{self.name}' failed to start all containers.")

    def stop(self):
        """Stop all containers in the Pod"""
        if self.status != 'Running':
            logging.error(f"Pod '{self.name}' is not running.")
            return
        
        all_stopped = True
        for container in self.containers:
            try:
                container.stop()
                logging.info(f"Container '{container.name}' stopped successfully.")
            except Exception as e:
                logging.error(f"Failed to stop container '{container.name}': {e}")
                all_stopped = False

        if all_stopped:
            self.status = 'Stopped'
            logging.info(f"Pod '{self.name}' in namespace '{self.namespace}' has been stopped.")

    def add_container(self, container):
        """Add a new container to the Pod if it is not running."""
        if self.status == 'Running':
            logging.error(f"Cannot add container '{container.name}' to running Pod '{self.name}'.")
            return
        self.containers.append(container)
        logging.info(f"Container '{container.name}' added to Pod '{self.name}' in namespace '{self.namespace}'.")

    def remove_container(self, container_name: str):
        """Remove a container from the Pod if it is not running."""
        if self.status == 'Running':
            logging.error(f"Cannot remove container '{container_name}' from running Pod '{self.name}'.")
            return
        self.containers = [c for c in self.containers if c.name != container_name]
        logging.info(f"Container '{container_name}' removed from Pod '{self.name}' in namespace '{self.namespace}'.")

    def get_status(self):
        """Get the current status of the Pod and its containers."""
        container_statuses = {c.name: c.status for c in self.containers}
        return {
            'pod_name': self.name,
            'namespace': self.namespace,
            'pod_status': self.status,
            'containers': container_statuses
        }
