from setuptools import setup

package_name = 'agro_ai_world_model'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'ultralytics'],
    zip_safe=True,
    maintainer='AGRO-AI Team',
    maintainer_email='dev@agro-ai.com',
    description='AGRO-AI World Model and YOLOv8 Inference Node',
    license='Proprietary',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'trt_yolo_node = agro_ai_world_model.trt_yolo_node:main'
        ],
    },
)
