from setuptools import setup, find_packages

setup(
    name='container_engine',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'flask', 'pyyaml', 'requests', 'containerd',"sanic","etcd","protobuf==3.20.1","tenserflow","pyyaml","psutil","GPUtil","matplotlib"
    ],
    entry_points={
        'console_scripts': [
            'container-engine=api.api_server:main',
        ],
    },
)