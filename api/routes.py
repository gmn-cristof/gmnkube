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
    # 容器相关路由
    @app.route('/containers/post', methods=['POST'])
    async def create_container(request: Request):
        data = request.json
        image = data.get('image')
        name = data.get('name')
        
        if not image or not name:
            return response.json({'error': 'Image and name are required.'}, status=400)

        try:
            container_manager.create_container(image, name)
            return response.json({'message': f"Container '{name}' created successfully."}, status=201)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)
        # {
        #   "name": "busybox-container",
        #   "image": "busybox",
        #   "command": ["sh", "-c", "sleep 3600"],
        #   "resources": {
        #     "requests": {
        #       "cpu": "50m",
        #       "memory": "128Mi"
        #     },
        #     "limits": {
        #       "cpu": "100m",
        #       "memory": "256Mi"
        #     }
        #   }
        # }

    @app.route('/containers/<name>', methods=['DELETE'])
    async def delete_container(request: Request, name: str):
        try:
            container_manager.delete_container(name)
            return response.json({'message': f"Container '{name}' deleted successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/containers/get', methods=['GET'])
    async def list_containers(request: Request):
        try:
            containers = container_manager.list_containers()
            return response.json({'containers': containers}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/containers/<name>', methods=['GET'])
    async def get_container_info(request: Request, name: str):
        try:
            info = container_manager.container_info(name)
            return response.json({'container_info': info}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)
        
    @app.route('/containers/<name>/start', methods=['POST'])
    async def start_container(request: Request, name: str):
        try:
            container_runtime.start_container(name)
            return response.json({'message': f"Container '{name}' started successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/containers/<name>/stop', methods=['POST'])
    async def stop_container(request: Request, name: str):
        try:
            container_runtime.stop_container(name)
            return response.json({'message': f"Container '{name}' stopped successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    # 镜像相关路由
    @app.route('/images/pull', methods=['POST'])
    async def pull_image(request: Request):
        image = request.json.get('image')
        if not image:
            return response.json({'error': 'Image name is required.'}, status=400)

        success = image_handler.pull_image(image)
        if success:
            return response.json({'message': f"Image '{image}' pulled successfully."}, status=200)
        else:
            return response.json({'error': f"Failed to pull image '{image}'."}, status=500)

    @app.route('/images', methods=['GET'])
    async def list_images(request: Request):
        images = image_handler.list_images()
        if images is not None:
            return response.json({'images': images}, status=200)
        else:
            return response.json({'error': 'Failed to list images.'}, status=500)

    @app.route('/images/remove', methods=['DELETE'])
    async def remove_image(request: Request):
        image = request.json.get('image')
        if not image:
            return response.json({'error': 'Image name is required.'}, status=400)

        success = image_handler.remove_image(image)
        if success:
            return response.json({'message': f"Image '{image}' removed successfully."}, status=200)
        else:
            return response.json({'error': f"Failed to remove image '{image}'."}, status=500)

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




    @app.route('/pods/yaml', methods=['POST'])
    async def create_pod_from_yaml(request: Request):
        yaml_file = request.json.get("yaml_file")
        #print(yaml_file)
        try:
            pod_controller.create_pod_from_yaml(yaml_file)
            return response.json({'message': f"Pod created from YAML '{yaml_file}' successfully."}, status=201)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/pods/<name>', methods=['DELETE'])
    async def delete_pod(request: Request, name: str):
        try:
            pod_controller.delete_pod(name)
            return response.json({'message': f"Pod '{name}' deleted successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/pods/<name>', methods=['GET'])
    async def get_pod(request: Request, name: str):
        pod = pod_controller.get_pod(name)
        if pod:
            return response.json({'pod': pod}, status=200)
        else:
            return response.json({'error': f"Pod '{name}' not found."}, status=404)

    @app.route('/pods', methods=['GET'])
    async def list_pods(request: Request):
        try:
            pods = pod_controller.list_pods()
            return response.json({'pods': pods}, status=200)
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

    # Node 相关路由
    @app.route('/nodes', methods=['POST'])
    async def add_node(request: Request):
        data = request.json
        try:
            name = data['name']
            ip_address = data['ip_address']
            total_cpu = data['total_cpu']
            total_memory = data['total_memory']
            total_gpu = data.get('total_gpu', 0)
            total_io = data.get('total_io', 0)
            total_net = data.get('total_net', 0)
            labels = data.get('labels', {})
            annotations = data.get('annotations', {})
            
            node_controller.add_node(name, ip_address, total_cpu, total_memory, total_gpu, total_io, total_net, labels, annotations)
            return response.json({'message': f"Node '{name}' added successfully."}, status=201)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/nodes/<name>', methods=['DELETE'])
    async def remove_node(request: Request, name: str):
        try:
            node_controller.remove_node(name)
            return response.json({'message': f"Node '{name}' removed successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/nodes', methods=['GET'])
    async def list_nodes(request: Request):
        try:
            nodes = node_controller.list_nodes()
            return response.json({'nodes': nodes}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/nodes/<name>', methods=['GET'])
    async def get_node(request: Request, name: str):
        try:
            node = node_controller.get_node(name)
            return response.json({'node': node.to_dict()}, status=200)  # 假设 Node 类有 to_dict 方法
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/nodes/<name>/schedule', methods=['POST'])
    async def schedule_pod_on_node(request: Request, name: str):
        data = request.json
        pod_name = data.get('pod_name')
        try:
            pod_controller.schedule_pod_to_node(pod_name, name)
            return response.json({'message': f"Pod '{pod_name}' scheduled to Node '{name}' successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    # DDQN 调度相关路由
    @app.route('/ddqn/schedule', methods=['POST'])
    async def ddqn_schedule(request: Request):
        pod_name = request.json.get('pod_name')
        try:
            node_name = ddqn_scheduler.schedule_pod(pod_name)
            return response.json({'message': f"Pod '{pod_name}' scheduled to Node '{node_name}' using DDQN."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    # Kube Scheduler 调度相关路由
    @app.route('/kube/schedule', methods=['POST'])
    async def kube_schedule(request: Request):
        pod_name = request.json.get('pod_name')
        try:
            node_name = kube_scheduler.schedule_pod(pod_name)
            return response.json({'message': f"Pod '{pod_name}' scheduled to Node '{node_name}' using Kube Scheduler."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

configure_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
