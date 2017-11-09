import os
import ConfigParser
import logging
import json
import yaml

from aliyunsdkcore.client import AcsClient

ALIYUNCLI = "{0}/.aliyuncli".format(os.path.expanduser('~'))
CONFIGURE = "{0}/configure".format(ALIYUNCLI)
CREDENTIALS = "{0}/credentials".format(ALIYUNCLI)
OSSUTILCONFIG = "{0}/.ossutilconfig".format(os.path.expanduser('~'))

#config = ConfigParser.ConfigParser()
#config.read(CREDENTIALS)
#config.read(CONFIGURE)
#access_key_id = config.get(config.sections()[0], "aliyun_access_key_id")
#access_key_secret = config.get(config.sections()[0], "aliyun_access_key_secret")
#region = config.get(config.sections()[0], "region")

REALPATH = os.path.split(os.path.realpath(__file__))[0]
# Get access_key_id, access_key_secret, region from common.yaml
common_yaml = REALPATH + "/../../../cfg/common.yaml"
with open(common_yaml) as f:
    data = yaml.load(f.read())
access_key_id = data.get("CloudSub").get("aliyun_access_key_id")
access_key_secret = data.get("CloudSub").get("aliyun_access_key_secret")
region = data.get("Region").get("id")

clt = AcsClient(access_key_id, access_key_secret, region)

import aliyunsdkecs.request.v20140526
module_path = aliyunsdkecs.request.v20140526.__path__[0]
del aliyunsdkecs.request.v20140526

for module in os.listdir(module_path):
    try:
        name, postfix = module.split('.')
    except:
        continue
    if postfix == 'py' and name != "__init__":
        exec("from aliyunsdkecs.request.v20140526.{0} import {0}".format(name))


def _send_request(request):
    request.set_accept_format('json')
    try:
        logging.debug("Run: {0}".format(request.__class__.__name__))
        response_str = clt.do_action_with_exception(request)
#        logging.info(response_str)
        response_detail = json.loads(response_str)
        return response_detail
    except Exception as e:
        logging.error(e)


def _add_params(request, key_list=None, params=None):
    print "==== Query Params ===="
    if params is None:
        print "None"
        return request
    if key_list:
        for key in key_list:
            if params.get(key) is not None:
                value = params.get(key)
                if "Ids" in key or \
                   "Names" in key:
                    value = str(value.split(',')).replace('\'', '"')
                eval("request.set_{0}('{1}')".format(key, value))
    print request.get_query_params()
    return request


# Instance
def describe_instances(params=None):
    request = DescribeInstancesRequest()
    key_list = ["InstanceName",
                "InstanceIds"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def create_instance(params):
    request = CreateInstanceRequest()
    key_list = ["InstanceChargeType",
                "ImageId",
                "InstanceType",
                "InternetChargeType",
                "SecurityGroupId",
                "VSwitchId",
                "KeyPairName",
                "SystemDiskCategory",
                "HostName",
                "InstanceName",
                "InternetMaxBandwidthOut",
                "InternetMaxBandwidthIn",
                "RegionId",
                "ZoneId"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def start_instance(params):
    request = StartInstanceRequest()
    key_list = ["InstanceId"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def stop_instance(params):
    request = StopInstanceRequest()
    key_list = ["InstanceId",
                "ForceStop"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def reboot_instance(params):
    request = RebootInstanceRequest()
    key_list = ["InstanceId",
                "ForceStop"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def delete_instance(params):
    request = DeleteInstanceRequest()
    key_list = ["InstanceId"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def describe_instance_attribute(params):
    request = DescribeInstanceAttributeRequest()
    key_list = ["InstanceId"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def modify_instance_spec(params):
    request = ModifyInstanceSpecRequest()
    key_list = ["InstanceId",
                "InstanceType",
                "InternetMaxBandwidthIn",
                "InternetMaxBandwidthOut"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


# Public IP
def allocate_public_ip_address(params):
    request = AllocatePublicIpAddressRequest()
    key_list = ["InstanceId"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


# KeyPair
def describe_keypairs(params):
    request = DescribeKeyPairsRequest()
    key_list = ["KeyPairName",
                "RegionId"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def create_keypair(params):
    request = CreateKeyPairRequest()
    key_list = ["KeyPairName",
                "RegionId"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def import_keypair(params):
    request = ImportKeyPairRequest()
    key_list = ["KeyPairName",
                "RegionId",
                "PublicKeyBody"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def delete_keypair(params):
    request = DeleteKeyPairsRequest()
    key_list = ["KeyPairNames",
                "RegionId"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


# Image
def describe_images(params):
    request = DescribeImagesRequest()
    key_list = ["ImageName",
                "ImageId"]
    request = _add_params(request, key_list, params)
    return _send_request(request)


def create_image(params):
    request = CreateImageRequest()
    key_list = ["ImageName",
                "SnaoshotId",
                "Platform"]
    request = _add_params(request, key_list, params)
    return _send_request(request)
