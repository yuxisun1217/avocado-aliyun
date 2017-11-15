import os
import sys
import yaml
import logging
from optparse import OptionParser

REALPATH = os.path.split(os.path.realpath(__file__))[0]
ROOT_PATH = os.path.dirname(REALPATH)

config_yaml = "%s/config.yaml" % ROOT_PATH
password_yaml = "%s/cfg/password.yaml" % ROOT_PATH
common_yaml = "%s/cfg/common.yaml" % ROOT_PATH
polarion_yaml = "%s/cfg/polarion_config.yaml" % ROOT_PATH

AliyunSub = """\
    aliyun_access_key_id: %(aliyun_access_key_id)s
    aliyun_access_key_secret: %(aliyun_access_key_secret)s\
"""

CommonYaml = """\
Common:
    Distro: %(distro)s
    Project: %(project)s
CloudSub:
%(cloud_sub)s
RedhatSub:
    username: %(redhat_username)s
    password: %(redhat_password)s
VMUser:
    username: %(vm_username)s
    password: %(vm_password)s
    keypairname: %(keypairname)s
Region:
    id: %(region_id)s
Zone:
    id: %(zone_id)s
OSDisk:
    name: %(osdisk_name)s
    local_path: %(osdisk_local_path)s
VM:
    name: %(vm_name_prefix)s
    instance_type: %(vm_size)s
Image:
    name: %(image_name)s
    id: %(image_id)s
Network:
    VPC:
        name: %(vpc_name)s
        id: %(vpc_id)s
        cidr: 172.17.0.0/16
    VSwitch:
        name: %(vswitch_name)s
        id: %(vswitch_id)s
        cidr: 172.17.224.0/20
SecurityGroup:
    name: %(security_group_name)s
    id: %(security_group_id)s
DataDisk:
    disk_number: 3
    disk1:
        size: 50
        host_caching: None
    disk2:
        size: 1023
        host_caching: ReadOnly
    disk3:
        size: 1023
        host_caching: ReadWrite
"""

TestYaml = """\
test:
    !include : common.yaml
    !include : instance_types_%(region)s.yaml
    !include : cases_%(case_group)s.yaml
"""

PolarionYaml = """\
PROJECT: %(project)s
RHEL_VERSION: %(rhel_version)s
TYPE: %(case_group)s
RESULT_PATH: %(result_path)s
TAG: %(tag)s
"""


def _write_file_content(filename, content):
    with open(filename, 'w') as f:
        f.write(content)


class Distro(object):
    def __init__(self):
        """
        The distro structure
        """
        self.size = None
        self.sub = None
        self.params = None


