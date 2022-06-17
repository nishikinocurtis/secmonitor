#!/usr/bin/python3

from bcc import BPF
import docker
import argparse
import os
import subprocess
import atexit
import logging
import csv
import json
from collections import *
from tester import TestingThread
from analyzer import generate_seccomp

parser = argparse.ArgumentParser(description='A Syscall analyzer for containers')
parser.add_argument('-i', '--image', help="the docker image to run", required=True)
parser.add_argument('-n', '--name', help="the desired container name")
parser.add_argument('-t', '--test', help="specifying the test script, in .py format")
parser.add_argument('-c', '--config', help="launch a container use specified configuration, in .json format")
parser.add_argument('-d', '--display', action='store_true', help="display realtime observation on screen")
parser.add_argument('-l', '--log', help="specifying the log file address")
parser.add_argument('-o', '--output', help="specifying the output statistics file address")
parser.add_argument('-g', '--generate', help="specifying the generating SECCOMP file address")

parser.set_defaults(log="secmon.log")
parser.set_defaults(output="syscalls.json")
parser.set_defaults(test="test_case_1.py")
parser.set_defaults(display=True)
args = parser.parse_args()

logging.basicConfig(filename=args.log, encoding='utf-8', level=logging.INFO)
logging.info(args)

# load BPC C Code
P = open("bpf_raw_tp.c", "r")
prog_text = P.read()
b = BPF(text=prog_text)
P.close()

logging.info("BPF Program loaded.")

# launching container
docker_config = dict()
if args.config:
    C = open(args.config, "r")
    docker_config = json.read(C)
    C.close()

client = docker.from_env()
container = client.containers.run(args.image, remove=True, detach=True, **docker_config)

processes = container.top()
logging.info(processes)
logging.info("Target container is running...")

# launching test thread
test_thread = TestingThread(args.test)
logging.info("Starting test threads...")
test_thread.start()

# prepare BPF perf data processing
syscall_counter = defaultdict(int)
processes_set = set()
cgroup_flag = None
counter = 0

for proc in processes["Processes"]:
    processes_set.add(int(proc[1]))

def consume_perf(cpu, data, size):
    global syscall_counter
    global processes_set
    global cgroup_flag

    global b
    global counter
    event = b["events"].event(data)
    # logging.info("catching " + str(event.pid) + " " + str(event.cgroup_id) + " " + str(event.syscall_id))
    if (not event.pid in processes_set) and (event.cgroup_id != cgroup_flag):
        return
    counter += 1
    if cgroup_flag is None :
        cgroup_flag = event.cgroup_id
    syscall_counter[event.syscall_id] += 1
    if args.display:
        logging.info("{} {} {}".format(event.pid, event.comm, event.syscall_id))


b["events"].open_perf_buffer(consume_perf)
logging.info("PID|COMM|SYSCALL_ID")


@atexit.register
def print_result():
    global counter
    logging.info("Recorded {} events in total.".format(counter))

    syscall_list = []

    for k, v in syscall_counter.items():
        syscall_list.append({"syscall_id": k, "counts": v})

    with open(args.output, 'w') as F:
        json.dump({"syscall_list": syscall_list}, F)

    if args.generate:
        if args.generate == "":
            generate_seccomp(args.output + "_secmonitor.json")
        else:
            generate_seccomp(args.generate)

while True:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        exit()

exit()