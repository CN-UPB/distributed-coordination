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
    name='coord-sim',
    version='0.9.3',
    description='Simulate flow-level, inter-node network coordination including scaling and placement of services and '
                'scheduling/balancing traffic between them.',
    url='https://github.com/CN-UPB/coordination-simulation',
    author='Stefan Schneider',
    dependency_links=dependency_links,
    author_email='stefan.schneider@upb.de',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=requirements + test_requirements,
    test_requirements=test_requirements,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'coord-sim=coordsim.main:main',
        ],
    },
)
