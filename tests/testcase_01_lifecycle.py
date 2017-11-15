import time
import sys
import os
import re

from avocado import Test

REALPATH = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(os.path.dirname(REALPATH)))

from api.setup import Setup


class LifeCycleTest(Test):

    def setUp(self):
        prep = Setup(self.params)
        prep.selected_case(self.name)
        self.project = prep.project
        self.vm_test01 = prep.vm_test01
        self.vm_params = prep.vm_params
        args = []
        if "password" in self.name.name:
            args.append("password")
        if "create_ecs" in self.name.name:
            args.append("pre-delete")
        if "test_start_ecs" in self.name.name or \
           "test_modify_instance_type" in self.name.name:
            args.append("pre-stop")
        prep.vm_prepare(args)

    def test_password_create_ecs(self):
        self.log.info("Create ECS with password")
        self.vm_test01.create(self.vm_params, authentication="password")
        self.vm_test01.wait_for_created()
        self.vm_test01.allocate_public_address()
        self.assertIsNotNone(self.vm_test01.get_public_address(),
                             "Fail to allocate public ip address")

    def test_password_start_ecs(self):
        self.log.info("Start ECS")
        self.vm_test01.start()
        self.vm_test01.wait_for_running()
        self.assertTrue(self.vm_test01.wait_for_login(authentication="password"),
                        "Fail to ssh login")

    def test_reset_password_ecs(self):
        self.log.info("Reset password for ECS")
        self.vm_test01.reset_password(new_password="Redhat123$")
        self.vm_test01.password="Redhat123$"
        self.vm_params["Password"]="Redhat123$"
        self.vm_test01.restart()
        self.vm_test01.wait_for_running()
        self.assertTrue(self.vm_test01.wait_for_login(authentication="password"),
                        "Fail to ssh login")

    def test_create_ecs(self):
        self.log.info("Create ECS with keypair")
        self.vm_test01.create(self.vm_params)
        self.vm_test01.wait_for_created()
        self.vm_test01.allocate_public_address()
        self.assertIsNotNone(self.vm_test01.get_public_address(),
                             "Fail to allocate public ip address")

    def test_start_ecs(self):
        self.log.info("Start ECS")
        self.vm_test01.start()
        self.vm_test01.wait_for_running()
        self.assertTrue(self.vm_test01.wait_for_login(),
                        "Fail to ssh login")

    def test_stop_ecs(self):
        """
        Stop ECS
        1. Stop ECS
        2. Force stop ECS
        """
        self.log.info("Stop ECS")
        self.log.info("1. Stop ECS")
        self.vm_test01.stop()
        self.vm_test01.wait_for_stopped()
        self.assertFalse(self.vm_test01.wait_for_login(timeout=10),
                         "Should not be able to login when ECS is stopped")
        # Recovery: Start VM
        self.vm_test01.start()
        self.vm_test01.wait_for_running()
        self.vm_test01.wait_for_login()
        self.log.info("2. Force stop ECS")
        self.vm_test01.stop(force=True)
        self.vm_test01.wait_for_stopped()
        self.assertFalse(self.vm_test01.wait_for_login(timeout=10),
                         "Should not be able to login when ECS is force stopped")

    def test_restart_ecs(self):
        """
        Restart ECS
        1. Restart ECS
        2. Force restart ECS
        """
        self.log.info("Restart ECS")
        self.log.info("1. Restart ECS")
        self.vm_test01.wait_for_login()
        before = self.vm_test01.get_output("who -b")
        time.sleep(60)
        self.vm_test01.restart()
        self.vm_test01.wait_for_running()
        self.vm_test01.wait_for_login()
        after = self.vm_test01.get_output("who -b")
        self.assertNotEqual(before, after,
                            "Restart error: ECS is not restarted")
        self.log.info("2. Force restart ECS")
        before = after
        time.sleep(60)
        self.vm_test01.restart(force=True)
        self.vm_test01.wait_for_running()
        self.vm_test01.wait_for_login()
        after = self.vm_test01.get_output("who -b")
        self.assertNotEqual(before, after,
                            "Force restart error: ECS is not restarted")

    def test_reboot_inside_vm(self):
        self.log.info("Reboot inside VM")
        self.vm_test01.wait_for_login()
        before = self.vm_test01.get_output("who -b")
        time.sleep(60)
        self.vm_test01.send_line("reboot")
        self.vm_test01.wait_for_running()
        self.vm_test01.wait_for_login()
        after = self.vm_test01.get_output("who -b")
        self.assertNotEqual(before, after,
                            "Restart error: ECS is not restarted")

    def test_modify_instance_type(self):
        self.log.info("Modify ECS instance type")
        self.vm_test01.modify_instance_type(new_type="ecs.n1.medium")
        self.vm_test01.start()
        self.vm_test01.wait_for_running()
        self.vm_test01.wait_for_login()
        cpu = self.vm_test01.get_output("cat /proc/cpuinfo|grep processor|wc -l")
        memory = self.vm_test01.get_output("cat /proc/meminfo|grep MemTotal")
        cpu_std = self.params.get("cpu")

    def test_delete_ecs(self):
        self.log.info("Delete ECS")
        self.vm_test01.delete()
        self.vm_test01.wait_for_deleted()

    def tearDown(self):
        self.log.info("Tear Down")
