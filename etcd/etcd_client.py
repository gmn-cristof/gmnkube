# etcd/etcd_client.py

import etcd3
import logging

logger = logging.getLogger(__name__)

class EtcdClient:
    def __init__(self, host='localhost', port=2379):
        self.host = host
        self.port = port
        self.client = None
        self.connect()

    def connect(self):
        """与 etcd 集群建立连接，带有重试机制"""
        try:
            self.client = etcd3.client(host=self.host, port=self.port)
            logger.info(f"Connected to etcd at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to etcd: {e}")
            raise

    def put(self, key, value):
        """将键值对写入 etcd"""
        try:
            self.client.put(key, value)
            logger.info(f"Successfully put key {key} into etcd")
        except Exception as e:
            logger.error(f"Failed to put key {key} into etcd: {e}")

    def get(self, key):
        """从 etcd 读取键的值"""
        try:
            value, _ = self.client.get(key)
            logger.info(f"Retrieved value for key {key}")
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None

    def get_with_prefix(self, prefix):
        """根据前缀从 etcd 读取所有键值对"""
        try:
            values = self.client.get_prefix(prefix)  # 获取前缀的值
            result = []
            for kv in values:
                value = kv[0].decode('utf-8')  # 只取字节字符串部分
                result.append(value)
            
            logger.info(f"Values returned: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to get values with prefix {prefix}: {e}")
            return []

    def delete(self, key):
        """从 etcd 删除指定键"""
        try:
            self.client.delete(key)
            logger.info(f"Deleted key {key} from etcd")
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")

    def delete_with_prefix(self, prefix):
        """根据前缀删除 etcd 中的所有键"""
        try:
            # 获取所有匹配前缀的键值对
            values = self.client.get_prefix(prefix)
            keys_to_delete = [kv[0].decode('utf-8') for kv in values]  # 获取所有的键

            # 删除所有匹配的键
            for key in keys_to_delete:
                self.client.delete(key)
                logger.info(f"Deleted key {key} from etcd")

        except Exception as e:
            logger.error(f"Failed to delete keys with prefix {prefix}: {e}")

    def watch(self, key, callback):
        """监控指定键的变化，并执行回调"""
        try:
            events_iterator, cancel = self.client.watch(key)
            logger.info(f"Watching key {key} for changes")
            for event in events_iterator:
                if event.event_type == 'put':
                    callback(event.key, event.value)
                elif event.event_type == 'delete':
                    callback(event.key, None)
            return cancel
        except Exception as e:
            logger.error(f"Failed to watch key {key}: {e}")
            return None

    def lease(self, ttl):
        """为键值对设置一个TTL（生存时间），过期自动删除"""
        try:
            lease = self.client.lease(ttl)
            logger.info(f"Lease created with TTL: {ttl}")
            return lease
        except Exception as e:
            logger.error(f"Failed to create lease: {e}")
            return None

    def close(self):
        """关闭 etcd 连接"""
        if self.client:
            self.client.close()
            logger.info("Closed etcd client connection")
