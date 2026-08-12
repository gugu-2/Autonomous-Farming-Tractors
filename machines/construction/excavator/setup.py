from setuptools import setup
package_name = 'agro_ai_excavator'
setup(
    name=package_name, version='1.0.0', packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'torch', 'numpy'], zip_safe=True,
    maintainer='AGRO-AI Team', maintainer_email='dev@agro-ai.com',
    description='AGRO-AI Excavator RL Trenching Node', license='Proprietary',
    entry_points={
        'console_scripts': [
            'trenching_rl_inference = agro_ai_excavator.trenching_rl_inference:main'
        ],
    },
)
