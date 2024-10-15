# etcd/etcd_manager.py

from .etcd_client import EtcdClient
import logging

logger = logging.getLogger(__name__)

class EtcdManager:
    def __init__(self):
        self.client = EtcdClient()
    
    def save_data(self, key, value):
        """保存数据到 etcd"""
        logger.info(f"Saving data with key: {key}")
        self.client.put(key, value)
    
    def load_data(self, key):
        """从 etcd 加载数据"""
        logger.info(f"Loading data with key: {key}")
        return self.client.get(key)
    
    def delete_data(self, key):
        """从 etcd 删除数据"""
        logger.info(f"Deleting data with key: {key}")
        self.client.delete(key)
    
    def monitor_key(self, key, callback):
        """监控指定键的变化"""
        logger.info(f"Monitoring key: {key}")
        return self.client.watch(key, callback)
    
    def allocate_lease(self, key, value, ttl):
        """分配带TTL的键值对，适用于临时数据"""
        logger.info(f"Allocating lease for key: {key} with TTL: {ttl}")
        lease = self.client.lease(ttl)
        if lease:
            self.client.put(key, value, lease)
        else:
            logger.error(f"Failed to allocate lease for key: {key}")
    
    def close(self):
        """关闭 etcd 客户端连接"""
        logger.info("Closing etcd manager")
        self.client.close()
