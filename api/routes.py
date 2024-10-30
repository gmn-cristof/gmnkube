from sanic import response
from sanic.request import Request
from container.container_manager import ContainerManager
from pod.pod_controller import PodController
from container.image_handler import ImageHandler
from node.node_controller import NodeController
from orchestrator.DDQN_scheduler import DDQNScheduler

# 初始化各个控制器
container_manager = ContainerManager()
image_handler = ImageHandler()
pod_controller = PodController()
node_controller = NodeController()
ddqn_scheduler = DDQNScheduler()

def configure_routes(app):
    # 容器相关路由
    @app.post('/api/containers')
    async def create_container(request: Request):
        data = request.json
        image = data['image']
        name = data['name']
        container_manager.create_container(image, name)
        return response.json({"status": "created"}, status=201)

    @app.delete('/api/containers/<name>')
    async def delete_container(request: Request, name):
        container_manager.delete_container(name)
        return response.empty(status=204)

    # 镜像相关路由
    @app.post('/api/images')
    async def pull_image(request: Request):
        data = request.json
        image = data['image']
        image_handler.pull_image(image)
        return response.json({"status": "pulled"}, status=201)

    @app.get('/api/images')
    async def list_images(request: Request):
        images = image_handler.list_images()
        return response.json(images, status=200)

    # Pod 相关路由
    @app.post('/api/pods')
    async def create_pod(request: Request):
        data = request.json
        name = data['name']
        image = data['image']
        pod_controller.create_pod(name, image)
        return response.json({"status": "created"}, status=201)

    @app.delete('/api/pods/<name>')
    async def delete_pod(request: Request, name):
        pod_controller.delete_pod(name)
        return response.empty(status=204)

    @app.get('/api/pods')
    async def list_pods(request: Request):
        pods = pod_controller.list_pods()
        return response.json(pods, status=200)

    @app.get('/api/pods/<name>')
    async def get_pod(request: Request, name):
        pod = pod_controller.get_pod(name)
        if pod:
            return response.json({"name": pod.name, "image": pod.image, "status": pod.status}, status=200)
        else:
            return response.json({"error": "Pod not found"}, status=404)

    # Node 相关路由
    @app.post('/api/nodes')
    async def add_node(request: Request):
        data = request.json
        name = data['name']
        total_cpu = data['total_cpu']
        total_memory = data['total_memory']
        labels = data.get('labels', {})
        annotations = data.get('annotations', {})
        node_controller.add_node(name, total_cpu, total_memory, labels, annotations)
        return response.json({"status": "Node created"}, status=201)

    @app.delete('/api/nodes/<name>')
    async def remove_node(request: Request, name):
        node_controller.remove_node(name)
        return response.empty(status=204)

    @app.get('/api/nodes')
    async def list_nodes(request: Request):
        nodes = node_controller.list_nodes()
        node_data = {node_name: node.to_dict() for node_name, node in nodes.items()}
        return response.json(node_data, status=200)

    @app.get('/api/nodes/<name>')
    async def get_node(request: Request, name):
        try:
            node = node_controller.get_node(name)
            return response.json(node.to_dict(), status=200)
        except Exception as e:
            return response.json({"error": str(e)}, status=404)

    @app.post('/api/nodes/<node_name>/pods')
    async def schedule_pod_to_node(request: Request, node_name):
        data = request.json
        pod_name = data['pod_name']
        pod = pod_controller.get_pod(pod_name)
        if not pod:
            return response.json({"error": "Pod not found"}, status=404)
        node_controller.schedule_pod_to_node(pod, node_name)
        return response.json({"status": "Pod scheduled to node"}, status=200)

    @app.delete('/api/nodes/<node_name>/pods/<pod_name>')
    async def remove_pod_from_node(request: Request, node_name, pod_name):
        pod = pod_controller.get_pod(pod_name)
        if not pod:
            return response.json({"error": "Pod not found"}, status=404)
        node_controller.remove_pod_from_node(pod, node_name)
        return response.json({"status": "Pod removed from node"}, status=200)

    @app.put('/api/nodes/<node_name>/status')
    async def update_node_status(request: Request, node_name):
        data = request.json
        status = data['status']
        node_controller.update_node_status(node_name, status)
        return response.json({"status": "Node status updated"}, status=200)
