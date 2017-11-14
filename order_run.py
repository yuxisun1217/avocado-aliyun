#!/usr/bin/python
from utils.utils_misc import *
import os
import yaml

testsuite = "function"

REALPATH = os.path.split(os.path.realpath(__file__))[0]

with open("{0}/cfg/cases_{1}.yaml".format(REALPATH, testsuite), 'r') as f:
    case_list_str = yaml.load(f).get("cases")
cmd = "/usr/bin/avocado run {0}/tests/{1} --mux-yaml {2}/cfg/test.yaml".format(REALPATH, case_list_str, REALPATH)
print(cmd)
command(cmd)
