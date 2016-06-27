#!/usr/bin/env python3

import argparse
import base64
import boto3
import json
import os
import re
import subprocess
import sys
import time
import yaml
from os import path

_cf_client = None
_ec2_client = None

def get_cf_client():
    global _cf_client
    if _cf_client == None:
        _cf_client = boto3.client('cloudformation')
    return _cf_client

def get_ec2_client():
    global _ec2_client
    if _ec2_client == None:
        _ec2_client = boto3.client('ec2')
    return _ec2_client


config = {}

class Options:
    retry = 0


def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("main", type=str, help="main.yaml as input file")
    parser.add_argument("output", type=str, help="output.json as output file")
    parser.add_argument("-c", "--config", type=str, default=None, help="config.yaml to be used")
    parser.add_argument("-r", "--retry", type=int, default=0,
        help="how many times it will retry to get external resource, retrying is done every 10 second",
    )
    parser.add_argument("--generate_config_only", action="store_true", default=False,
        help="Only parse config.yaml and output it"
    )

    argv = parser.parse_args(argv[1:])

    main_file = argv.main
    Options.retry = argv.retry

    if argv.config != None:
        try:
            global config
            with open(argv.config) as file:
                new_config = yaml.load(file)
            while True:
                config = new_config
                new_config = process_object(path.dirname(argv.config), config)
                if new_config == config:
                    break
        except Exception as e:
            raise Exception("Error on processing config file") from e

    root = None
    if not argv.generate_config_only:
        root = TVLK.FromFile(path.dirname(main_file), path.basename(main_file))
        root = json.dumps(root)
    else:
        root = json.dumps(config)

    with open(argv.output, 'w') as file:
        print(root, file=file)

def process_object(cwd, what):
    if isinstance(what, list):
        return [process_object(cwd, item) for item in what]

    if isinstance(what, dict):
        ret = {}
        for key in what:
            match = re.search(r'^TVLK::(.*)$', key)
            if match:
                if len(what) == 1:
                    return getattr(TVLK, match.group(1))(cwd, what[key])
                else:
                    raise Exception("function '%s' must not have sibling" % key)
            else:
                ret[key] = process_object(cwd, what[key])
        return ret

    return what


class TVLK:
    def FromFile(cwd, file_name):
        try:
            ret = {}
            with open(path.join(cwd, file_name)) as file:
                ret = yaml.load(file)
            return process_object(cwd, ret)

        except Exception as e:
            raise Exception("Error Processing file '%s'" % path.join(cwd, file_name)) from e

    def FromFolder(cwd, folder):
        ret = {}
        cwd = path.join(cwd, folder)

        for file_name in os.listdir(cwd):
            match = re.search(r'^(.*)\.yaml$', file_name)
            if match:
                ret[match.group(1)] = TVLK.FromFile(cwd, file_name)

        return ret

    def Base64OfFile(cwd, file_name):
        file_name = path.join(cwd, file_name)
        with open(file_name, "rb") as file:
            return base64.b64encode(file.read()).decode("utf8")

    def Base64OfMakefileTarget(cwd, argv):
        makefile_dir = argv[0]
        makefile_target = argv[1]
        cwd = path.join(cwd, makefile_dir)
        proc = subprocess.Popen(["make", makefile_target], cwd=cwd)
        proc.wait()
        if proc.returncode != 0:
            raise Exception("Makefile failed to build target %s" % path.join(cwd, makefile_target))

        return TVLK.Base64OfFile(cwd, makefile_target)

    def Config(cwd, key_list):
        try:
            ret = config
            for key in key_list:
                ret = ret[key]

        except Exception as e:
            raise Exception("Cannot retrieve data from configuration") from e

        return ret

    def Merge(cwd, obj_list):
        ret = {}
        obj_list = process_object(cwd, obj_list)
        for item in obj_list:
            item = process_object(cwd, item)
            for key in item:
                if key in ret:
                    raise Exception("'%s' is already declared" % key)
                ret[key] = item[key]

        return ret

    def MergeList(cwd, list_list):
        ret = []
        for item in list_list:
            item = process_object(cwd, item)
            ret.extend(item)

        return ret

    def Select(cwd, argv):
        index = argv[0]
        collection = argv[1]
        return process_object(cwd, collection[index])

    def Concat(cwd, obj_list):
        obj_list = process_object(cwd, obj_list)
        return "".join(obj_list)

    def If(cwd, argv):
        cond = argv[0]
        result_true = argv[1]
        result_false = argv[2]
        if process_object(cwd, cond):
            return process_object(cwd, result_true)
        else:
            return process_object(cwd, result_false)

    def Equals(cwd, argv):
        obj1 = argv[0]
        obj2 = argv[1]
        return process_object(cwd, obj1) == process_object(cwd, obj2)

    def Not(cwd, cond):
        return not process_object(cwd, cond)

    def And(cwd, argv):
        cond1 = argv[0]
        cond2 = argv[1]
        return process_object(cwd, cond1) and process_object(cwd, cond2)


    def Or(cwd, argv):
        cond1 = argv[0]
        cond2 = argv[1]
        return process_object(cwd, cond1) or process_object(cwd, cond2)

    def CFStackResource(cwd, argv):
        stack = process_object(cwd, argv[0])
        logical_id = process_object(cwd, argv[1])

        cf = get_cf_client()
        attempt = 0

        while True:
            attempt = attempt + 1
            try:
                print("Geting resource '%s' in stack '%s'" % (logical_id, stack))
                ret = cf.describe_stack_resource(
                    StackName=stack,
                    LogicalResourceId=logical_id
                )
                ret = ret["StackResourceDetail"]
                if ret["ResourceStatus"] not in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
                    raise Exception("resource '%s' in stack %s is not ready" % (logical_id, stack) )
                return ret["PhysicalResourceId"]

            except Exception as e:
                if Options.retry >= 0 and attempt > Options.retry:
                    raise e
                else:
                    time.sleep(10)

    def EC2PublicIp(cwd, instance_id):
        instance_id = process_object(cwd, instance_id)
        ec2 = get_ec2_client()
        attempt = 0

        while True:
            attempt = attempt + 1
            try:
                print("Geting public ip of instance '%s'" % instance_id)
                ret = ec2_client.describe_instances(
                    InstanceIds=[instance_id]
                )
                ret = ret['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]
                return ret['Association']['PublicIp']

            except Exception as e:
                if Options.retry >= 0 and attempt > Options.retry:
                    raise e
                else:
                    time.sleep(10)

    def EC2PrivateIp(cwd, instance_id):
        instance_id = process_object(cwd, instance_id)
        ec2 = get_ec2_client()
        attempt = 0

        while True:
            attempt = attempt + 1
            try:
                print("Geting private ip of instance '%s'" % instance_id)
                ret = ec2_client.describe_instances(
                    InstanceIds=[instance_id]
                )
                ret = ret['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]
                return ret['PrivateIpAddress']

            except Exception as e:
                if Options.retry >= 0 and attempt > Options.retry:
                    raise e
                else:
                    time.sleep(10)

if __name__ == '__main__':
    main(sys.argv)
