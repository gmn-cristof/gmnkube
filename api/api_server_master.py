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
    