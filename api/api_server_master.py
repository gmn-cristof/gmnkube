from sanic import Sanic, response, SanicException
from sanic.response import json
from sanic.request import Request
#from tensorflow.keras.utils import plot_model
from container.container import Container
from etcd.etcd_client import EtcdClient
from container.container_manager import ContainerManager
from container.container_runtime import ContainerRuntime
from pod.pod_controller import PodController
from container.image_handler import ImageHandler
from node.node_controller import NodeController

from orchestrator.kube_scheduler_plus import Kube_Scheduler_Plus
from sanic_cors import CORS
import logging,json

app = Sanic(__name__)
app.config.DEBUG = True
CORS(app)

# 全局唯一的调度器实例
ddqn_scheduler = None
use_ddqn = False

# 初始化控制器
etcd_client = EtcdClient()
container_manager = ContainerManager(etcd_client)
container_runtime = ContainerRuntime(etcd_client)
image_handler = ImageHandler()
pod_controller = PodController(etcd_client, container_manager, container_runtime)
node_controller = NodeController(etcd_client)
kube_scheduler = Kube_Scheduler_Plus(node_controller)

def create_scheduler():
    global ddqn_scheduler
    if ddqn_scheduler is None and use_ddqn is True:
        from orchestrator.DDQN_scheduler import DDQNScheduler
        ddqn_scheduler = DDQNScheduler(node_controller)

    

