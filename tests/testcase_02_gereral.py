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
        self.rhel7_cert = """-----BEGIN CERTIFICATE-----
MIIGDTCCA/WgAwIBAgIJALDxRLt/tVsrMA0GCSqGSIb3DQEBBQUAMIGuMQswCQYD
VQQGEwJVUzEXMBUGA1UECAwOTm9ydGggQ2Fyb2xpbmExFjAUBgNVBAoMDVJlZCBI
YXQsIEluYy4xGDAWBgNVBAsMD1JlZCBIYXQgTmV0d29yazEuMCwGA1UEAwwlUmVk
IEhhdCBFbnRpdGxlbWVudCBQcm9kdWN0IEF1dGhvcml0eTEkMCIGCSqGSIb3DQEJ
ARYVY2Etc3VwcG9ydEByZWRoYXQuY29tMB4XDTE3MDYyODE4MDUxMFoXDTM3MDYy
MzE4MDUxMFowRDFCMEAGA1UEAww5UmVkIEhhdCBQcm9kdWN0IElEIFs0Zjk5OTVl
MC04ZGM0LTRiNGYtYWNmZS00ZWYxMjY0Yjk0ZjNdMIICIjANBgkqhkiG9w0BAQEF
AAOCAg8AMIICCgKCAgEAxj9J04z+Ezdyx1U33kFftLv0ntNS1BSeuhoZLDhs18yk
sepG7hXXtHh2CMFfLZmTjAyL9i1XsxykQpVQdXTGpUF33C2qBQHB5glYs9+d781x
8p8m8zFxbPcW82TIJXbgW3ErVh8vk5qCbG1cCAAHb+DWMq0EAyy1bl/JgAghYNGB
RvKJObTdCrdpYh02KUqBLkSPZHvo6DUJFN37MXDpVeQq9VtqRjpKLLwuEfXb0Y7I
5xEOrR3kYbOaBAWVt3mYZ1t0L/KfY2jVOdU5WFyyB9PhbMdLi1xE801j+GJrwcLa
xmqvj4UaICRzcPATP86zVM1BBQa+lilkRQes5HyjZzZDiGYudnXhbqmLo/n0cuXo
QBVVjhzRTMx71Eiiahmiw+U1vGqkHhQNxb13HtN1lcAhUCDrxxeMvrAjYdWpYlpI
yW3NssPWt1YUHidMBSAJ4KctIf91dyE93aStlxwC/QnyFsZOmcEsBzVCnz9GmWMl
1/6XzBS1yDUqByklx0TLH+z/sK9A+O2rZAy1mByCYwVxvbOZhnqGxAuToIS+A81v
5hCjsCiOScVB+cil30YBu0cH85RZ0ILNkHdKdrLLWW4wjphK2nBn2g2i3+ztf+nQ
ED2pQqZ/rhuW79jcyCZl9kXqe1wOdF0Cwah4N6/3LzIXEEKyEJxNqQwtNc2IVE8C
AwEAAaOBljCBkzAJBgNVHRMEAjAAMDAGCysGAQQBkggJAUUBBCEMH1JlZCBIYXQg
RW50ZXJwcmlzZSBMaW51eCBTZXJ2ZXIwFAYLKwYBBAGSCAkBRQIEBQwDNy40MBcG
CysGAQQBkggJAUUDBAgMBng4Nl82NDAlBgsrBgEEAZIICQFFBAQWDBRyaGVsLTcs
cmhlbC03LXNlcnZlcjANBgkqhkiG9w0BAQUFAAOCAgEAsFOqdKsB2R1tBQPsDOxq
ocR4pdKgYvYvZ0HlgcDtdK8g9FqJcD8z78ryQI1LtCR7vryZ8BW3645u0gFxY96j
+6Jpy4uusYpRm4MaVmzLq8G43yJa01TjU6emSvBuAUOLprBJTYc5AzNGOK2bVCJO
jEn4raBuEYjpC5Wy9r6Thp95U6PlkYC9EZAfX8IdFMWIlOoCl8HrWl186fy95gM7
iZID968vrw/yvzsyh6Xbr0rCWOC82wNRcOx1TITtzkLD/d3PB1Gxt4zV5H9LBtYj
KQ8DHM0GzCNNuEKB/CsNRI9kXxp2KKdmkax5a7Fn7hbTBqiq+WOJVzUHGjrnS7aR
7dvfkHx7Yas9JdeCEcanJluL1hQUQ9DIx/PojSQ6bDAJrvakUHGG5FJ7vOFzEZ7t
cuRHl7E/DBqb/ElXQ2m8motoNfZoNRUk2x/t+X7s4ygAgv2Lg+7q05SPrhHdKcTC
YFlmcwUdl2oIS8XiEgRn0uff2PxJIB+dqELNIqY9E54BCkD6fb9CpKEtAZndKMCk
IHKzYSSFY6cr9w2/tET7J/hZhETkopWnHh3auZIGizTeKfcM4uZA14vwyZydu52j
GIqsZDPpoSajx5UZcx2RXyVLmGPDNdTZLvRaX60TQk/ZJh7xdhw3ojUUiAJrrQ+O
E82UcqNc+f9GbP8zuLA4Tl4=
-----END CERTIFICATE-----"""
        self.rhel6_cert = """-----BEGIN CERTIFICATE-----
MIIGDTCCA/WgAwIBAgIJALDxRLt/tU/zMA0GCSqGSIb3DQEBBQUAMIGuMQswCQYD
VQQGEwJVUzEXMBUGA1UECAwOTm9ydGggQ2Fyb2xpbmExFjAUBgNVBAoMDVJlZCBI
YXQsIEluYy4xGDAWBgNVBAsMD1JlZCBIYXQgTmV0d29yazEuMCwGA1UEAwwlUmVk
IEhhdCBFbnRpdGxlbWVudCBQcm9kdWN0IEF1dGhvcml0eTEkMCIGCSqGSIb3DQEJ
ARYVY2Etc3VwcG9ydEByZWRoYXQuY29tMB4XDTE2MDMxNzIwMzEwOVoXDTM2MDMx
MjIwMzEwOVowRDFCMEAGA1UEAww5UmVkIEhhdCBQcm9kdWN0IElEIFswNjY0MTEz
MC0wNzM2LTQ4NGMtYmNkZC1kYmNkZTk4YWMxMGFdMIICIjANBgkqhkiG9w0BAQEF
AAOCAg8AMIICCgKCAgEAxj9J04z+Ezdyx1U33kFftLv0ntNS1BSeuhoZLDhs18yk
sepG7hXXtHh2CMFfLZmTjAyL9i1XsxykQpVQdXTGpUF33C2qBQHB5glYs9+d781x
8p8m8zFxbPcW82TIJXbgW3ErVh8vk5qCbG1cCAAHb+DWMq0EAyy1bl/JgAghYNGB
RvKJObTdCrdpYh02KUqBLkSPZHvo6DUJFN37MXDpVeQq9VtqRjpKLLwuEfXb0Y7I
5xEOrR3kYbOaBAWVt3mYZ1t0L/KfY2jVOdU5WFyyB9PhbMdLi1xE801j+GJrwcLa
xmqvj4UaICRzcPATP86zVM1BBQa+lilkRQes5HyjZzZDiGYudnXhbqmLo/n0cuXo
QBVVjhzRTMx71Eiiahmiw+U1vGqkHhQNxb13HtN1lcAhUCDrxxeMvrAjYdWpYlpI
yW3NssPWt1YUHidMBSAJ4KctIf91dyE93aStlxwC/QnyFsZOmcEsBzVCnz9GmWMl
1/6XzBS1yDUqByklx0TLH+z/sK9A+O2rZAy1mByCYwVxvbOZhnqGxAuToIS+A81v
5hCjsCiOScVB+cil30YBu0cH85RZ0ILNkHdKdrLLWW4wjphK2nBn2g2i3+ztf+nQ
ED2pQqZ/rhuW79jcyCZl9kXqe1wOdF0Cwah4N6/3LzIXEEKyEJxNqQwtNc2IVE8C
AwEAAaOBljCBkzAJBgNVHRMEAjAAMDAGCysGAQQBkggJAUUBBCEMH1JlZCBIYXQg
RW50ZXJwcmlzZSBMaW51eCBTZXJ2ZXIwFAYLKwYBBAGSCAkBRQIEBQwDNi44MBcG
CysGAQQBkggJAUUDBAgMBng4Nl82NDAlBgsrBgEEAZIICQFFBAQWDBRyaGVsLTYs
cmhlbC02LXNlcnZlcjANBgkqhkiG9w0BAQUFAAOCAgEAkmwyb55mtjLpXrG/djUP
Ux1e4AGBpmZ4Tw/RkHOu5wFfX8M4GstThoaiDgBtd0G1DCgeGDufRVVBluWkEIdE
4YC/KEaXDu6tZ+/ulL9gAufooGSJovpSZJDScuJY5NozYlydtJkLZDKHM8GUmRqO
D8RDU5wCTy8Em0uGweUWq/MC5pMZsYlw2fGgfpPap/j/LurKa1TBm+az0+a1iHFF
Ls61K9EbdrtcXe2Cp8sYhWUPQn9IBJhgi079NS7xfAvuOlk0vuM8b8RvkXAVMdjE
EMJRqwrhyeicIzt8roK/beADfH7RM314MjKB10ot4oR0JVX+f9EE4aGDTwZFrh2d
qTFkQKNfKBx2wWEfNGOwU5uiNYlTuxhiDoVximVmCaLIaqPJtseAcyXC4YhBiC0u
1XaCWaePn1FI25BGNe4y5/BYc+hPfArMEFmDQWXVFvZ3Qx2bFju0AE387KxvROd+
nVsx8b8WzyHnOvF0b6XnAbA2XDuymbb9FoEdgU00bEa6v7BbFOKNNlIwB4m5fTIC
C/jyZBxu5Rg48PB3dghkaw9C7rAW039f7uIg1YeCoh2g704VibIBI29Xc8W4XDIN
xF2tTJSpYRzmwFFda50RcJgYmddHPc+n1yvu8Ptg/yhdghbRsWLtxOOwR6K4+VFp
YlUJiCvEei7xX/qSPtyti68=
-----END CERTIFICATE-----"""

    def test_verify_package_signed(self):
        self.log.info("Verify all packages are signed")
        cmd = "rpm -qa --qf '%{name}-%{version}-%{release}.%{arch} (%{SIGPGP:pgpsig})\\n'|grep -v 'Key ID'"
        output = self.vm_test01.get_output(cmd)
        self.assertEqual("", output,
                         "There're packages that are not signed.\n {0}".format(output))

    def test_check_virt_what(self):
        self.log.info("Check the virt-what")
        self.assertEqual(self.vm_test01.get_output("virt-what"), "kvm", "virt-what result is not kvm")

    def test_check_selinux(self):
        self.log.info("Check SELinux status")
        self.assertEqual(self.vm_test01.get_output("getenforce"), "Enforcing", "SELinux is not enforcing")
        cmd = "cat /etc/selinux/config|grep -v '^[[:space:]]*#'|grep 'SELINUX='|cut -d '=' -f 2"
        self.assertEqual(self.vm_test01.get_output(cmd), "enforcing", "SELinux is not enforcing")

    def test_check_hostname(self):
        self.log.info("Check the hostname")
        self.assertEqual(self.vm_test01.get_output("hostname"), self.vm_params.get("HostName"),
                         "The hostname is wrong")

    def test_check_release_version(self):
        self.log.info("Check the /etc/redhat-release file contains a correct release version")
        self.assertIn("Red Hat Enterprise Linux Server release {0}".format(self.project),
                      self.vm_test01.get_output("cat /etc/redhat-release"),
                      "The release version is wrong")

    def test_check_product_certificate(self):
        self.log.info("Check the /etc/pki/product-default/69.pem file contains the right data")
        cert = ""
        if int(self.project) == 7:
            cert = self.rhel7_cert
        elif int(self.project) == 6:
            cert = self.rhel6_cert
        self.assertEqual(cert,
                         self.vm_test01.get_output("cat /etc/pki/product-default/69.pem"),
                         "The product certificate is wrong")

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
