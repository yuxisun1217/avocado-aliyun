#!/usr/bin/python
import subprocess
import os
import yaml

testsuite = "function"

REALPATH = os.path.split(os.path.realpath(__file__))[0]

with open("{0}/cfg/cases_{1}.yaml".format(REALPATH, testsuite), 'r') as f:
    case_list_str = yaml.load(f).get("cases")
cmd = "/usr/bin/avocado run {0}/tests/{1} --mux-yaml {2}/cfg/test.yaml".format(REALPATH, case_list_str, REALPATH)
print(cmd)
p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
while p.poll() is None:
    line = p.stdout.readline()
    line = line.strip()
    if line:
        print(line)
if p.returncode == 0:
    print("Run Success")
else:
    print("Run Failed")
