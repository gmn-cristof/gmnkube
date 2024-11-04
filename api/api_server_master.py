from sanic import Sanic, response, SanicException
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
#from orchestrator.DDQN_scheduler import DDQNScheduler
from orchestrator.kube_scheduler_plus import Kube_Scheduler_Plus
from sanic_cors import CORS
import logging,json

app = Sanic(__name__)
app.config.DEBUG = True
# CORS(app)

# 全局唯一的调度器实例
ddqn_scheduler = None

# 初始化控制器
etcd_client = EtcdClient()
container_manager = ContainerManager(etcd_client)
container_runtime = ContainerRuntime(etcd_client)
image_handler = ImageHandler()
pod_controller = PodController(etcd_client)
node_controller = NodeController(etcd_client)
kube_scheduler = Kube_Scheduler_Plus(node_controller)

# def create_scheduler():
#     global ddqn_scheduler
#     if ddqn_scheduler is None:
#         ddqn_scheduler = DDQNScheduler(node_controller)

# @app.listener('before_server_start')
# async def setup_scheduler(app, loop):
#     create_scheduler()  # 在服务器启动前创建调度器

def configure_routes(app):
    # Node 相关路由
    @app.route('/nodes', methods=['POST'])
    async def add_node(request: Request):
        data = request.json
        try:
            name = data['name']
            ip_address = data['ip_address']
            total_cpu = data.get('total_cpu', 0)  # 修改这一行
            total_memory = data.get('total_memory', 0)
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
            # 从 etcd 获取所有节点信息
            nodes = node_controller.get_all_nodes()
            return response.json({'nodes': nodes}, status=200)
        except Exception as e:
            logging.error(f"Error while listing nodes: {e}")
            return response.json({'error': str(e)}, status=500)


    @app.route('/nodes/<name>', methods=['GET'])
    async def get_node(request: Request, name: str):
        try:
            node = node_controller.get_node(name)
            return response.json({'node': node.to_dict()}, status=200)  
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

    @app.route('/pods/<name>', methods=['DELETE'])
    async def delete_pod(request: Request, name: str):
        try:
            pod_controller.delete_pod(name)
            return response.json({'message': f"Pod '{name}' deleted successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

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
        
    # DDQN 调度相关路由
    # @app.route("/DDQN_schedule", methods=["POST"])
    # async def schedule_pod(request):
    #     """调度一个 Pod 到合适的节点."""
    #     try:
    #         pod_data = request.json  # 从请求中获取 Pod 数据

    #         # 提取 Pod 的元数据和规范
    #         metadata = pod_data.get("metadata", {})
    #         spec = pod_data.get("spec", {})

    #         pod_name = metadata.get("name")
    #         namespace = metadata.get("namespace", "default")
    #         volumes = spec.get("volumes", [])
    #         # Create a list to hold Container objects
    #         containers = []

    #         # Iterate through each container definition in the JSON
    #         for container_data in spec.get("containers", []):
    #             container_name = container_data.get("name")
    #             container_image = container_data.get("image")
    #             container_command = container_data.get("command")
    #             container_ports = container_data.get("ports", [])
    #             container_resources = container_data.get("resources", {})

    #             # Extract port numbers for the Container class
    #             ports = [port['containerPort'] for port in container_ports] if container_ports else []

    #             # Create a Container object
    #             container = Container(
    #                 name=container_name,
    #                 image=container_image,
    #                 command=container_command,
    #                 resources=container_resources,
    #                 ports=ports
    #             )
    #             containers.append(container)
    #         # 创建 Pod 实例
    #         pod = Pod(name=pod_name, containers=containers, namespace=namespace, volumes=volumes)

    #         # 设置 Pod 资源请求和限制
    #         for container in containers:
    #             resources = container.get("resources", {})
    #             pod.resources['requests'].update(resources.get("requests", {}))
    #             pod.resources['limits'].update(resources.get("limits", {}))

    #         # 调用调度器调度 Pod
    #         ddqn_scheduler.schedule_pod(pod)
    #         return response.json({"status": "success", "message": f"Pod '{pod_name}' scheduled successfully."})

    #     except SanicException as e:
    #         return response.json({"status": "error", "message": str(e)}, status=400)
    #     except Exception as e:
    #         return response.json({"status": "error", "message": f"Failed to schedule Pod: {str(e)}"}, status=500)
        
configure_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)
