import pdb
import re
import os
import sys
import time
import shutil
import json
import yaml
import logging
from optparse import OptionParser
from utils.utils_misc import *
import ondemand_provision

POSTFIX = time.strftime("%Y%m%d%H%M")
AVOCADO_PATH = os.path.split(os.path.realpath(__file__))[0]
OSDISK_PATH = "{0}/ondemand_osdisk".format(AVOCADO_PATH)
IGNORE_LIST = []
SUBMIT_RESULT = yaml.load(file('%s/config.yaml' % AVOCADO_PATH))["submit_result"]
LOGFILE = "/tmp/run-avocado/run-avocado.log-" + POSTFIX
if not os.path.isdir(os.path.dirname(LOGFILE)):
    os.makedirs(os.path.dirname(LOGFILE))

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s %(levelname)s %(message)s',
                    datefmt='[%Y-%m-%d %H:%M:%S]',
                    filename=LOGFILE,
                    filemode='w')


def config():
    avocado_conf = '/etc/avocado/avocado.conf'
    comp_test = re.compile('^test_dir = .*$')
    comp_data = re.compile('^data_dir = .*$')
    comp_logs = re.compile('^logs_dir = .*$')
    with open(avocado_conf, 'r') as f:
        data = f.readlines()
    new_data = ""
    for line in data:
        if re.findall(comp_test, line):
            line = "test_dir = %s/tests\n" % AVOCADO_PATH
        elif re.findall(comp_data, line):
            line = "data_dir = %s/data\n" % AVOCADO_PATH
        elif re.findall(comp_logs, line):
            line = "logs_dir = %s/job-results\n" % AVOCADO_PATH
        new_data += line
    with open(avocado_conf, 'w') as f:
        f.write(new_data)


class Run(object):
    def __init__(self):
        self.avocado_path = AVOCADO_PATH
        self.job_path = "%s/job-results/latest" % self.avocado_path
        config_file = "%s/config.yaml" % self.avocado_path
        with open(config_file, 'r') as f:
            data=yaml.load(f)
        store_dir = data.get("store_dir", "/home/autotest").rstrip('/')
        self.result_path = "%s/run-results/%s" % (store_dir, POSTFIX)
        if not os.path.exists(self.result_path):
            os.makedirs(self.result_path)
        latest_path = "%s/run-results/latest" % store_dir
        if os.path.exists(latest_path):
            os.remove(latest_path)
        command("ln -s %s %s" % (POSTFIX, latest_path))

    def _get_rerun_list(self):
        logging.info("Rerun case list:")
        with open('%s/results.json' % self.job_path, 'r') as f:
            data = f.read()
        result_dict = json.loads(data)
        rerun_list = []
        for case in result_dict["tests"]:
            if str(case["status"]) == 'FAIL' or \
               str(case["status"]) == 'ERROR':
                case_name = case["test"].split(':')[1]
                if case_name not in IGNORE_LIST:
                    rerun_list.append(case_name)
                    logging.info(case_name)
        return rerun_list

    def mk_rerun_yaml(self, rerun_list):
        test_rerun_str = """\
test:
    !include : common.yaml
    !include : instance_types.yaml
    !include : rerun_cases.yaml
"""
        test_rerun_file = "%s/cfg/test_rerun.yaml" % self.avocado_path
        with open(test_rerun_file, 'w') as f:
            f.write(test_rerun_str)
        rerun_cases_file = "%s/cfg/rerun_cases.yaml" % self.avocado_path
        rerun_cases_str = """\
cases:
""" 
        rerun_cases_str += '\n    '.join(rerun_list)
        logging.info(rerun_cases_str)
        with open(rerun_cases_file, 'w') as f:
            f.write(rerun_cases_str)

    def run(self):
        logging.info("=============== Test run begin ===============")
        cmd1 = "avocado run {0}/tests/*.py --mux-yaml {0}/cfg/test.yaml".format(self.avocado_path)
        logging.info(cmd1)
        ret = command(cmd1, timeout=None, ignore_status=True, debug=True)
        logging.info(ret.stdout)
        run_exitstatus = ret.exit_status
        logging.info("Copy %s to %s" % (self.job_path, self.result_path))
        shutil.copytree(self.job_path, self.result_path)
        # Rerun failed cases
        rerun_list = self._get_rerun_list()
        if rerun_list:
            logging.info("Rerun failed cases")
            self.mk_rerun_yaml(rerun_list)
            ret_rerun = command("avocado run %s/tests/*.py --mux-yaml %s/cfg/test_rerun.yaml" %
                                (self.avocado_path, self.avocado_path),
                                timeout=None, ignore_status=True, debug=True)
            logging.info(ret_rerun.stdout)
            run_exitstatus += ret_rerun.exit_status
            shutil.copytree(self.job_path, "%s/rerun_result" % self.mode_path)
        logging.info("=============== Test run end ===============")
        return run_exitstatus


