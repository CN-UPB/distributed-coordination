Copy of https://github.com/ldklenner/coordination-simulation-ba-adapted/tree/adapted

# Simulation: Coordination of chained virtual network functions

Simulate flow-level, inter-node network coordination including scaling and placement of services and routing flows between them. Note: this repository holds an altered version of the original simulator [coord-sim](https://github.com/RealVNF/coordination-simulation), adapted to my needs in order to accomplish my bachelor thesis.


**Additional features**:

* Forwarding capabilities. Prior to this, forwarding happened implicit. Now flows are explicit forwarded over link, taking into account individual link utilization
* Individual flow forwarding rules. A node can make a forwarding decision on individual flows.
* Individual flow processing rules. A node can explicit decide if it will process a flow.
* Extended simulator state and action interface.
* Algorithm callback interface. To allow a external algorithm to capture certain event, it can register callback functions invoked by the flowsimulator.
	* init_flow callback
	* pass_flow callback
	* periodic measurement callbacks.
* Adapted metrics.
* Egress node routing.
* Extended simulator configuration


## Setup

Requires Python 3.6. Install with [virtualenv](https://virtualenv.pypa.io/en/stable/) to not break original coord-sim installation. Make sure to install simulator with adapted source files, located on the default `adapted` branch:
```bash
git checkout adapted
```

Then follow original setup procedure:
```bash
pip install -r requirements.txt
```

For evaluation, also install these dependencies:

```
pip install -r eval_requirements.txt
```

Due to the use of deprecated networkx functions and their removal in the 2.4 version, released while developing, the networkx library is locked to version 2.3

## Usage

* All relevant scripts for running experiments are in `src/algorithms/execution`
* The folders `time` and `3x3` are for different experiments but contain similar scripts. Choose either one or create a new one.
* Create configurtion files by running `config_creator.py`. The generated configurations specify percentage of ignress nodes, capacities, etc.
* Adjust the network, algorithms, ingress in `iterator.py`
* Then call `python iterator.py start_run end_run num_parallel poll_pause` to run experiments.
* For example `python iterator.py 50 55 4 5` will run 6 repetitions (ID 50-55) on 4 cores, polling every 5s if a core is free.
* The results are saved in the subfolder `scenarios` according to run ID, config, algorithm, etc.

## Evaluation of Results

* To evaluate the results, aggregate and plot them.
* To aggregate, run `aggregator.py`
* Then plot with `plotter.py`. Or easier (for me) with a Jupyter notebook such as `time/eval.ipynb`
