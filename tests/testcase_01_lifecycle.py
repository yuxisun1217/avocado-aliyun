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
        if "create_ecs" in self.name.name:
            args.append("pre-delete")
        if "start_ecs" in self.name.name:
            args.append("pre-stop")
        prep.vm_prepare(args)

    def test_create_ecs(self):
        self.log.info("Create ECS")
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
        before = self.vm_test01.get_output("who -b")
        self.vm_test01.restart()
        self.vm_test01.wait_for_running()
        self.vm_test01.wait_for_login()
        after = self.vm_test01.get_output("who -b")
        self.assertNotEqual(before, after,
                            "Restart error: ECS is not restarted")
        self.log.info("2. Force restart ECS")
        before = after
        self.vm_test01.restart(force=True)
        self.vm_test01.wait_for_running()
        self.vm_test01.wait_for_login()
        after = self.vm_test01.get_output("who -b")
        self.assertNotEqual(before, after,
                            "Force restart error: ECS is not restarted")

    def test_delete_ecs(self):
        self.log.info("Delete ECS")
        self.vm_test01.delete()
        self.vm_test01.wait_for_deleted()

    def test_reboot_inside_vm(self):
        self.log.info("Reboot inside VM")
        self.vm_test01.get_output("reboot")
        time.sleep(30)
        self.assertTrue(self.vm_test01.wait_for_login(),
                        "Fail to access to VM")


    def tearDown(self):
        self.log.info("Tear Down")
        pass
