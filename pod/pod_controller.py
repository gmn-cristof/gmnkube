import logging
import yaml,json
from .pod import Pod
from container.container import Container
from etcd.etcd_client import EtcdClient  

class PodController:
    def __init__(self, etcd_client):
        self.pods = {}
        self.etcd_client = etcd_client

    def create_pod(self, name: str, containers: list, namespace: str = 'default'):
        """Creates a new Pod with a list of containers"""
        if name in self.pods:
            logging.error(f"Pod '{name}' already exists.")
            raise ValueError(f"Pod '{name}' already exists.")

        pod = Pod(name=name, containers=containers, namespace=namespace)
        try:
            #pod.start()
            self.pods[name] = pod
            # 将 Pod 状态同步到 etcd
            self.etcd_client.put(f"/pods/{namespace}/{name}/status", "Created")
            logging.info(f"Pod '{name}' created successfully with containers: {[c.name for c in containers]}.")
        except Exception as e:
            logging.error("An error occurred", exc_info=True)
            logging.error(f"Failed to create Pod '{name}'. Containers: {containers}. Error: {e}")
            raise

    def create_pod_from_yaml(self, yaml_file: str):
        """Creates a Pod from a YAML file"""
        try:
            with open(yaml_file, 'r') as file:
                pod_config = yaml.safe_load(file)
            
            if pod_config['kind'] != 'Pod':
                raise ValueError("Invalid YAML file: kind must be 'Pod'")

            name = pod_config['metadata']['name']
            namespace = pod_config['metadata'].get('namespace', 'default')
            containers = [
                Container(
                    name=c['name'],
                    image=c['image'],
                    resources=c.get('resources', {}),
                    ports=c.get('ports', [])
                ) for c in pod_config['spec']['containers']
            ]
            self.create_pod(name, containers, namespace)

        except Exception as e:
            print(f"Failed to create Pod '{name}': {str(e)}")
        
        except FileNotFoundError:
            logging.error(f"YAML file '{yaml_file}' not found.")
            raise
        except KeyError as e:
            logging.error(f"Invalid YAML structure, missing key: {e}")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file '{yaml_file}': {e}")
            raise
        except Exception as e:
            logging.error(f"Failed to create Pod from YAML '{yaml_file}': {e}")
            raise

    def delete_pod(self, name: str):
        """Deletes a Pod after stopping it"""
        if name not in self.pods:
            logging.error(f"Pod '{name}' not found.")
            raise ValueError(f"Pod '{name}' not found.")

        pod = self.pods[name]
        try:
            pod.stop()
            del self.pods[name]
            # 从 etcd 中删除该 Pod 的状态记录
            self.etcd_client.delete(f"/pods/{pod.namespace}/{name}")
            logging.info(f"Pod '{name}' deleted successfully.")
        except Exception as e:
            logging.error(f"Failed to delete Pod '{name}': {e}")
            raise

    def get_pod(self, name: str):
        """Get Pod details"""
        pod = self.pods.get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found.")
        return pod

    def list_pods(self):
        """List all Pod names"""
        pod_list = list(self.pods.keys())
        logging.info(f"Listing all pods: {pod_list}")
        return pod_list

    def start_pod(self, name: str):
        """Starts a Pod and updates etcd status"""
        pod = self.pods.get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found.")
            raise ValueError(f"Pod '{name}' not found.")

        try:
            pod.start()
            # 更新 etcd 中的 Pod 状态
            self.etcd_client.put(f"/pods/{pod.namespace}/{name}/status", "Running")
            logging.info(f"Pod '{name}' started successfully.")
        except Exception as e:
            logging.error(f"Failed to start Pod '{name}': {e}")
            raise


    def stop_pod(self, name: str):
        """Stops a Pod and updates etcd status"""
        pod = self.pods.get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found.")
            raise ValueError(f"Pod '{name}' not found.")
        
        try:
            pod.stop()
            # 更新 etcd 中的 Pod 状态
            self.etcd_client.put(f"/pods/{pod.namespace}/{name}/status", "Stopped")
            logging.info(f"Pod '{name}' stopped successfully.")
        except Exception as e:
            logging.error(f"Failed to stop Pod '{name}': {e}")
            raise

    def restart_pod(self, name: str):
        """Restarts a Pod and updates etcd status"""
        pod = self.pods.get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found.")
            raise ValueError(f"Pod '{name}' not found.")
        
        try:
            pod.stop()
            pod.start()
            # 更新 etcd 中的 Pod 状态
            self.etcd_client.put(f"/pods/{pod.namespace}/{name}/status", "Running")
            logging.info(f"Pod '{name}' restarted successfully.")
        except Exception as e:
            logging.error(f"Failed to restart Pod '{name}': {e}")
            raise

    def get_all_pods(self):
        """获取所有 Pods 的信息"""
        try:
            pod_values = self.etcd_client.get_with_prefix("pods/")  # 使用 EtcdClient 的方法
            pod_info_list = {}

            for value in pod_values:
                pod_data = json.loads(value)  # 解析 JSON 字符串
                pod_name = pod_data['metadata']['name']  # 获取 Pod 名称
                pod_info_list[pod_name] = pod_data  # 存储 Pod 数据

            logging.info(f"Retrieved all pods: {pod_info_list}")
            return pod_info_list
        except Exception as e:
            logging.error(f"Failed to get all pods: {e}")
            return {}