class CreateConfFiles(object):
    def __init__(self, data, account_data):
        """
        :param data: Parameters dictionary. Parse the config.yaml
        :param account_data: Account parameters dictionary. Parse the password.yaml
        """
        self.data = data
        self.account_data = account_data
        self.distro = data.get("distro")
        self.rhel_version = None

    def create_common_yaml(self):
        """
        Create common.yaml
        """
        # Set distro specified parameters
        cloud = Distro()
        if self.distro == "aliyun":
            cloud.size = "ecs.sn1.medium"
            aliyun_sub_params = {
                "aliyun_access_key_id": self.account_data.get("AliyunSub").get("aliyun_access_key_id"),
                "aliyun_access_key_secret": self.account_data.get("AliyunSub").get("aliyun_access_key_secret")
            }
            cloud.sub = AliyunSub % aliyun_sub_params
            cloud.params = {"keypairname": "wshi",
                            "vm_username": "root",
                            "vm_name_prefix": "aliauto"}
        else:
            logging.error("No such distro: {0}".format(self.distro))
            sys.exit(1)
        # Set common param dict
        common_yaml_dict = {
            "distro": self.distro,
            "project": self.data.get("project"),
            "cloud_sub": cloud.sub,
            "redhat_username": self.account_data.get("RedhatSub").get("username"),
            "redhat_password": self.account_data.get("RedhatSub").get("password"),
            "vm_username": self.account_data.get("VMUser").get("username", ""),
            "vm_password": self.account_data.get("VMUser").get("password", ""),
            "region_id": self.data.get("Region").get("id"),
            "zone_id": self.data.get("Zone").get("id"),
            "osdisk_name": self.data.get("OSDisk", {}).get("name", ""),
            "osdisk_local_path": self.data.get("OSDisk", {}).get("local_path", "/home/autotest/osdisk/{0}".format(self.distro)),
            "vm_size": cloud.size,
            "image_name": self.data.get("Image").get("name", ""),
            "image_id": self.data.get("Image").get("id", ""),
            "vpc_name": self.data.get("VPC").get("name", ""),
            "vpc_id": self.data.get("VPC").get("id", ""),
            "vswitch_name": self.data.get("VSwitch").get("name", ""),
            "vswitch_id": self.data.get("VSwitch").get("id", ""),
            "security_group_name": self.data.get("SecurityGroup").get("name", ""),
            "security_group_id": self.data.get("SecurityGroup").get("id", "")
        }
        # Merge cloud.params into common param dict
        common_yaml_dict.update(cloud.params)
        # Wrote to file
        _write_file_content(common_yaml,
                            CommonYaml % common_yaml_dict)
        return 0

    def create_test_yaml(self):
        """
        Create test_asm.yaml or test_arm.yaml
        """
        test_yaml = "{0}/cfg/test.yaml".format(ROOT_PATH)
        test_yaml_dict = {
            "case_group": self.data.get("case_group", "function"),
            "region": self.data.get("Region").get("id", "us-west-1").replace('-', '')
        }
        _write_file_content(test_yaml,
                            TestYaml % test_yaml_dict)
        return 0

    def create_polarion_config_yaml(self):
        """
        Create polarion_config.yaml
        """
        polarion_yaml_dict = {
            "project": self.data.get("project"),
            "rhel_version": self.data.get("rhel_version"),
            "case_group": self.data.get("case_group"),
            "result_path": "{0}run-results/{1}/latest".format(self.data.get("store_dir", "/home/autotest/"), self.distro),
            "tag": self.data.get("tag")
        }
        _write_file_content(polarion_yaml,
                            PolarionYaml % polarion_yaml_dict)
        return 0


if __name__ == "__main__":
    usage = "usage: %prog [-o <osdisk>]"
    parser = OptionParser(usage)
#    parser.add_option('-t', '--type', dest='type', action='store',
#                      help='The type of the test. Default value is onpremise. '
#                           '(onpremise/ondemand/customize)', metavar='TYPE')
#    parser.add_option('-o', '--osdisk', dest='osdisk', action='store',
#                      help='The VHD OS disk name(e.g.RHEL-7.3-20161019.0-wala-2.2.0-2.vhd)', metavar='OSDISK.vhd')
    parser.add_option('-p', '--provision-only', dest='provision_only', default=False, action='store_true',
                      help='Only run provision. Do not run test cases.')
    parser.add_option('-r', '--run-only', dest='run_only', default=False, action='store_true',
                      help='Only run test cases. Do not provision.')
    parser.add_option('-i', '--import-only', dest='import_only', default=False, action='store_true',
                      help='Only import the latest result to polarion. Do not run tests.')

    options, args = parser.parse_args()

    with open(config_yaml, 'r') as f:
        data = yaml.load(f)
    with open(password_yaml, 'r') as f:
        account_data = yaml.load(f)
#    type = options.type
#    if not type:
#        type = data.get("type", None)
#        if not type:
#            parser.print_help()
#            parser.error("The type must be specified.")
    createFile = CreateConfFiles(data, account_data)
    ret = 0
    if options.provision_only:
        pass
    elif options.run_only:
        ret += createFile.create_common_yaml()
        ret += createFile.create_test_yaml()
    elif options.import_only:
        ret += createFile.create_polarion_config_yaml()
    else:
        ret += createFile.create_common_yaml()
        ret += createFile.create_test_yaml()
        ret += createFile.create_polarion_config_yaml()
    sys.exit(ret)
