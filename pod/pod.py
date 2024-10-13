class Pod:
    def __init__(self, name: str, image: str):
        self.name = name
        self.image = image
        self.status = 'Pending'

    def start(self):
        """Start the Pod"""
        self.status = 'Running'
        print(f"Pod '{self.name}' is now running.")

    def stop(self):
        """Stop the Pod"""
        self.status = 'Stopped'
        print(f"Pod '{self.name}' has been stopped.")
