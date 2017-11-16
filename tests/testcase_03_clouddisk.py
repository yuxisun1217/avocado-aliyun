import time
import sys
import os
import re

from avocado import Test

REALPATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(os.path.dirname(REALPATH)))

from api.setup import Setup


class CloudDiskTest(Test):

    def setUp(self):
        self.cloud_disk_limit = 16
        prep = Setup(self.params)
        prep.selected_case(self.name)
        self.project = prep.project
        self.vm_test01 = prep.vm_test01
        self.vm_params = prep.vm_params
        args = []
        if "offline" in self.name.name:
            args.append("pre-stop")
        if "ecs.i" in self.vm_params["InstanceType"] or "ecs.d" in self.vm_params["InstanceType"]:
            self.disk_count = self.params.get('disk_count', '*/{0}/*'.format(self.vm_params["InstanceType"]))
        else:
            self.disk_count = 0
        prep.vm_prepare(args)
        prep.disk_prepare(disk_count=self.cloud_disk_limit)

    def test_online_attach_cloud_disks(self):
        self.log.info("Online attach a cloud disk to VM")
        for disk_id in self.vm_params.get("AttachDiskIds"):
            self.vm_test01.attach_disk(diskid=disk_id)
            while True:
                output = self.vm_test01.describe_disks(self.vm_params, diskid=disk_id.encode("ascii"))
                status = output.get("Disks").get("Disk")[0].get("Status")
                if status == u"In_use":
                    break
                else:
                    time.sleep(1)
        for i in xrange(1, self.cloud_disk_limit + 1):
            delta = self.disk_count + i
            if delta <= 25:
                idx = chr(97 + delta)
            else:
                idx = 'a' + chr(97 - 1 + delta % 25)
            cmd = "fdisk -l /dev/vd%s | grep '/dev/vd%s' | cut -d ',' -f 1 | cut -d ' ' -f 4"
            output = self.vm_test01.get_output(cmd % (idx, idx))
            self.assertEqual(output, "GB",
                             "Attach disk size is not as expected.\n {0}".format(output))
            cmd = "fdisk -l /dev/vd%s | grep '/dev/vd%s' | cut -d ',' -f 1 | cut -d ' ' -f 3"
            output = self.vm_test01.get_output(cmd % (idx, idx))
            self.assertTrue(22 > float(output) >= 20,
                             "Attach disk size is not as expected.\n {0}".format(output))
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

    def test_online_detach_cloud_disks(self):
        self.log.info("Online detach a cloud disk to VM")
        for disk_id in self.vm_params.get("AttachDiskIds"):
            self.vm_test01.detach_disk(diskid=disk_id)
            while True:
                output = self.vm_test01.describe_disks(self.vm_params, diskid=disk_id.encode("ascii"))
                status = output.get("Disks").get("Disk")[0].get("Status")
                if status == u"Available":
                    break
                else:
                    time.sleep(1)
        for i in xrange(1, self.cloud_disk_limit + 1):
            delta = self.disk_count + i
            if delta <= 25:
                idx = chr(97 + delta)
            else:
                idx = 'a' + chr(97 - 1 + delta % 25)
            cmd = "fdisk -l | grep '/dev/vd%s'"
            output = self.vm_test01.get_output(cmd % idx)
            self.assertEqual(output, "",
                             "Disk not detached.\n {0}".format(output))


    def test_offline_attach_cloud_disks(self):
        self.log.info("Offline attach a cloud disk to VM")
        for disk_id in self.vm_params.get("AttachDiskIds"):
            self.vm_test01.attach_disk(diskid=disk_id)
            while True:
                output = self.vm_test01.describe_disks(self.vm_params, diskid=disk_id.encode("ascii"))
                status = output.get("Disks").get("Disk")[0].get("Status")
                if status == u"In_use":
                    break
                else:
                    time.sleep(1)
        self.vm_test01.start()
        self.vm_test01.wait_for_running()
        self.assertTrue(self.vm_test01.wait_for_login(),
                        "Fail to ssh login after offline attach disks")
        for i in xrange(1, self.cloud_disk_limit + 1):
            delta = self.disk_count + i
            if delta <= 25:
                idx = chr(97 + delta)
            else:
                idx = 'a' + chr(97 - 1 + delta % 25)
            cmd = "fdisk -l /dev/vd%s | grep '/dev/vd%s' | cut -d ',' -f 1 | cut -d ' ' -f 4"
            output = self.vm_test01.get_output(cmd % (idx, idx))
            self.assertEqual(output, "GB",
                             "Attach disk size is not as expected.\n {0}".format(output))
            cmd = "fdisk -l /dev/vd%s | grep '/dev/vd%s' | cut -d ',' -f 1 | cut -d ' ' -f 3"
            output = self.vm_test01.get_output(cmd % (idx, idx))
            self.assertTrue(22 > float(output) >= 20,
                             "Attach disk size is not as expected.\n {0}".format(output))
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

    def test_offline_detach_cloud_disks(self):
        self.log.info("Offline detach a cloud disk to VM")
        for disk_id in self.vm_params.get("AttachDiskIds"):
            self.vm_test01.detach_disk(diskid=disk_id)
            while True:
                output = self.vm_test01.describe_disks(self.vm_params, diskid=disk_id.encode("ascii"))
                status = output.get("Disks").get("Disk")[0].get("Status")
                if status == u"Available":
                    break
                else:
                    time.sleep(1)
        self.vm_test01.start()
        self.vm_test01.wait_for_running()
        self.assertTrue(self.vm_test01.wait_for_login(),
                        "Fail to ssh login after offline attach disks")
        for i in xrange(1, self.cloud_disk_limit + 1):
            delta = self.disk_count + i
            if delta <= 25:
                idx = chr(97 + delta)
            else:
                idx = 'a' + chr(97 - 1 + delta % 25)
            cmd = "fdisk -l | grep '/dev/vd%s'"
            output = self.vm_test01.get_output(cmd % idx)
            self.assertEqual(output, "",
                             "Disk not detached.\n {0}".format(output))

    def tearDown(self):
        self.log.info("TearDown")
