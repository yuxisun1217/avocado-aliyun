import logging
import time
import os
import sys

#REALPATH = os.path.split(os.path.realpath(__file__))[0]
#sys.path.append(os.path.join(os.path.dirname(REALPATH)))

from utils import utils_misc
from utils import remote
from utils.globalvars import GlobalVars as g
from aexpect.exceptions import ShellProcessTerminatedError
from aexpect.exceptions import ShellTimeoutError

MESSAGES_IGNORELIST = []


class GuestUtils(object):
    def __init__(self, params):
        self.params = params
        self.session = None
        self.username = self.params.get("username")
        self.password = self.params.get("Password")

    @property
    def name(self):
        return None

    def get_public_address(self):
        return None

    def get_ssh_port(self):
        return "22"

    def vm_disk_part(self, disk, partition=1, del_part=True, label="msdos", start=None, end=None, size=None, sudo=True):
        logging.info("DISK: %s", disk)
        if del_part:
            self.get_output("parted -s %s rm %d" % (disk, partition))
        current_label = self.get_output("parted {0} print|grep Partition".format(disk))
        if ("unknown" in current_label) or (label not in current_label):
            self.get_output("parted -s {0} mklabel {1}".format(disk, label))
        min, max = self.get_output("parted %s unit GB p free|grep Free|tail -1" % disk).replace("GB", "").split()[0:2]
        if not start:
            start = min
        if not end:
            end = max
        # If size is set, the "end" config will be ignored
        if size:
            end = float(start) + size
        start = start if "GB" in str(start).upper() else str(start)+"GB"
        end = end if "GB" in str(end).upper() else str(end)+"GB"
        self.get_output("parted %s mkpart primary %s %s" % (disk, start, end))
        output = self.get_output("parted {0} print".format(disk+str(partition)))
        if "Could not stat device" in output:
            logging.error("Fail to part disk "+disk)
            raise Exception

    def vm_disk_mount(self, disk, mount_point, fstype="ext4", partition=1,
                      del_part=True, start=None, end=None, size=None,
                      sudo=True):
        self.vm_disk_part(disk, partition=partition, del_part=del_part,
                          start=start, end=end, size=size, sudo=sudo)
        self.get_output("mkfs.{0} %s".format(fstype) % disk+str(partition), timeout=300, sudo=sudo)
        self.get_output("mkdir -p %s" % mount_point, sudo=sudo)
        self.get_output("mount %s %s" % (disk+str(partition), mount_point), sudo=sudo)
        if self.get_output("mount | grep %s" % mount_point, sudo=sudo) == "":
            logging.error("Fail to mount %s to %s" % (disk+str(partition), mount_point))
            raise Exception
        return True

    def vm_disk_check(self, mount_point):
        self.get_output("touch %s" % mount_point+"/file1")
        self.get_output("echo \"test\" > %s" % mount_point+"/file1")
        self.get_output("mkdir %s" % mount_point+"/folder1")
        if self.get_output("cat %s" % mount_point+"/file1").strip('\n') != "test":
            logging.error("Fail to write in %s" % mount_point+"/file1")
            raise Exception
        self.get_output("cp %s %s" % (mount_point+"/file1", mount_point+"/file2"))
        self.get_output("rm -f %s" % mount_point+"/file1")
        if "No such file or directory" not in self.get_output("ls %s" % mount_point+"/file1"):
            logging.error("Fail to remove file from %s" % mount_point+"/file1")
            raise Exception
        return True

    def login(self, timeout=g.LOGIN_TIMEOUT,
              username=None, password=None, authentication="password"):
        """
        Log into the guest via SSH.
        If timeout expires while waiting for output from the guest (e.g. a
        password prompt or a shell prompt) -- fail.

        :param timeout: Time (seconds) before giving up logging into the
                guest.
        :param username:
        :param password:
        :param authentication: ssh PreferredAuthentications. Should be password of publickey.
        :return: A ShellSession object.
        """
        if username is None:
            username = self.username
        if authentication == "password" and password is None:
            password = self.password
        prompt = self.params.get("shell_prompt", "[\#\$]")
