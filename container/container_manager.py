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
