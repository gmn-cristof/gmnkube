import subprocess

class ContainerRuntime:
    def start_container(self, name: str):
        """Starts a container."""
        try:
            result = subprocess.run(
                ['ctr', 'task', 'start', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error starting container: {result.stderr.strip()}")
            print(f"Container {name} started successfully.")
        except Exception as e:
            print(f"Failed to start container {name}: {e}")

    def stop_container(self, name: str):
        """Stops a container."""
        try:
            result = subprocess.run(
                ['ctr', 'task', 'kill', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error stopping container: {result.stderr.strip()}")
            print(f"Container {name} stopped successfully.")
        except Exception as e:
            print(f"Failed to stop container {name}: {e}")

    def list_containers(self):
        """Lists all containers."""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'ls'], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error listing containers: {result.stderr.strip()}")
            print("Containers:\n" + result.stdout)
        except Exception as e:
            print(f"Failed to list containers: {e}")

    def remove_container(self, name: str):
        """Removes a container."""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'rm', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error removing container: {result.stderr.strip()}")
            print(f"Container {name} removed successfully.")
        except Exception as e:
            print(f"Failed to remove container {name}: {e}")

    def inspect_container(self, name: str):
        """Inspects a container."""
        try:
            result = subprocess.run(
                ['ctr', 'containers', 'info', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error inspecting container: {result.stderr.strip()}")
            print(f"Container {name} info:\n" + result.stdout)
        except Exception as e:
            print(f"Failed to inspect container {name}: {e}")