#        linesep = eval("'%s'" % self.params.get("shell_linesep", r"\n"))
        client = self.params.get("shell_client", "ssh")
        address = self.get_public_address()
        port = self.get_ssh_port()
        log_filename = ("session-%s-%s.log" %
                        (self.name, utils_misc.generate_random_string(4)))
        session = remote.remote_login(client=client, host=address, port=port,
                                      username=username, password=password, prompt=prompt,
                                      log_filename=log_filename, timeout=timeout,
                                      authentication=authentication)
        session.set_status_test_command(self.params.get("status_test_command", ""))
        self.session_close()
        self.session = session
        #        logging.info("Session: ")
        #        logging.info(type(session))
        return session

    def remote_login(self, timeout=g.LOGIN_TIMEOUT,
                     username=None, password=None, authentication="password"):
        """
        Alias for login() for backward compatibility.
        """
        return self.login(timeout=timeout, username=username, password=password,
                          authentication=authentication)

    def get_output(self, cmd="", timeout=g.DEFAULT_TIMEOUT, sudo=True, max_retry=1, ignore_status=False):
        """
        Run command and return output into guest
        :param cmd:
        :param timeout: SSH connection timeout
        :param sudo: If the command need sudo permission
        :param max_retry: The max retry number
        :param ignore_status: Ignore return code. Continue even if command run failed
        :return: raise if exception
        """
        if self.username == "root":
            sudo = False
        sudo_cmd = "echo %s | sudo -S sh -c \"\"" % self.params.get("password")
        if sudo:
            cmd = "sudo sh -c \"%s\"" % cmd
#            cmd = "echo %s | sudo -S sh -c \"%s\"" % (self.password, cmd)
        for retry in xrange(0, max_retry):
            try:
                if sudo:
                    self.session.cmd_output(sudo_cmd)
#                logging.info(cmd)
                output = self.session.cmd_output(cmd, timeout).rstrip('\n')
            except (ShellTimeoutError, ShellProcessTerminatedError):
                logging.info("Run command %s timeout. Retry %d/%d" % (cmd, retry+1, max_retry))
                self.wait_for_login()
                continue
            except Exception, e:
                logging.info("Run command %s fail. Exception: %s", cmd, str(e))
                raise
            else:
                break
        else:
            if ignore_status:
                return None
            else:
#                logging.info("After retry %d times, run command %s timeout" % (max_retry, cmd))
                raise Exception("After retry %d times, run command %s timeout" % (max_retry, cmd))
        logging.info(output)
        return output

    def send_line(self, cmd=""):
        self.session.sendline(cmd)

    def modify_value(self, key, value, conf_file, sepr='='):
        """

        :param key: The name of the parameter
        :param value: The value of the parameter
        :param conf_file: The file to be modified
        :param sepr: The separate character
        :return: True/False of the modify result
        """
        #        if self.get_output("grep -R \'%s\' %s" % (key, conf_file)):
        #            self.get_output("sed -i -e '/^.*%s/s/^# *//g' -e 's/%s.*$/%s%s%s/g' %s" %
        #                            (key, key, key, sepr, value, conf_file))
        if self.get_output("grep -R \'^{0}\' {1}".format(key, conf_file)):
            self.get_output("sed -i 's/{0}.*$/{0}{1}{2}/g' {3}".format(key, sepr, value, conf_file))
        else:
            self.get_output("echo \'{0}{1}{2}\' >> {3}".format(key, sepr, value, conf_file))
        time.sleep(0.5)
        return self.verify_value(key, value, conf_file, sepr)

    def verify_value(self, key, value, conf_file, sepr='='):
        if not self.get_output("grep -R \'^{0}{1}{2}\' {3}".format(key, sepr, value, conf_file)):
            logging.error("Fail to modify to {0}{1}{2} in {3}".format(key, sepr, value, conf_file))
            return False
        else:
            return True

    def wait_for_login(self, username=None, password=None, timeout=g.LOGIN_WAIT_TIMEOUT,
                       authentication="publickey", options=''):
        """

        :param username: VM username
        :param password: VM password
        :param timeout: Retry timeout
        :param authentication: ssh PreferredAuthentications
        :param options: Other options of ssh
        :return: False if timeout
        """
        if username is None:
            username = self.username
        if authentication == "password" and password is None:
            password = self.password
        host = self.get_public_address()
        port = self.get_ssh_port()

        prompt = self.params.get("shell_prompt", "[\#\$]")
        try:
            session = remote.wait_for_login(client="ssh", host=host, port=port,
                                            username=username, password=password,
                                            prompt=prompt, timeout=timeout,
                                            authentication=authentication,
                                            options=options)
        except Exception, e:
            logging.info("Timeout. Cannot login VM. Exception: %s", str(e))
            return False
        logging.info("VM is alive.")
        self.session_close()
        self.session = session
        return True

    def copy_files_to(self, host_path, guest_path, limit="",
                      verbose=False,
                      timeout=g.COPY_FILES_TIMEOUT,
                      username=None, password=None):
        """
        Transfer files to the remote host(guest).
        :param username: VM username
        :param password: VM password
        :param host_path: Host path
        :param guest_path: Guest path
        :param limit: Speed limit of file transfer.
        :param verbose: If True, log some stats using logging.info (RSS only)
        :param timeout: Time (seconds) before giving up on doing the remote
                copy.
        """
        logging.info("sending file(s) to '%s'", self.name)
        if username is None:
            username = self.username
        if password is None:
            password = self.password
        client = self.params.get("file_transfer_client", "scp")
        address = self.get_public_address()
        port = self.get_ssh_port()
        log_filename = ("transfer-%s-to-%s-%s.log" %
                        (self.name, address,
                         utils_misc.generate_random_string(4)))
        remote.copy_files_to(address, client, username, password, port,
                             host_path, guest_path, limit, log_filename,
                             verbose, timeout)
        utils_misc.close_log_file(log_filename)

    def copy_files_from(self, guest_path, host_path, nic_index=0, limit="",
                        verbose=False,
                        timeout=g.COPY_FILES_TIMEOUT,
                        username=None, password=None):
        """
        Transfer files from the guest.
        :param username: VM username
        :param password: VM password
        :param host_path: Guest path
        :param guest_path: Host path
        :param limit: Speed limit of file transfer.
        :param verbose: If True, log some stats using logging.info (RSS only)
        :param timeout: Time (seconds) before giving up on doing the remote
                copy.
        """
        logging.info("receiving file(s) to '%s'", self.name)
        if username is None:
            username = self.username
        if password is None:
            password = self.password
        client = self.params.get("file_transfer_client", "scp")
        address = self.get_public_address()
        port = self.get_ssh_port()
        log_filename = ("transfer-%s-from-%s-%s.log" %
                        (self.name, address,
                         utils_misc.generate_random_string(4)))
        remote.copy_files_from(address, client, username, password, port,
                               guest_path, host_path, limit, log_filename,
                               verbose, timeout)
        utils_misc.close_log_file(log_filename)

    def session_close(self):
        """
        Close current session.
        """
        try:
            self.session.close()
        except:
            pass

