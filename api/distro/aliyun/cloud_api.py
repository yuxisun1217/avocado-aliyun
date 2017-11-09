import abc
import logging
import time

from api.distro.aliyun import sdk as sdk
from api.guest import GuestUtils
from utils.globalvars import GlobalVars as g


class Base(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, params):
        self.params = params
        self.status = -1

    @abc.abstractproperty
    def name(self):
        return self.params.get("Name")

    @property
    def id(self):
        return self.params.get("Id")

    @abc.abstractmethod
    def show(self):
        pass

    def list(self):
        pass

    def create(self, params):
        pass

    def delete(self):
        pass

    def update(self, params=None):
        pass

    def exists(self):
        if self.status == -1:
            return False
        else:
            return True

    def _get_status(self, params):
        if params.get("TotalCount") > 0:
            self.status = 0
        else:
            self.status = -1

    def wait_for_status(self, status, times=g.WAIT_FOR_RETRY_TIMES, interval=g.RETRY_INTERVAL):
        """
        Wait for vm status is <status>
        :param status: The target VM status: created/running/stopped/deleted
        :param times: Retry times
        :param interval: Retry interval
        :return: raise VMStatusError if status is wrong after retry
        """
        logging.debug("Waiting for VM {0}...".format(status))
        for retry in xrange(0, times):
            self.show()
            if status == "created":
                ret = self.exists()
            elif status == "deleted":
                ret = not self.exists()
            else:
                raise Exception("{0} status {1} is wrong.".format(self.__class__.__name__, status))
            if ret:
                logging.debug("{0} is {1}".format(self.__class__.__name__, status))
                return
            logging.debug("Retry times: {0}/{1}.".format(retry+1, times))
            time.sleep(interval)
        else:
            raise ValueError("After retry {0} times, {1} is not {2}".format(times, self.__class__.__name__, status))

    def wait_for_created(self):
        """
        Wait for vm exists
        """
        self.wait_for_status(status="created")

    def wait_for_deleted(self):
        """
        Wait for vm exists
        """
        self.wait_for_status(status="deleted")


class VM(Base, GuestUtils):
    def __init__(self, params):
        """
        self.vm_status:
           -1: VM doesn't exist
           0:  VM is running
           1:  VM is starting
           2:  VM is stopped
        """
#        super(VM, self).__init__(params)
        Base.__init__(self, params)
        GuestUtils.__init__(self, params)

    @property
    def name(self):
        return self.params.get("InstanceName")

    @property
    def id(self):
        return self.params.get("InstanceId")

    def list(self, params=None):
        """
        This show the vm list
        """
        logging.info("List VMs")
        return sdk.describe_instances(params)

    def create(self, params):
        """
        This helps to create a VM
        """
        logging.info("Create VM")
        params.setdefault("InstanceChargeType", "PostPaid")
        params.setdefault("InternetChargeType", "PayByTraffic")
        params.setdefault("SystemDiskCategory", "cloud_efficiency")
        params.setdefault("InternetMaxBandwidthIn", "5")
        params.setdefault("InternetMaxBandwidthOut", "5")
        response = sdk.create_instance(params)
        time.sleep(10)
        return response

    def start(self):
        """
        This helps to start a VM
        """
        logging.info("Start VM")
        params = {}
        params.setdefault("InstanceId", self.id)
        return sdk.start_instance(params)

    def stop(self, force=False):
        """
        This helps to stop a VM
        """
        logging.info("Stop VM")
        params = {}
        params.setdefault("InstanceId", self.id)
        if force:
            params.setdefault("ForceStop", "True")
        return sdk.stop_instance(params)

    def restart(self, force=False):
        """
        This helps to restart a VM
        """
        logging.info("Restart VM")
        params = {}
        params.setdefault("InstanceId", self.id)
        if force:
            params.setdefault("ForceStop", "True")
        return sdk.reboot_instance(params)

    def delete(self):
        """
        This helps to delete a VM
        The VM can be deleted only if the status is stopped(sdk/cli only)
        """
        logging.info("Delete VM")
        params = {}
        params.setdefault("InstanceId", self.id)
        if not self.is_stopped():
            self.stop()
            self.wait_for_stopped()
        return sdk.delete_instance(params)

    def show(self):
        logging.info("Show VM params")
        params = {}
        params.setdefault("InstanceName", self.name)
        params.setdefault("RegionId", self.params.get("RegionId"))
        show_params = sdk.describe_instances(params)
        self._get_status(show_params)
        if self.exists():
            self.params = show_params["Instances"]["Instance"][0]
        #        print "---------Show VM Params-----------"
        #        print self.params

    def wait_for_status(self, status, times=g.WAIT_FOR_RETRY_TIMES, interval=g.RETRY_INTERVAL):
        """
        Wait for vm status is <status>
        :param status: The target VM status: created/running/stopped/deleted
        :param times: Retry times
        :param interval: Retry interval
        :return: raise VMStatusError if status is wrong after retry
        """
        logging.debug("Waiting for VM {0}...".format(status))
        for retry in xrange(0, times):
            self.show()
            if status == "created":
                ret = self.exists()
            elif status == "running":
                ret = self.is_running()
            elif status == "stopped":
                ret = self.is_stopped()
            elif status == "deleted":
                ret = not self.exists()
            else:
                raise Exception("VM status {0} is wrong.".format(status))
            if ret:
                logging.debug("VM is {0}".format(status))
                return
            logging.debug("Retry times: {0}/{1}.".format(retry+1, times))
            time.sleep(interval)
        else:
            raise ValueError("After retry {0} times, VM is not {1}".format(times, status))

    def wait_for_created(self):
        """
        Wait for vm exists
        """
        self.wait_for_status(status="created")

    def wait_for_running(self):
        """
        Wait for the VM status is running
        """
        self.wait_for_status(status="running", interval=g.VM_START_RETRY_INTERVAL)

    def wait_for_stopped(self):
        """
        Wait for the VM status is stopped
        """
        self.wait_for_status(status="stopped")

    def wait_for_deleted(self):
        """
        Wait for the VM status is stopped
        """
        self.wait_for_status(status="deleted")

    def is_running(self):
        """
        Return True if VM is running.
        """
        if self.status == 0:
            return True
        else:
            return False

    def is_stopped(self):
        """
        Return True if VM is stopped.
        """
        if self.status == 2:
            return True
        else:
            return False

    def _get_status(self, params):
        """
        Get VM status from self.params, set self.vm_status

        :self.vm_status:
        -1: VM doesn't exist
        0:  VM is running
        1:  VM is starting
        2:  VM is stopped
        """
        if params.get("TotalCount") == 0:
            logging.info("VM doesn't exist.")
            self.status = -1
        else:
            status = params["Instances"]["Instance"][0].get("Status")
            logging.info("VM status: %s", status)
            if status == "Stopped":
                self.status = 2
            elif status == "Running":
                self.status = 0
            else:
                self.status = 1
