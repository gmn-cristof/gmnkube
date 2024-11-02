from sanic import response
from sanic.request import Request
from container.container_manager import ContainerManager
from pod.pod_controller import PodController
from container.image_handler import ImageHandler
from node.node_controller import NodeController
from orchestrator.DDQN_scheduler import DDQNScheduler
from orchestrator.kube_scheduler_plus import Kube_Scheduler_Plus

# 初始化各个控制器
container_manager = ContainerManager()
image_handler = ImageHandler()
pod_controller = PodController()
node_controller = NodeController()
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

    @app.route('/containers', methods=['GET'])
    async def list_containers(request: Request):
        try:
            containers = container_runtime.list_containers()
            return response.json({'containers': containers}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/containers/remove/<name>', methods=['DELETE'])
    async def remove_container(request: Request, name: str):
        try:
            container_runtime.remove_container(name)
            return response.json({'message': f"Container '{name}' removed successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/containers/<name>/inspect', methods=['GET'])
    async def inspect_container(request: Request, name: str):
        try:
            container_info = container_runtime.inspect_container(name)
            return response.json({'container_info': container_info}, status=200)
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
        data = request.json
        try:
            name = data.get("name")
            containers = data.get("containers")
            namespace = data.get("namespace", "default")
            pod_controller.create_pod(name, containers, namespace)
            return response.json({'message': f"Pod '{name}' created successfully."}, status=201)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/pods/yaml', methods=['POST'])
    async def create_pod_from_yaml(request: Request):
        yaml_file = request.json.get("yaml_file")
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
    async def schedule_pod(request: Request, name: str):
        data = request.json
        try:
            pod = data['pod']  # 假设 pod 是一个对象或字典
            node_controller.schedule_pod_to_node(pod, name)
            return response.json({'message': f"Pod scheduled to node '{name}'."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/nodes/<name>/remove_pod', methods=['POST'])
    async def remove_pod(request: Request, name: str):
        data = request.json
        try:
            pod = data['pod']  # 假设 pod 是一个对象或字典
            node_controller.remove_pod_from_node(pod, name)
            return response.json({'message': f"Pod removed from node '{name}'."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/nodes/<name>/status', methods=['PATCH'])
    async def update_node_status(request: Request, name: str):
        data = request.json
        try:
            status = data['status']
            node_controller.update_node_status(name, status)
            return response.json({'message': f"Node '{name}' status updated to '{status}'."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)
        
    #DDQN调度器相关：
    @app.route('/DDQN/schedule', methods=['POST'])
    async def schedule_pod(request: Request):
        data = request.json
        try:
            pod = data['pod']  # 假设 pod 是一个对象或字典
            ddqn_scheduler.schedule_pod(pod)
            return response.json({'message': f"Pod '{pod['name']}' scheduled successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/DDQN/scheduler/state', methods=['GET'])
    async def get_scheduler_state(request: Request):
        """获取当前调度器状态（例如，epsilon 值等）。"""
        try:
            state = {
                'epsilon': ddqn_scheduler.epsilon,
                'memory_size': len(ddqn_scheduler.memory)
            }
            return response.json({'scheduler_state': state}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/DDQN/scheduler/update', methods=['POST'])
    async def update_scheduler_config(request: Request):
        """更新调度器的配置，例如学习率、epsilon 等。"""
        data = request.json
        try:
            if 'learning_rate' in data:
                ddqn_scheduler.learning_rate = data['learning_rate']
                ddqn_scheduler.model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(learning_rate=ddqn_scheduler.learning_rate))
            
            if 'gamma' in data:
                ddqn_scheduler.gamma = data['gamma']
            
            return response.json({'message': "Scheduler configuration updated successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/DDQN/scheduler/memory', methods=['GET'])
    async def get_memory_size(request: Request):
        """获取当前记忆的大小。"""
        try:
            memory_size = len(ddqn_scheduler.memory)
            return response.json({'memory_size': memory_size}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)
        
    #kube_schedule相关
    @app.route('/kube/schedule', methods=['POST'])
    async def schedule_pod(request: Request):
        data = request.json
        try:
            pod_name = data['pod_name']  # 假设 pod_name 是一个字符串
            required_resources = data['required_resources']  # 假设这是一个字典
            kube_scheduler.schedule_pod(pod_name, required_resources)
            return response.json({'message': f"Pod '{pod_name}' scheduled successfully."}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/kube/nodes', methods=['GET'])
    async def list_nodes(request: Request):
        """列出所有可用节点的信息。"""
        try:
            nodes = node_controller.list_nodes()
            return response.json({'nodes': nodes}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

    @app.route('/kube/nodes/filter', methods=['POST'])
    async def filter_nodes(request: Request):
        """根据所需资源过滤可用节点。"""
        data = request.json
        required_resources = data['required_resources']  # 假设这是一个字典
        try:
            available_nodes = kube_scheduler.filter_nodes(required_resources)
            return response.json({'available_nodes': available_nodes}, status=200)
        except Exception as e:
            return response.json({'error': str(e)}, status=500)

