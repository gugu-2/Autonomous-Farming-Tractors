import os
from glob import glob
from setuptools import setup

package_name = 'agro_ai_sprayer'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*')))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='AGRO-AI Team',
    maintainer_email='dev@agro-ai.com',
    description='AGRO-AI Tier 2 Sprayer Logic and Launch Files',
    license='Proprietary',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'precision_spray_logic = agro_ai_sprayer.precision_spray_logic:main'
        ],
    },
)
