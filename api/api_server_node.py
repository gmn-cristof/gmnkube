from sanic import Sanic, response, SanicException
from sanic.request import Request
from container.container import Container
from etcd.etcd_client import EtcdClient
from container.container_manager import ContainerManager
from container.container_runtime import ContainerRuntime
from pod.pod_controller import PodController
from container.image_handler import ImageHandler
from node.node_controller import NodeController
from orchestrator.DDQN_scheduler import DDQNScheduler
from orchestrator.kube_scheduler_plus import Kube_Scheduler_Plus
from sanic_cors import CORS
import logging,json

app = Sanic(__name__)
app.config.DEBUG = True
CORS(app)

etcd_client = EtcdClient()
container_manager = ContainerManager(etcd_client)
container_runtime = ContainerRuntime(etcd_client)
image_handler = ImageHandler()
pod_controller = PodController(etcd_client, container_manager, container_runtime)




def configure_routes(app):
    @app.route('/pods', methods=['POST'])
    async def create_pod(request: Request):
        # print(type(request))
        # print(request)
        try:
            data = request.json
            # print(type(request))
            # print(request)

  
            metadata = data.get("metadata")
            spec = data.get("spec")
            
            if not metadata or not spec:
                return response.json({'error': "Invalid pod specification."}, status=400)

            name = metadata.get("name")
            namespace = metadata.get("namespace", "default")

            if not name:
                return response.json({'error': "Pod name is required."}, status=400)

            # Create a list to hold Container objects
            containers = []

            # Iterate through each container definition in the JSON
            for container_data in spec.get("containers", []):
                container_name = container_data.get("name")
                container_image = container_data.get("image")
                container_command = container_data.get("command", [])  # Default to empty list
                container_ports = container_data.get("ports", [])
                container_resources = container_data.get("resources", {
                                'requests': {
                                    },
                                'limits': { 
                                }
                })

                if not container_name or not container_image:
                    return response.json({'error': "Container name and image are required."}, status=400)

                # Extract port numbers for the Container class
                ports = [port['containerPort'] for port in container_ports if 'containerPort' in port]

                # Create a Container object
                container = Container(
                    name=container_name,
                    image=container_image,
                    command=container_command,
                    resources=container_resources,
                    ports=ports,
                    etcd_client=etcd_client
                )
                containers.append(container)

            if not containers:
                return response.json({'error': "At least one container must be specified."}, status=400)

            # Call the pod controller to create the pod
            pod_controller.create_pod(name, containers, namespace)

            return response.json({'message': f"Pod '{name}' created successfully."}, status=201)

        except Exception as e:
            logging.error("An error occurred", exc_info=True)
            return response.json({'error': str(e)}, status=500)
        
    @app.route('/pods/<name>', methods=['DELETE'])
    async def delete_pod(request: Request, name: str):
        try:
            pod_controller.delete_pod(name)
            return response.json({'message': f"Pod '{name}' deleted successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)
        
    @app.route('/pods/<name>/stop', methods=['POST'])
    async def stop_pod(request: Request, name: str):
        try:
            pod_controller.stop_pod(name)
            return response.json({'message': f"Pod '{name}' stopped successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)
        
    @app.route('/pods/<name>/start', methods=['POST'])
    async def start_pod(request: Request, name: str):
        try:
            pod_controller.start_pod(name)
            return response.json({'message': f"Pod '{name}' started successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/pods/<name>/restart', methods=['POST'])
    async def restart_pod(request: Request, name: str):
        try:
            pod_controller.restart_pod(name)
            return response.json({'message': f"Pod '{name}' restarted successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)