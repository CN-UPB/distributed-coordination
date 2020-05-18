import os
from setuptools import setup, find_packages

# install packages on GitHub
os.system('pip install git+https://github.com/RealVNF/common-utils')
os.system('pip install git+https://github.com/CN-UPB/B-JointSP.git')

requirements = [
    'simpy',
    'networkx==2.3',
    'geopy',
    'pyyaml>=5.1',
    'numpy',
    'common-utils',
    'pandas'
]

test_requirements = [
    'flake8',
    'pytest',
    'nose2'
]

setup(
    name='distributed-coordination',
    version='1.0.0',
    description='Algorithms for fully distributed service coordination. With simulator built in.',
    url='https://github.com/CN-UPB/distributed-coordination',
    author='Stefan Schneider',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=requirements + test_requirements,
    test_requirements=test_requirements,
    zip_safe=False
)
