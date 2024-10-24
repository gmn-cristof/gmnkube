import subprocess

class ContainerManager:
    def create_container(self, image: str, name: str):
        """Creates a container using containerd"""
        try:
            result = subprocess.run(
                ['ctr', 'run', '--name', name, image], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error creating container: {result.stderr}")
            print(f"Container {name} created successfully.")
        except Exception as e:
            print(f"Failed to create container {name}: {e}")

    def delete_container(self, name: str):
        """Deletes a container using containerd"""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'delete', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error deleting container: {result.stderr}")
            print(f"Container {name} deleted successfully.")
        except Exception as e:
            print(f"Failed to delete container {name}: {e}")
    
    def list_containers(self):
        """Lists all containers using containerd"""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'list'], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error listing containers: {result.stderr}")
            print("Containers:\n", result.stdout)
        except Exception as e:
            print(f"Failed to list containers: {e}")

    def container_info(self, name: str):
        """Retrieves information about a specific container"""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'info', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error getting container info: {result.stderr}")
            print(f"Container info for {name}:\n", result.stdout)
        except Exception as e:
            print(f"Failed to get info for container {name}: {e}")

