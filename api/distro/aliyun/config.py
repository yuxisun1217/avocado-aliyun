"""
Wrappers for the Aliyuncli functions

:copyright: 2017 Red Hat Inc.
"""

import os
import sys
import ConfigParser

sys.path.append(os.path.join(sys.path[0], ".."))

ALIYUNCLI = "{0}/.aliyuncli".format(os.path.expanduser('~'))
CONFIGURE = "{0}/configure".format(ALIYUNCLI)
CREDENTIALS = "{0}/credentials".format(ALIYUNCLI)
OSSUTILCONFIG = "{0}/.ossutilconfig".format(os.path.expanduser('~'))

CONFIGURE_CONTENT = """\
[default]
output = json
region = %(region)s
"""

CREDENTIALS_CONTENT = """\
[default]
aliyun_access_key_secret = %(access_key_secret)s
aliyun_access_key_id = %(access_key_id)s
"""

OSSUTILCONFIG_CONTENT = """\
[Credentials]
language=CH
endpoint=oss-%(region)s.aliyuncs.com
accessKeyID=%(access_key_id)s
accessKeySecret=%(access_key_secret)s
"""


if not os.path.isdir(ALIYUNCLI):
    os.makedirs(ALIYUNCLI, 0755)


class UpdateConfig(object):
    def __init__(self, access_key_id=None, access_key_secret=None, region=None):
        self.config = dict()
        self.config["access_key_id"] = access_key_id
        self.config["access_key_secret"] = access_key_secret
        self.config["region"] = region

    def _get_value(self, conf_file, key):
        config = ConfigParser.ConfigParser()
        config.read(conf_file)
        if config.sections():
            return config.get(config.sections()[0], key)
        else:
            return None

    def _get_params(self):
        if not self.config["access_key_id"]:
            self.config["access_key_id"] = self._get_value(CREDENTIALS, "aliyun_access_key_id")
        if not self.config["access_key_secret"]:
            self.config["access_key_secret"] = self._get_value(CREDENTIALS, "aliyun_access_key_secret")
        if not self.config["region"]:
            self.config["region"] = self._get_value(CONFIGURE, "region")
        return

    def _write_file(self, file_var):
        with open(eval(file_var), 'w') as f:
            f.write(eval(file_var+"_CONTENT") % self.config)

    def update(self):
        self._get_params()
        self._write_file("CREDENTIALS")
        self._write_file("CONFIGURE")
        self._write_file("OSSUTILCONFIG")
        print("Update configurations finished.")

if __name__ == "__main__":
    c = UpdateConfig(region="cn-beijing")
    c.update()