#    def wait_for_dns(self, dns, times=g.WAIT_FOR_START_RETRY_TIMES):
#        """
#
#        :param dns: VM Domain Name
#        :param times: Retry times of checking dns connection.
#        :return: False if ti
#        """
#        r = 0
#        interval = 10
#        while r < times:
#            #            logging.info(dns)
#            if utils_misc.check_dns(dns):
#                return True
#            time.sleep(interval)
#            r += 1
#            logging.info("Retry %d times.", r)
#        logging.info("After retry %d times, the DNS is not available.", times)
#        return False

    def get_device_name(self, times=g.WAIT_FOR_RETRY_TIMES):
        r = 0
        interval = 10
        disk = ''
        while r < times:
            disk = self.get_output("ls /dev/sd* | grep -v [1234567890]", sudo=False).split('\n')[-1]
            if disk not in ["/dev/sda", "/dev/sdb"]:
                break
            r += 1
            logging.info("Get device name retry %d times" % r)
            time.sleep(interval)
        if disk in ["/dev/sda", "/dev/sdb"]:
            logging.info("Fail to get the device name")
            return None
        else:
            return disk

    def _check_log(self, logfile, ignore_list, additional_ignore_list=None, sudo=True):
        if additional_ignore_list:
            ignore_list += additional_ignore_list
        if ignore_list:
            cmd = "cat {0} | grep -iE '(error|fail)' | grep -vE '({1})'".format(logfile, '|'.join(ignore_list))
        else:
            cmd = "cat {0} | grep -iE '(error|fail)'".format(logfile)
        return self.get_output(cmd, sudo=sudo)

    def check_messages_log(self, additional_ignore_list=None):
        return self._check_log("/var/log/messages", MESSAGES_IGNORELIST, additional_ignore_list)

    def get_pid(self, process_key):
        """
        Return process pid according to the process_key string
        :param process_key: The process key string
        :return: pid
        """
        pid = self.get_output("ps aux|grep -E '({0})'|grep -v grep|tr -s ' '".format(process_key))
        if pid == "":
            return None
        else:
            pid = pid.split(' ')[1]
            logging.info("PID: {0}".format(pid))
            return pid

    def file_exists(self, filename, is_folder=False):
        """
        Check if file exists inside VM.
        :param filename: The file fullpath inside the VM
        :param is_folder: If the filename is a folder, set True; If it is a file, set False
        :return: True/False
        """
        option = "d" if is_folder else "f"
        ret = self.get_output("if [ -{1} {0} ];then echo 'yes';else echo 'no';fi".format(filename, option))
        return True if ret == 'yes' else False
