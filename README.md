# Fully Distributed Service Coordination

Two fully distributed algorithms for online service coordination. 
All nodes runs the algorithm individually and in parallel to decide how to scale and where to place
service components as well as how to route incoming flows through the placed instances.

This fully distributed approach reaches similar solution quality as centralized approaches
but is more robust, requires less global knowledge, and is magnitudes faster.

This repository contains prototype implementations of both algorithms,
extends [`coord-sim`](https://github.com/RealVNF/coord-sim) for simulation, and contains extensive evaluation results.

## Citation

If you use this code, please cite our [paper](http://dl.ifip.org/db/conf/cnsm/cnsm2020/1570653213.pdf):

```
@inproceedings{schneider2020distributed,
	title={Every Node for Itself: Fully Distributed Service Coordination},
	author={Schneider, Stefan and Klenner, Lars Dietrich and Karl, Holger},
	booktitle={International Conference on Network and Service Management (CNSM)},
	year={2020},
	publisher={IFIP/IEEE}
}
```


## Setup

Requires Python 3.6+. All dependencies can be installed with: 

```bash
python setup.py install
```

For evaluation, also install these dependencies:

```
pip install -r eval_requirements.txt
```

## Usage

* All relevant scripts for running experiments are in `src/algorithms/execution`
* The folders `time` and `3x3` are for different experiments but contain similar scripts. Choose either one or create a new one.
* Create configurtion files by running `config_creator.py`. The generated configurations specify percentage of ignress nodes, capacities, etc.
* Adjust the network, algorithms, ingress in `iterator.py`
* Then call `python iterator.py start_run end_run num_parallel poll_pause` to run experiments.
* For example `python iterator.py 50 55 4 5` will run 6 repetitions (ID 50-55) on 4 cores, polling every 5s if a core is free.
* The results are saved in the subfolder `scenarios` according to run ID, config, algorithm, etc.
* *Attention:* `python iterator.py` silently overwrites existing results!

## Evaluation of Results

* To evaluate the results, aggregate and plot them.
* To aggregate, run `aggregator.py`. You can adjust settings in `settings.py`. 
* In case of 3x3, also specify the runs to aggregate, eg, `python aggregator.py 0 49`.
* Then plot with `plotter.py`. Or easier using/extending the available Jupyter notebooks under `execution`:
`3x3/eval.ipynb`, `3x3/eval_decisions.ipynb`, `time/eval.ipynb`.
* These notebooks use and plot the available evaluation results, which are stored in the `scenarios` and `transformed` folders. 



## Simulation

For simulation, the [`coord-sim`](https://github.com/RealVNF/coord-sim) simulator was extended as follows:

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


## Contributors

* Main development: [@ldklenner](https://github.com/ldklenner)
* Advisor: [@stefanbschneider](https://github.com/stefanbschneider)

Please use GitHub's issue system to file bugs or ask questions.
