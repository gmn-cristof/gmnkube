import subprocess
import logging
from typing import Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)

class ImageHandler:
    def pull_image(self, image: str) -> bool:
        try:
            result = subprocess.run(
                ['ctr', 'images', 'pull', image],
                capture_output=True,
                text=True,
                check=True
            )
            logging.info(f"Image '{image}' pulled successfully.")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to pull image '{image}': {e.stderr.strip()}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred while pulling image '{image}': {e}")
            return False

    def list_images(self) -> Optional[List[str]]:
        try:
            result = subprocess.run(
                ['ctr', 'images', 'list'],
                capture_output=True,
                text=True,
                check=True
            )
            images = result.stdout.splitlines()  # Split into a list of images
            logging.info("Images listed successfully.")
            return images
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to list images: {e.stderr.strip()}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while listing images: {e}")
        return None

    def remove_image(self, image: str) -> bool:
        try:
            result = subprocess.run(
                ['ctr', 'images', 'rm', image],
                capture_output=True,
                text=True,
                check=True
            )
            logging.info(f"Image '{image}' removed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to remove image '{image}': {e.stderr.strip()}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred while removing image '{image}': {e}")
            return False
