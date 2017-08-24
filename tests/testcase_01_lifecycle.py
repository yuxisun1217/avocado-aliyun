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
        self.host_pubkey_file = prep.host_pubkey_file
        self.vm_test01 = prep.vm_test01
        self.vm_params = prep.vm_params
        args = []
        if "create_ecs" in self.name.name:
            args.append("pre-delete")
        if "start_ecs" in self.name.name:
            args.append("pre-stop")
        prep.vm_prepare(args)

    def test_create_ecs(self):
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

    def test_delete_ecs(self):
        self.log.info("Delete ECS")
        self.vm_test01.delete()
        self.vm_test01.wait_for_deleted()

    def tearDown(self):
        self.log.info("Tear Down")
        pass
