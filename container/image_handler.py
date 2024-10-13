import subprocess

class ImageHandler:
    def pull_image(self, image: str):
        """Pulls an image from the container registry"""
        try:
            result = subprocess.run(
                ['ctr', 'images', 'pull', image], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error pulling image: {result.stderr}")
            print(f"Image {image} pulled successfully.")
        except Exception as e:
            print(f"Failed to pull image {image}: {e}")

    def list_images(self):
        """Lists all available images"""
        try:
            result = subprocess.run(
                ['ctr', 'images', 'list'], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Error listing images: {result.stderr}")
            print(result.stdout)
        except Exception as e:
            print(f"Failed to list images: {e}")
