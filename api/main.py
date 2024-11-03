from sanic import Sanic, response
from sanic.request import Request
from node.node import Node
from pod.pod import Pod
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


app = Sanic(__name__)
CORS(app)

# 初始化各个控制器
etcd_client = EtcdClient()
container_manager = ContainerManager(etcd_client)
container_runtime = ContainerRuntime(etcd_client)
image_handler = ImageHandler()
pod_controller = PodController(etcd_client)
node_controller = NodeController(etcd_client)
ddqn_scheduler = DDQNScheduler(node_controller)
kube_scheduler = Kube_Scheduler_Plus(node_controller)

def configure_routes(app):
        # Pod 相关路由
    @app.route('/pods', methods=['POST'])
    async def create_pod(request: Request):
        data = await request.json()  # Ensure we're awaiting the JSON parsing
        try:
            metadata = data.get("metadata")
            spec = data.get("spec")
            name = metadata.get("name")
            namespace = metadata.get("namespace", "default")
            
            # Create a list to hold Container objects
            containers = []

            # Iterate through each container definition in the JSON
            for container_data in spec.get("containers", []):
                container_name = container_data.get("name")
                container_image = container_data.get("image")
                container_command = container_data.get("command")
                container_ports = container_data.get("ports", [])
                container_resources = container_data.get("resources", {})

                # Extract port numbers for the Container class
                ports = [port['containerPort'] for port in container_ports] if container_ports else []

                # Create a Container object
                container = Container(
                    name=container_name,
                    image=container_image,
                    command=container_command,
                    resources=container_resources,
                    ports=ports
                )
                containers.append(container)

            # Call the pod controller to create the pod
            pod_controller.create_pod(name, containers, namespace)

            return response.json({'message': f"Pod '{name}' created successfully."}, status=201)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

configure_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)