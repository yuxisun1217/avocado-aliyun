import time
import sys
import os
import re

from avocado import Test

REALPATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(os.path.dirname(REALPATH)))

from api.setup import Setup


class MiscTest(Test):

    def setUp(self):
        prep = Setup(self.params)
        prep.selected_case(self.name)
        self.project = prep.project
        self.vm_test01 = prep.vm_test01
        self.vm_params = prep.vm_params
        if "ecs.i" not in self.vm_params["InstanceType"] and "ecs.d" not in self.vm_params["InstanceType"] \
                and "test_delete_ecs" not in self.name.name:
            self.cancel("Skip for instance types not in ecs.i1/i2 series")
        args = []
        prep.vm_prepare(args)

    def test_local_disks(self):
        self.log.info("Test local disks on VM")
        instance_type = self.vm_test01.params["InstanceType"]
        disk_count = self.params.get('disk_count', '*/{0}/*'.format(instance_type))
        disk_size = self.params.get('disk_size', '*/{0}/*'.format(instance_type))
        disk_type = self.params.get('disk_type', '*/{0}/*'.format(instance_type))
        for i in xrange(1, disk_count + 1):
            delta = self.disk_count + i
            if delta <= 25:
                idx = chr(97 + delta)
            else:
                idx = 'a' + chr(97 - 1 + delta % 25)
            cmd = "fdisk -l /dev/vd%s | grep '/dev/vd%s' | cut -d ',' -f 1 | cut -d ' ' -f 4"
            output = self.vm_test01.get_output(cmd % (idx, idx))
            self.assertEqual(output, "GB",
                             "Local disk size is not as expected.\n {0}".format(output))
            cmd = "fdisk -l /dev/vd%s | grep '/dev/vd%s' | cut -d ',' -f 1 | cut -d ' ' -f 3"
            output = self.vm_test01.get_output(cmd % (idx, idx))
            self.assertTrue(float(output) >= disk_size,
                            "Local disk size is not as expected.\n {0}".format(output))
            cmd = "[[ -d /mnt/vd%s ]] || mkdir /mnt/vd%s"
            self.vm_test01.get_output(cmd % (idx, idx))
            cmd = "mkfs.ext4 /dev/vd%s && mount /dev/vd%s /mnt/vd%s && echo 'test_content' > /mnt/vd%s/test_file"
            self.vm_test01.get_output(cmd % (idx, idx, idx, idx))
            cmd = "cat /mnt/vd%s/test_file"
            output = self.vm_test01.get_output(cmd % idx)
            self.assertEqual(output, "test_content",
                             "Cannot write files on attached disk.\n {0}".format(output))
            cmd = "umount /mnt/vd%s"
            self.vm_test01.get_output(cmd % idx)

    def test_delete_ecs(self):
        self.log.info("Delete ECS")
        self.vm_test01.delete()
        self.vm_test01.wait_for_deleted()

    def tearDown(self):
        self.log.info("TearDown")
