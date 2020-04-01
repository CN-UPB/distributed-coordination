import sys
import logging
import os

from siminterface.simulator import Simulator
from algorithms.greedy.gpasp import GPASPAlgo
from algorithms.score.spr1 import SPR1Algo
from algorithms.score.spr2 import SPR2Algo
from algorithms.prototypes.random.random_walk import RWAlgo
from algorithms.centralized.bjointsp_algo import BJointSPAlgo

log = logging.getLogger(__name__)


def main():
    # eg: python iteraton_runner.py 50 lnc ../../../../params/networks/dfn_58.graphml 0.1 gpasp
    run = sys.argv[1]
    scenario = sys.argv[2]
    network_path = sys.argv[3]
    network = os.path.basename(network_path)
    ingress = sys.argv[4]
    algo_id = sys.argv[5]

    args = {
        'network': network_path,
        'service_functions': '../../../../params/services/3sfcs.yaml',
        'resource_functions': '../../../../params/services/resource_functions',
        'config': f'configurations/{scenario}_{ingress}.yaml',
        'seed': int(run),
        'output_path': f'scenarios/{run}/{scenario}/{network}/{ingress}/{algo_id}'
    }

    os.makedirs(args['output_path'], exist_ok=True)

    logging.getLogger('coordsim').setLevel(logging.CRITICAL)
    logging.getLogger('coordsim.reader').setLevel(logging.CRITICAL)
    logging.getLogger('algorithms.centralized.bjointsp').setLevel(logging.WARNING)

    simulator = Simulator(test_mode=True)

    # Setup algorithm
    algo = None
    if algo_id == 'gpasp':
        algo = GPASPAlgo(simulator)
    elif algo_id == 'spr1':
        algo = SPR1Algo(simulator)
    elif algo_id == 'spr2':
        algo = SPR2Algo(simulator)
    elif algo_id == 'random':
        algo = RWAlgo(simulator)
    elif algo_id == 'bjointsp':
        algo = BJointSPAlgo(simulator)
    elif algo_id == 'bjointsp_recalc':
        algo = BJointSPAlgo(simulator, recalc_before_drop=True)

    algo.init(os.path.abspath(args['network']),
              os.path.abspath(args['service_functions']),
              os.path.abspath(args['config']),
              args['seed'],
              args['output_path'],
              resource_functions_path=os.path.abspath(args['resource_functions']))
    # Execute orchestrated simulation
    algo.run()
    print(f'{run}-{scenario}-{os.path.basename(network)}-{ingress}-{algo_id}')


if __name__ == "__main__":
    main()