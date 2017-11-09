import time
import sys
import os
import re

from avocado import Test

REALPATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(os.path.dirname(REALPATH)))

from api.setup import Setup


class GeneralTest(Test):

    def setUp(self):
        prep = Setup(self.params)
        prep.selected_case(self.name)
        self.project = prep.project
        self.vm_test01 = prep.vm_test01
        self.vm_params = prep.vm_params
        if "validation" in self.name.name:
            return
        args = []
        if "create_ecs" in self.name.name:
            args.append("pre-delete")
        if "start_ecs" in self.name.name:
            args.append("pre-stop")
        prep.vm_prepare(args)

    def test_verify_package_signed(self):
        self.log.info("Verify all packages are signed")
        cmd = "rpm -qa --qf '%{name}-%{version}-%{release}.%{arch} (%{SIGPGP:pgpsig})\\n'|grep -v 'Key ID'"
        output = self.vm_test01.get_output(cmd)
        self.assertEqual("", output,
                         "There're packages that are not signed.\n {0}".format(output))

    def test_check_hostname(self):
        self.log.info("Check the hostname")
        self.assertEqual(self.vm_test01.get_output("hostname"), self.vm_params.get("HostName"),
                         "The hostname is wrong")

    def test_check_release_version(self):
        self.log.info("Check the /etc/redhat-release file contains a correct release version")
        self.assertIn("Red Hat Enterprise Linux Server release {0}".format(self.project),
                      self.vm_test01.get_output("cat /etc/redhat-release"),
                      "The release version is wrong")

    def test_check_boot_message(self):
        self.log.info("Check the boot messages with no errors")
        self.assertEqual("", self.vm_test01.check_messages_log(),
                         "There're error logs")

    def test_check_kvm_pv_drivers(self):
        self.log.info("Check kvm pv drivers in VM")
        module_list = ["virtio_balloon", "virtio_net", "virtio_console", "virtio_blk", "virtio_pci", "virtio_ring"]
        output = self.vm_test01.get_output("lsmod|grep 'virtio'")
        for module in module_list:
            self.assertIn(module, output,
                          "%s module doesn't exist" % module)

    def test_validation(self):
        self.log.info("Validation test")
        region_list = ["us-west-1"]
        instance_type_list = ["ecs.n1.tiny",
                              "ecs.xn4.small"]
        error_msg = ""
        for region in region_list:
            self.vm_test01["RegionId"] = region
            # Create and start instances
            for instance_type in instance_type_list:
                self.vm_test01["InstanceType"] = instance_type
                self.vm_params["InstanceName"] = self.params.get('name', '*/VM/*') + \
                                                str(self.project).replace('.', '') + \
                                                self.vm_params["InstanceType"][4:].lower().replace(".", "")
                self.log.info("Creating ECS. Region:{0}, Instance type:{1}".format(region, instance_type))
                self.vm_test01.create(self.vm_params)
                self.vm_test01.wait_for_created()
                self.vm_test01.allocate_public_address()
                self.vm_test01.start()
            # Login instnaces and check
            for instance_type in instance_type_list:
                self.vm_test01.wait_for_running()
                if not self.vm_test01.wait_for_login():
                    tmp_msg = "Fail to login. Region:{0}, Instance type:{1}".format(region, instance_type)
                    self.log.error(tmp_msg)
                    error_msg += tmp_msg + '\n'
                    continue
                std_cpu = self.params.get('cpu', '*/{0}/*'.format(instance_type))
                real_cpu = self.vm_test01.get_output("grep processor /proc/cpuinfo|wc -l")
                if int(real_cpu) != int(std_cpu):
                    error_msg += "CPU number is wrong. Region:{0}, Instance type:{1}, "\
                                 "Standard:{2}, Real:{3}\n".format(region, instance_type, std_cpu, real_cpu)
        if error_msg != "":
            self.fail("Validation test failed. Error messages:\n"+error_msg)


    def tearDown(self):
        self.log.info("TearDown")