def provision():
    if TYPE == "onpremise":
        return Run().provision_onpremise()
    elif TYPE == "ondemand":
        return Run().provision_ondemand()


def runtest():
    run = Run()
    return run.run()


def import_result():
    if SUBMIT_RESULT:
        # Parse polarion_config.yaml
        config_file = '%s/cfg/polarion_config.yaml' % AVOCADO_PATH
        if not os.path.exists(config_file):
            logging.error("No config file: %s" % config_file)
            sys.exit(1)
        with open(config_file) as f:
            conf = yaml.load(f.read())
        # Set testrun prefix
        TESTRUN_PREFIX = "Aliyun-{rhel_version}".format(
            tag=tag,
            rhel_version=conf["RHEL_VERSION"].replace('.', '_'))
        logging.info("Testrun prefix: {0}".format(TESTRUN_PREFIX))
        xunit_project = "rhel{0}".format(str(conf["PROJECT"]).split('.')[0])
        # Get results path
        result_path = conf["RESULT_PATH"]
        # Main process
        logging.info("=============== Import result to polarion ===============")
        ret += command("/usr/bin/python {0}/xen-ci/utils/import_XunitResult2Polarion.py -f {1}/results.xml -d {0}/xen-ci/database/testcases.db -t aliyun -p {2} -r \"{3}\" -o {1}/xUnit.xml -k {4} -v".format(AVOCADO_PATH, result_path, xunit_project, TESTRUN_PREFIX, CIUSER_PASSWORD), timeout=36000, debug=True, stdout=True).exit_status
#        ret = command("/usr/bin/python %s/tools/import_JunitResult2Polarion.py" % AVOCADO_PATH, debug=True).exit_status
#        ret += command("curl -k -u {0}_machine:polarion -X POST -F file=@{1}/xUnit.xml https://polarion.engineering.redhat.com/polarion/import/xunit".format(xunit_project, result_path), debug=True, stdout=True).exit_status
        logging.info("Import result successful")
        return ret
    else:
        logging.info("Do not submit result to polarion.")
        return 0


def teardown():
    logging.info("=============== Teardown ===============")
    ret = command("avocado run {0}/tests/01_img_prep.py: --mux-yaml {0}/cfg/provision.yaml".format(AVOCADO_PATH))
    logging.info("Teardown finished.")
    return ret


def _get_osdisk(osdisk_path=OSDISK_PATH):
    if not options.osdisk:
        if os.path.isfile(osdisk_path):
            with open(osdisk_path, 'r') as f:
                osdisk = f.read().strip("\n")
            if ".vhd" not in osdisk:
                logging.error("osdisk format is wrong.")
                sys.exit(1)
        else:
            logging.error("No osdisk")
            sys.exit(1)
    else:
        osdisk = options.osdisk
    return osdisk


def main():
    # modify /etc/avocado/avocado.conf
    config()
    # Run main process
    if os.path.isfile(OSDISK_PATH):
        os.remove(OSDISK_PATH)
    if RUN_ONLY:
        logging.info("Run test only")
        osdisk = _get_osdisk()
        command("/usr/bin/python {0}/create_conf.py --run-only"
                .format(AVOCADO_PATH), debug=True)
        sys.exit(runtest() or teardown())
    elif IMPORT_ONLY:
        logging.info("Import result only")
        command("/usr/bin/python {0}/create_conf.py --import-only"
                .format(AVOCADO_PATH), debug=True)
        sys.exit(import_result())
    else:
        command("/usr/bin/python {0}/create_conf.py"
                .format(AVOCADO_PATH), debug=True)
        ret += runtest()
        ret += import_result()
        ret += teardown()
        sys.exit(ret)


if __name__ == "__main__":
    usage = "usage: %prog [options] [-m <mode>]"
    parser = OptionParser(usage)
    parser.add_option('-r', '--run-only', dest='run_only', default=False, action='store_true',
                      help='Only run test cases. Do not provision.')
    parser.add_option('-i', '--import-only', dest='import_only', default=False, action='store_true',
                      help='Only import the latest result to polarion. Do not run tests.')
    parser.add_option('-k', '--ci-user-password', dest='ci_user_password', action='store',
                      help='The ci-user password.', metavar='CIUSER_PASSWORD')

    options, args = parser.parse_args()
    RUN_ONLY = options.run_only
    IMPORT_ONLY = options.import_only
    CIUSER_PASSWORD = options.ci_user_password

    main()
