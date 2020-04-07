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

dependency_links = [
    'git+https://github.com/RealVNF/coord-env-interface'
]

setup(
    name='distributed-coordination',
    version='0.9.4',
    description='Fully distributed algorithms for service coordination. With simulator built in.',
    url='https://github.com/CN-UPB/distributed-coordination',
    author='Stefan Schneider',
    dependency_links=dependency_links,
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=requirements + test_requirements,
    test_requirements=test_requirements,
    zip_safe=False
)
