import argparse
import simpy
import random
import numpy
from coordsim.simulation.flowsimulator import FlowSimulator
from coordsim.reader import reader
from coordsim.metrics import metrics
from coordsim.simulation.simulatorparams import SimulatorParams
import coordsim.network.dummy_data as dummy_data
import logging
import time


log = logging.getLogger(__name__)


def main():
    args = parse_args()
    metrics.reset()
    start_time = time.time()
    logging.basicConfig(level=logging.INFO)

    # Create a SimPy environment
    env = simpy.Environment()

    # Seed the random generator
    random.seed(args.seed)
    numpy.random.seed(args.seed)

    # Parse network and get NetworkX object and ingress network list
    network, ing_nodes = reader.read_network(args.network, node_cap=10, link_cap=10)

    # Getting current SFC list, and the SF list of each SFC, and config
    sfc_list = reader.get_sfc(args.sf)
    sf_list = reader.get_sf(args.sf, args.sfr)
    config = reader.get_config(args.config)

    # use dummy placement and schedule for running simulator without algorithm
    # TODO: make configurable via CLI
    sf_placement = dummy_data.triangle_placement
    schedule = dummy_data.triangle_schedule

    # Create the simulator parameters object with the provided args
    params = SimulatorParams(network, ing_nodes, sfc_list, sf_list, config, args.seed, sf_placement=sf_placement,
                             schedule=schedule)
    log.info(params)

    # Create a FlowSimulator object, pass the SimPy environment and params objects
    simulator = FlowSimulator(env, params)

    # Start the simulation
    simulator.start()

    # Run the simpy environment for the specified duration
    env.run(until=args.duration)

    # Record endtime and running_time metrics
    end_time = time.time()
    metrics.running_time(start_time, end_time)


# parse CLI args (when using simulator as stand-alone, not triggered through the interface)
def parse_args():
    parser = argparse.ArgumentParser(description="Coordination-Simulation tool")
    parser.add_argument('-d', '--duration', required=True, dest="duration", type=int,
                        help="The duration of the simulation (simulates milliseconds).")
    parser.add_argument('-sf', '--sf', required=True, dest="sf",
                        help="VNF file which contains the SFCs and their respective SFs and their properties.")
    parser.add_argument('-sfr', '--sfr', required=False, default='', dest='sfr',
                        help="Path which contains the SF resource consumption functions.")
    parser.add_argument('-n', '--network', required=True, dest='network',
                        help="The GraphML network file that specifies the nodes and edges of the network.")
    parser.add_argument('-c', '--config', required=True, dest='config', help="Path to the simulator config file.")
    parser.add_argument('-s', '--seed', required=False, default=random.randint(0, 9999), dest='seed', type=int,
                        help="Random seed")
    return parser.parse_args()


if __name__ == '__main__':
    main()
