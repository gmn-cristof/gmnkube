from sanic import Sanic, response
from sanic.request import Request
from container.container_manager import ContainerManager
from pod.pod_controller import PodController
from container.image_handler import ImageHandler

app = Sanic("ContainerAPI")

container_manager = ContainerManager()
image_handler = ImageHandler()
pod_controller = PodController()

# 创建容器
@app.post('/api/containers')
async def create_container(request: Request):
    data = request.json
    image = data['image']
    name = data['name']
    container_manager.create_container(image, name)
    return response.json({"status": "created"}, status=201)

# 删除容器
@app.delete('/api/containers/<name>')
async def delete_container(request: Request, name):
    container_manager.delete_container(name)
    return response.empty(status=204)

# 拉取镜像
@app.post('/api/images')
async def pull_image(request: Request):
    data = request.json
    image = data['image']
    image_handler.pull_image(image)
    return response.json({"status": "pulled"}, status=201)

# 列出所有镜像
@app.get('/api/images')
async def list_images(request: Request):
    images = image_handler.list_images()
    return response.json(images, status=200)

# 创建 Pod
@app.post('/api/pods')
async def create_pod(request: Request):
    data = request.json
    name = data['name']
    image = data['image']
    pod_controller.create_pod(name, image)
    return response.json({"status": "created"}, status=201)

# 删除 Pod
@app.delete('/api/pods/<name>')
async def delete_pod(request: Request, name):
    pod_controller.delete_pod(name)
    return response.empty(status=204)

# 列出所有 Pods
@app.get('/api/pods')
async def list_pods(request: Request):
    pods = pod_controller.list_pods()
    return response.json(pods, status=200)

# 获取单个 Pod 信息
@app.get('/api/pods/<name>')
async def get_pod(request: Request, name):
    pod = pod_controller.get_pod(name)
    if pod:
        return response.json({"name": pod.name, "image": pod.image, "status": pod.status}, status=200)
    else:
        return response.json({"error": "Pod not found"}, status=404)

