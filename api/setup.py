import logging
import sys
import os
import time
#REALPATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(sys.path[0], ".."))
from utils import utils_misc
from distro.aliyun import cloud_api as aliyun_api
from distro.aliyun import config as aliyun_config
from distro import aliyun
from avocado.core.exceptions import TestSkipError


class Setup(object):
    def __init__(self, params):
        self.params = params
        self.vm_params = {}
        self.disk_params = {}
        self.disk_list = []
        self.vm_test01 = None
        self.disk_test01 = None
        self.distro = self.params.get('Distro', '*/Common/*')
        self.project = self.params.get('Project', '*/Common/*')
        self.redhat_username = self.params.get('username', '*/RedhatSub/*')
        self.redhat_password = self.params.get('password', '*/RedhatSub/*')
        if self.distro == "aliyun":
            self.vm = aliyun_api
        self._prepare()

    def _prepare(self, **kwargs):
        # Prepare the vm parameters
        if self.distro == "aliyun":
            aliyun_access_key_id = self.params.get('aliyun_access_key_id', '*/CloudSub/*')
            aliyun_access_key_secret = self.params.get('aliyun_access_key_secret', '*/CloudSub/*')
            region = self.params.get('id', "*/Region/*")
            prepare_params = {"aliyun_access_key_id": aliyun_access_key_id,
                              "aliyun_access_key_secret": aliyun_access_key_secret,
                              "region": region}
            self._config_aliyun(prepare_params)
            self._get_vm_params_aliyun(**kwargs)
        else:
            raise ValueError("No such distro: {0}".format(self.distro))

    def _get_vm_params_aliyun(self, **kwargs):
        self.vm_params["InstanceType"] = self.params.get('instance_type', '*/VM/*')
        self.vm_params["region"] = self.params.get('id', "*/Region/*")
        vmname_tag = kwargs.get("vmname_tag", "").replace("_", "")
        self.vm_params["InstanceName"] = self.params.get('name', '*/VM/*') + \
                                         str(self.project).replace('.', '') + \
                                         self.vm_params["InstanceType"][4:].lower().replace(".", "") + \
                                         vmname_tag
        self.vm_params["HostName"] = self.vm_params["InstanceName"]
        self.vm_params["username"] = self.params.get('username', '*/VMUser/*')
        self.vm_params["Password"] = self.params.get('password', '*/VMUser/*')
        self.vm_params["KeyPairName"] = self.params.get('keypairname', '*/VMUser/*')
        self._check_key_pair()
        self.vm_params["ZoneId"] = self.params.get('id', '*/Zone/*')
        self.vm_params["ImageId"] = self.params.get('id', '*/Image/*')
        if self.vm_params["ImageId"] is None:
            self.vm_params["ImageName"] = self.params.get('name', '*/Image/*')
            image_params = {"ImageName": self.vm_params["ImageName"]}
            image = self.vm.Image(image_params)
            image.show()
            self.vm_params["ImageId"] = image.id
        self.vm_params["SecurityGroupId"] = self.params.get('id', '*/SecurityGroup/*')
        if self.vm_params["SecurityGroupId"] is None:
            self.vm_params["SecurityGroupName"] = self.params.get('name', '*/SecurityGroup/*')
            security_group_params = {"SecurityGroupName": self.vm_params["SecurityGroupName"]}
            security_group = self.vm.SecurityGroup(security_group_params)
            security_group.show()
            self.vm_params["SecurityGroupId"] = security_group.id
        self.vm_params["VSwitchId"] = self.params.get('id', '*/Network/VSwitch/*')
        if self.vm_params["VSwitchId"] is None:
            self.vm_params["VSwitchName"] = self.params.get('name', '*/Network/VSwitch/*')
            vswitch_params = {"VSwitchName": self.vm_params["VSwitchName"]}
            vswitch = self.vm.VSwitch(vswitch_params)
            vswitch.show()
            self.vm_params["VSwitchId"] = vswitch.id
        for param in kwargs:
            if param in self.vm_params:
                self.vm_params[param] = kwargs.get(param)
        logging.info(str(self.vm_params))
        self.vm_test01 = self.vm.VM(self.vm_params)

    def _check_key_pair(self):
        key_pair_params = {"KeyPairName": self.vm_params["KeyPairName"]}
        key_pair = self.vm.KeyPair(key_pair_params)
        key_pair.show()
        if key_pair.exists():
            ssh_key = utils_misc.get_ssh_key()
            if not ssh_key.get("fingerprint") == key_pair.fingerprint:
                logging.info("KeyPair fingerprint is not match. Remove old KeyPair")
                key_pair.delete()
        if not key_pair.exists():
            ssh_key = utils_misc.get_ssh_key()
            key_pair_params.setdefault("PublicKeyBody", ssh_key.get("content"))
            key_pair.create(key_pair_params)

    def _config_aliyun(self, params):
        access_key_id = params.get('aliyun_access_key_id')
        access_key_secret = params.get('aliyun_access_key_secret')
        region = params.get('region')
        c = aliyun_config.UpdateConfig(access_key_id, access_key_secret, region)
        c.update()

    def vm_prepare(self, args=None):
        # If vm doesn't exist, create it. If it exists, start it.
        if args is None:
            args = []
        logging.info("args: {0}".format(str(args)))
        logging.info("Prepare the VM %s", self.vm_params["InstanceName"])
        self.vm_test01.show()
        # If need pre-deleted VM, delete it and return
        if "pre-delete" in args:
            logging.info("Pre delete VM")
            if self.vm_test01.exists():
                self.vm_test01.delete()
                self.vm_test01.wait_for_deleted()
            return True
        # If not exists, create VM
        if not self.vm_test01.exists():
            self.vm_test01.create(self.vm_params)
            self.vm_test01.wait_for_created()
        if not self.vm_test01.get_public_address():
            self.vm_test01.allocate_public_address()
        # If need pre-stopped VM, stop it and return.
        if "pre-stop" in args:
            logging.info("Pre stop VM")
            if not self.vm_test01.is_stopped():
                self.vm_test01.stop(force=True)
                self.vm_test01.wait_for_stopped()
            return True
        # If need running VM, start it
        if not self.vm_test01.is_running():
            self.vm_test01.start()
            time.sleep(30)
            self.vm_test01.wait_for_running()
        # If don't need to verify alive, return True.
        if "no-login" in args:
            logging.info("Skip verifying alive.")
            return True
        # Set authentication method. Default is publickey.
        if "password" in args:
            authentication = "password"
        else:
            authentication = "publickey"
        if not self.vm_test01.wait_for_login(authentication=authentication):
            raise Exception("VM %s is not available. Exit." % self.vm_params["InstanceName"])
        logging.info("Setup successfully.")
        return True

    def disk_prepare(self, disk_count=1):
        output = self.vm_test01.describe_disks(self.vm_params)
        if output.get("TotalCount") < disk_count:
            i = 0
            while i < (disk_count - output.get("TotalCount")):
                self.vm_test01.create_disk(self.vm_params)
                i = i + 1
        output = self.vm_test01.describe_disks(self.vm_params)
        disk_ids = list(disk['DiskId'] for disk in output.get("Disks").get("Disk"))
        self.vm_params["AttachDiskIds"] = disk_ids

    def selected_case(self, case):
        case_name = case.name.split(':')[-1]
        if case_name not in self.params.get('cases', '*/test/*'):
            raise TestSkipError
