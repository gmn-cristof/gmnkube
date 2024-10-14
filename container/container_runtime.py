import subprocess

class ContainerRuntime:
    def start_container(self, name: str):
        """Starts a container"""
        try:
            result = subprocess.run(
                ['ctr', 'task', 'start', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error starting container: {result.stderr}")
            print(f"Container {name} started successfully.")
        except Exception as e:
            print(f"Failed to start container {name}: {e}")

    def stop_container(self, name: str):
        """Stops a container"""
        try:
            result = subprocess.run(
                ['ctr', 'task', 'kill', name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error stopping container: {result.stderr}")
            print(f"Container {name} stopped successfully.")
        except Exception as e:
            print(f"Failed to stop container {name}: {e}")
