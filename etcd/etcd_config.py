# etcd/etcd_config.py

import yaml
import logging

logger = logging.getLogger(__name__)

class EtcdConfig:
    def __init__(self, config_file='config/config.yaml'):
        self.config_file = config_file
        self.config_data = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r') as file:
                config_data = yaml.safe_load(file)
                logger.info(f"Successfully loaded config from {self.config_file}")
                return config_data
        except FileNotFoundError:
            logger.error(f"Config file {self.config_file} not found")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file {self.config_file}: {e}")
            raise
    
    def get_etcd_nodes(self):
        """获取 etcd 集群节点列表"""
        return self.config_data.get('etcd', {}).get('nodes', ['localhost:2379'])
    
    def get_lease_ttl(self):
        """获取租约 TTL 时间"""
        return self.config_data.get('etcd', {}).get('lease_ttl', 60)
