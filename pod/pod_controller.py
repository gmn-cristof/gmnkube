import logging
import yaml
import json
from .pod import Pod
from container.container import Container

class PodController:
    def __init__(self, etcd_client, container_manager, container_runtime):
        self.pods = {}  # 命名空间到 Pod 字典的映射
        self.etcd_client = etcd_client
        self.container_manager = container_manager
        self.container_runtime = container_runtime

    def create_pod(self, name: str, containers: list, namespace: str = 'default'):
        """Creates a new Pod with a list of containers in the specified namespace."""
        # 初始化命名空间的 Pods 字典
        if namespace not in self.pods:
            self.pods[namespace] = {}

        if name in self.pods[namespace]:
            logging.error(f"Pod '{name}' already exists in namespace '{namespace}'.")
            raise ValueError(f"Pod '{name}' already exists in namespace '{namespace}'.")

        pod = Pod(name=name, containers=containers, namespace=namespace)
        try:
            self.pods[namespace][name] = pod
            # 将 Pod 状态同步到 etcd
            #print(pod_data)
            pod_data=json.dumps(pod.to_dict())
            self.etcd_client.put(f"pods/{namespace}/{name}", pod_data)
            self.etcd_client.put(f"/pods/{namespace}/{name}/status", "Created")
            logging.info(f"Pod '{name}' created successfully in namespace '{namespace}' with containers: {[c.name for c in containers]}.")
        except Exception as e:
            logging.error("An error occurred", exc_info=True)
            logging.error(f"Failed to create Pod '{name}' in namespace '{namespace}'. Containers: {containers}. Error: {e}")
            raise

    def create_pod_from_yaml(self, yaml_file: str):
        """Creates a Pod from a YAML file."""
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

    def delete_pod(self, name: str, namespace: str = 'default'):
        """Deletes a Pod after stopping it."""
        if namespace not in self.pods or name not in self.pods[namespace]:
            logging.error(f"Pod '{name}' not found in namespace '{namespace}'.")
            raise ValueError(f"Pod '{name}' not found in namespace '{namespace}'.")
        try:
            self.stop_pod(name, namespace)
            del self.pods[namespace][name]
            # 从 etcd 中删除该 Pod 的状态记录
            self.etcd_client.delete_with_prefix(f"/pods/{namespace}/{name}")
            self.etcd_client.delete(f"pods/{namespace}/{name}")
            logging.info(f"Pod '{name}' deleted successfully from namespace '{namespace}'.")
        except Exception as e:
            logging.error(f"Failed to delete Pod '{name}' from namespace '{namespace}': {e}")
            raise

    def get_pod(self, name: str, namespace: str = 'default'):
        """Get Pod details in the specified namespace."""
        pod = self.pods.get(namespace, {}).get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found in namespace '{namespace}'.")
        return pod

    def list_pods(self, namespace: str = None):
        """List all Pod names in a specific namespace or across all namespaces."""
        if namespace:
            pod_list = list(self.pods.get(namespace, {}).keys())
            logging.info(f"Listing all pods in namespace '{namespace}': {pod_list}")
            return pod_list
        else:
            all_pods = {ns: list(pods.keys()) for ns, pods in self.pods.items()}
            logging.info(f"Listing all pods in all namespaces: {all_pods}")
            return all_pods

    def start_pod(self, name: str, namespace: str = 'default'):
        """Starts a Pod in the specified namespace and updates etcd status."""
        pod = self.pods.get(namespace, {}).get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found in namespace '{namespace}'.")
            raise ValueError(f"Pod '{name}' not found in namespace '{namespace}'.")

        try:
            if pod.status != 'Pending' and pod.status != 'Stopped':
                logging.error(f"Pod '{pod.name}' is already running or terminated.")
                return
            
            all_started = True
            for container in pod.containers:
                try:
                    self.container_manager.create_container(container)
                    self.container_runtime.start_container(container)
                    logging.info(f"Container '{container.name}' started successfully.")
                    # 将容器状态更新到 etcd
                    self.etcd_client.put(f"/pods/{namespace}/{name}/containers/{container.name}/status", "Running")
                except Exception as e:
                    logging.error(f"Failed to start container '{container.name}': {e}")
                    all_started = False
            
            if all_started:
                pod.status = 'Running'
                logging.info(f"Pod '{pod.name}' in namespace '{namespace}' is now running.")
            pod_data=json.dumps(pod.to_dict())
            self.etcd_client.put(f"pods/{namespace}/{name}", pod_data)
            self.etcd_client.put(f"/pods/{namespace}/{name}/status", "Running")
            logging.info(f"Pod '{name}' started successfully in namespace '{namespace}'.")
        except Exception as e:
            logging.error(f"Failed to start Pod '{name}' in namespace '{namespace}': {e}")
            raise

    def stop_pod(self, name: str, namespace: str = 'default'):
        """Stops a Pod in the specified namespace and updates etcd status."""
        pod = self.pods.get(namespace, {}).get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found in namespace '{namespace}'.")
            raise ValueError(f"Pod '{name}' not found in namespace '{namespace}'.")

        try:
            if pod.status != 'Running':
                logging.error(f"Pod '{pod.name}' is not running.")
                return
            
            all_stopped = True
            for container in pod.containers:
                try:
                    self.container_runtime.stop_container(container.name)
                    logging.info(f"Container '{container.name}' stopped successfully.")
                    self.etcd_client.put(f"/pods/{namespace}/{name}/containers/{container.name}/status", "Stopped")
                except Exception as e:
                    logging.error(f"Failed to stop container '{container.name}': {e}")
                    all_stopped = False

            if all_stopped:
                pod.status = 'Stopped'

                logging.info(f"Pod '{pod.name}' in namespace '{namespace}' has been stopped.")
            pod_data=json.dumps(pod.to_dict())
            self.etcd_client.put(f"pods/{namespace}/{name}", pod_data)
            self.etcd_client.put(f"/pods/{namespace}/{name}/status", "Stopped")
            logging.info(f"Pod '{name}' stopped successfully in namespace '{namespace}'.")
        except Exception as e:
            logging.error(f"Failed to stop Pod '{name}' in namespace '{namespace}': {e}")
            raise


    def restart_pod(self, name: str, namespace: str = 'default'):
        """Restarts a Pod and updates etcd status based on namespace"""
        # 获取指定命名空间下的 Pod 字典
        namespace_pods = self.pods.get(namespace, {})
        
        pod = namespace_pods.get(name)
        if not pod:
            logging.error(f"Pod '{name}' not found in namespace '{namespace}'.")
            raise ValueError(f"Pod '{name}' not found in namespace '{namespace}'.")
        
        try:
            self.stop_pod(name, namespace)  # 需要加上命名空间参数
            self.start_pod(name, namespace)  # 需要加上命名空间参数
            # 更新 etcd 中的 Pod 状态
            pod_data=json.dumps(pod.to_dict())
            self.etcd_client.put(f"pods/{namespace}/{name}", pod_data)
            self.etcd_client.put(f"/pods/{namespace}/{name}/status", "Running")
            logging.info(f"Pod '{name}' in namespace '{namespace}' restarted successfully.")
        except Exception as e:
            logging.error(f"Failed to restart Pod '{name}' in namespace '{namespace}': {e}")
            raise

    def get_all_pods(self):
        """获取所有 Pods 的信息，按命名空间区分"""
        try:
            pod_values = self.etcd_client.get_with_prefix("pods/")  # 使用 EtcdClient 的方法
            pod_info_list = {}

            for value in pod_values:
                pod_data = json.loads(value)  # 解析 JSON 字符串
                namespace = pod_data['namespace']  # 获取 Pod 所在的命名空间
                pod_name = pod_data['name']  # 获取 Pod 名称

                if namespace not in pod_info_list:
                    pod_info_list[namespace] = {}

                pod_info_list[namespace][pod_name] = pod_data  # 存储按命名空间分类的 Pod 数据

            logging.info(f"Retrieved all pods: {pod_info_list}")
            return pod_info_list
        except Exception as e:
            logging.error(f"Failed to get all pods: {e}")
            return {}
