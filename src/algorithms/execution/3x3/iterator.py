import sys
import subprocess
import time


def main():
    # cli args: start_run end_run num_parallel poll_pause
    # eg: python iterator.py 50 55 1 5
    start = int(sys.argv[1])
    end = int(sys.argv[2]) + 1
    runs = [str(x) for x in range(start, end)]
    pparallel = int(sys.argv[3])
    poll_pause = int(sys.argv[4])

    scenarios = ['llc']
    # networks = ['../../../../params/networks/bics_34.graphml', '../../../../params/networks/dfn_58.graphml',
    #             '../../../../params/networks/intellifiber_73.graphml']
    # ingress = ['0.1', '0.15', '0.2', '0.25', '0.3', '0.35', '0.4', '0.45', '0.5']
    # algos = ['gpasp', 'spr1', 'spr2']
    # scenarios = ['hc']
    networks = ['../../../../params/networks/dfn_58.graphml']
    # ingress = ['0.1']
    ingress = ['0.1', '0.2', '0.3', '0.4', '0.5']
    algos = ['gpasp', 'spr2', 'bjointsp', 'bjointsp_recalc']
    # algos = ['bjointsp', 'bjointsp_recalc']

    running_processes = []
    for r in runs:
        for s in scenarios:
            for net in networks:
                for ing in ingress:
                    for a in algos:
                        running_processes.append(subprocess.Popen(['python', 'iteration_runner.py', r, s, net, ing, a]))
                        print(f'{r}-{s}-{net}-{ing}-{a}')
                        while len(running_processes) == pparallel:
                            unfinished_processes = []
                            for p in running_processes:
                                if p.poll() is None:
                                    # process has NOT terminated
                                    unfinished_processes.append(p)
                            if len(unfinished_processes) == len(running_processes):
                                time.sleep(poll_pause)
                            else:
                                running_processes = unfinished_processes
    for p in running_processes:
        p.wait()


if __name__ == "__main__":
    main()