#        logging.info("VM status code: %d", self.status)

    def allocate_public_address(self):
        """
        Allocate public ip address for the instance
        """
        ret = sdk.allocate_public_ip_address(self.params)
        time.sleep(5)
        return ret

    def get_public_address(self):
        """
        Get VM public ip address
        :return: public ip if have. Else, return None
        """
        public_ip_list = self.params["PublicIpAddress"]["IpAddress"]
        if public_ip_list:
            return public_ip_list[0]
        else:
            return None

    def modify_instance_type(self, new_type):
        """
        Modify Instance Type
        """
        params = {}
        params.setdefault("InstanceId", self.id)
        params.setdefault("InstanceType", new_type)
        return sdk.modify_instance_spec(params)


class Image(Base):
    def __init__(self, params):
        super(Image, self).__init__(params)

    @property
    def name(self):
        return self.params.get("ImageName")

    @property
    def id(self):
        if self.exists():
            return self.params.get("ImageId")
        else:
            return None

    def list(self, params=None):
        logging.info("List Images")
        return sdk.describe_images(params)

    def show(self):
        logging.info("Show Image params")
        params = sdk.describe_images(self.params)
        self._get_status(params)
        if self.exists():
            self.params = params["Images"]["Image"][0]
#        print "======= Image Params ======="
#        print self.params

    def create(self, params):
        sdk.create_image(params)
        return self.wait_for_created()


class KeyPair(Base):
    def __init__(self, params):
        super(KeyPair, self).__init__(params)

    @property
    def name(self):
        return self.params.get("KeyPairName")

    @property
    def fingerprint(self):
        return self.params.get("KeyPairFingerPrint")

    def show(self):
        params = {}
        params.setdefault("KeyPairName", self.name)
        show_params = sdk.describe_keypairs(params)
        self._get_status(show_params)
        if self.exists():
            self.params = show_params["KeyPairs"]["KeyPair"][0]

    def create(self, params):
        sdk.import_keypair(params)
        return self.wait_for_created()

    def delete(self):
        params = {"KeyPairNames", self.name}
        sdk.delete_keypair(params)
        return self.wait_for_deleted()


class SecurityGroup(Base):
    def __init__(self, params):
        super(SecurityGroup, self).__init__(params)

    @property
    def name(self):
        return self.params.get("SecurityGroupName")

    @property
    def id(self):
        if self.exists():
            return self.params.get("SecurityGroupId")
        else:
            return None

    def show(self):
        pass


class VSwitch(Base):
    def __init__(self, params):
        super(VSwitch, self).__init__(params)

    @property
    def name(self):
        return self.params.get("VSwitchName")

    @property
    def id(self):
        return self.params.get("VSwitchId")

    def show(self):
        pass