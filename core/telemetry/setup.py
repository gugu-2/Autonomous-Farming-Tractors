from setuptools import setup

package_name = 'agro_ai_telemetry'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'paho-mqtt'],
    zip_safe=True,
    maintainer='AGRO-AI Team',
    maintainer_email='dev@agro-ai.com',
    description='AGRO-AI Telemetry and IoT Bridge',
    license='Proprietary',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mqtt_bridge = agro_ai_telemetry.mqtt_bridge_node:main'
        ],
    },
)