def configure_routes(app):
    # Node 相关路由
    @app.route('/nodes', methods=['POST'])
    async def add_node(request: Request):
        # print(f"Request type: {type(request)}")
        # print(f"Request content: {request}")
        
        try:
            data = request.json  # Ensure JSON parsing is awaited.
            #print(f"Received data: {data}")

            # Check that essential fields are present
            if not all(key in data for key in ['name', 'ip_address']):
                return response.json({'error': 'Missing required fields: name or ip_address'}, status=400)

            name = data['name']
            ip_address = data['ip_address']
            
            # Fetch values using get() with default 0 for missing fields
            total_cpu = data.get('total_cpu', 0)
            total_memory = data.get('total_memory', 0)
            total_gpu = data.get('total_gpu', 0)
            total_io = data.get('total_io', 0)
            total_net = data.get('total_net', 0)
            labels = data.get('labels', {})
            annotations = data.get('annotations', {})

            # Debugging: Log the values being passed to add_node
            # print(f"Adding node with values: {name}, {ip_address}, {total_cpu}, {total_memory}, {total_gpu}, {total_io}, {total_net}, {labels}, {annotations}")

            # Add node to the controller
            node_controller.add_node(name, ip_address, total_cpu, total_memory, total_gpu, total_io, total_net, labels, annotations)

            return response.json({'message': f"Node '{name}' added successfully."}, status=201)

        except KeyError as e:
            # Handle specific missing key errors
            return response.json({'error': f"Missing key: {str(e)}"}, status=400)
        except Exception as e:
            # Catch other exceptions
            return response.json({'error': f"Error: {str(e)}"}, status=500)


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
            node_controller._update_etcd_node()
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
    async def schedule_pod_on_node(request, name: str):
        try:
            # 获取请求体中的JSON数据
            pod_data = request.json

            # 提取 Pod 的元数据和规范
            metadata = pod_data.get("metadata", {})
            #spec = pod_data.get("spec", {})

            pod_name = metadata.get("name")
            namespace = metadata.get("namespace", "default")

            # 这里假设你已经有了pod_controller和node_controller来处理Pod调度逻辑
            pod = pod_controller.get_pod(pod_name ,namespace)

            # 调度Pod到指定的节点
            node_controller.schedule_pod_to_node(pod, name)

            # 启动Pod
            pod_controller.start_pod(pod_name, namespace)

            # 返回成功响应
            return json({'message': f"Pod '{pod_name}' scheduled to Node '{name}' successfully."}, status=200)
        except KeyError as e:
            # 如果数据中缺少必要的字段，返回400错误
            logging.error(f"Missing field in request data: {e}")
            return json({'error': f"Missing field: {e}"}, status=400)
        except Exception as e:
            # 捕获其他异常并记录
            logging.error("An error occurred while scheduling pod", exc_info=True)
            return json({'error': str(e)}, status=500)
   
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
            pod_controller.delete_pod(name,"default")
            return response.json({'message': f"Pod '{name}' deleted successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/pods', methods=['GET'])
    async def list_pods(request: Request):
        try:
            # 从 etcd 获取所有 Pods 信息
            pods = pod_controller.get_all_pods()
            return response.json({'pods': pods}, status=200)
        except Exception as e:
            logging.error(f"Error while listing pods: {e}")
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
        
    #DDQN 调度相关路由
    @app.route("/DDQN_schedule", methods=["POST"])
    async def DDQN_schedule_pod(request):
        """调度一个 Pod 到合适的节点."""
        try:
            pod_data = request.json  # 从请求中获取 Pod 数据

            # 提取 Pod 的元数据和规范
            metadata = pod_data.get("metadata", {})
            #spec = pod_data.get("spec", {})

            pod_name = metadata.get("name")
            namespace = metadata.get("namespace", "default")


            # 调用调度器调度 Pod
            pod=pod_controller.get_pod(pod_name, namespace)
            node_name=ddqn_scheduler.schedule_pod(pod)
            #pod_controller.start_pod(pod_name, namespace)
            #node_controller._update_etcd_node()
            return response.json({"status": "success", "message": f"Pod '{pod_name}' scheduled successfully at '{node_name}'."})

        except SanicException as e:
            return response.json({"status": "error", "message": str(e)}, status=400)
        except Exception as e:
            return response.json({"status": "error", "message": f"Failed to schedule Pod: {str(e)}"}, status=500)

    @app.delete("/pods")
    async def remove_all_pods(request):
        """
        清空集群中所有 Pods。
        HTTP DELETE /pods
        """
        try:
            # 假设 node_controller 是全局实例
            node_controller.remove_all_pods()
            
            return response.json({"message": "All Pods have been removed from the cluster."}, status=200)
        except Exception as e:
            # 捕获异常并返回错误信息
            return response.json({"error": str(e)}, status=500)
        
    @app.route("/kube_schedule", methods=["POST"])
    async def kube_schedule_pod(request):
        """调度一个 Pod 到合适的节点."""
        try:
            pod_data = request.json  # 从请求中获取 Pod 数据

            # 提取 Pod 的元数据和规范
            metadata = pod_data.get("metadata", {})
            #spec = pod_data.get("spec", {})

            pod_name = metadata.get("name")
            namespace = metadata.get("namespace", "default")


            # 调用调度器调度 Pod
            pod=pod_controller.get_pod(pod_name, namespace)
            node_name=kube_scheduler.schedule_pod(pod)
            #pod_controller.start_pod(pod_name, namespace)
            #node_controller._update_etcd_node()
            return response.json({"status": "success", "message": f"Pod '{pod_name}' scheduled successfully at '{node_name}'."})

        except SanicException as e:
            return response.json({"status": "error", "message": str(e)}, status=400)
        except Exception as e:
            return response.json({"status": "error", "message": f"Failed to schedule Pod: {str(e)}"}, status=500)

    @app.route("/save_DDQN_schedule", methods=["POST"])
    async def save_DDQN_schedule(request):
        try:
            # 从 POST 请求中获取文件路径（可选参数），默认为 "output/schedule_history.png"
            file_path = request.json.get("file_path", "output/schedule_history.png")

            # 调用调度器的保存方法并获取结果
            ddqn_scheduler.save_schedule_history(file_path)

            # 返回成功的 JSON 响应
            return response.json({"message": "Schedule saved successfully"}, status=200)
        
        except Exception as e:
            # 捕获异常并返回错误信息
            return response.json({"error": str(e)}, status=500)

    @app.route("/save_kube_schedule", methods=["POST"])
    async def save_kube_schedule(request):
        try:
            # 从 POST 请求中获取文件路径（可选参数），默认为 "output/schedule_history.png"
            file_path = request.json.get("file_path", "output/schedule_history.png")

            # 调用调度器的保存方法并获取结果
        # 异步调用保存操作
            kube_scheduler.save_schedule_history(file_path)

            # 返回成功的 JSON 响应
            return response.json({"message": "Schedule saved successfully"}, status=200)
        
        except Exception as e:
            # 捕获异常并返回错误信息
            return response.json({"error": str(e)}, status=500)


            
configure_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)
