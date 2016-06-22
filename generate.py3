#!/usr/bin/env python3

import sys
import os
import yaml
import json
import re
import base64
import boto3
from os import path

config = {}

_cf_client = None
def get_cf_client():
    global _cf_client
    if _cf_client == None:
        _cf_client = boto3.client('cloudformation')
    return _cf_client


def main(argv):
    if len(argv) < 2:
        print("Usage: %s <main.yml> [config.yaml]" % argv[0])
        exit(1)

    main_file = argv[1]

    if len(argv) >= 3:
        global config
        with open(argv[2]) as file:
            config = yaml.load(file)
        config = process_object(path.dirname(argv[2]), config)

    root_obj = fn_process_file(path.dirname(main_file), path.basename(main_file))
    print(json.dumps(root_obj))

def process_object(cwd, obj):
    if isinstance(obj, dict):
        ret = {}
        for key in obj:
            if key in func_map:
                return func_map[key](cwd, obj[key])
            else:
                ret[key] = process_object(cwd, obj[key])
        return ret

    if isinstance(obj, list):
        return [process_object(cwd, tmp) for tmp in obj]

    return obj


def fn_process_file(cwd, file_name):
    try:
        ret = {}
        with open(path.join(cwd, file_name)) as file:
            ret = yaml.load(file)
        ret = process_object(cwd, ret)
        return ret

    except Exception as e:
        print("Error Processing %s" % path.join(cwd, file_name), file=sys.stderr)
        raise e

def fn_from_folders(cwd, dir_list):
    if not isinstance(dir_list, list):
        return fn_from_folders(cwd, [dir_list])

    ret = {}
    for diritem in dir_list:
        curcwd = path.join(cwd, diritem)

        for file_name in os.listdir(curcwd):
            match = re.search(r'(.*)\.yaml$', file_name)
            if match:
                key = match.group(1)
                if key in ret:
                    raise ValueError("'%s' is already declared" % key)
                ret[key] = fn_process_file(curcwd, file_name)

    return ret

def fn_file_as_base64(cwd, file_name):
    file_name = path.join(cwd, file_name)
    with open(file_name, "rb") as file:
        return base64.b64encode(file.read()).decode("UTF-8")

def fn_get_config(cwd, key_path):
    if not isinstance(key_path, list):
        return fn_get_config(cwd, [key_path])

    ret = config
    for key in key_path:
        ret = ret[key]

    return ret

def fn_merge(cwd, obj_list):
    ret = {}
    for item in obj_list:
        item = process_object(cwd, item)
        for key in item:
            if key in ret:
                raise ValueError("'%s' is already declared" % key)
            ret[key] = item[key]

    return ret

def fn_merge_list(cwd, list_list):
    ret = []
    for item in list_list:
        ret.extend(process_object(cwd, item))

    return ret

def fn_concat(cwd, item_list):
    item_list = [process_object(cwd, item) for item in item_list]
    return "".join(item_list)

def fn_awscf_get_stack_resource(cwd, argv):
    cf_client = get_cf_client()
    ret = cf_client.describe_stack_resource(
        StackName=argv[0],
        LogicalResourceId=argv[1]
    )
    status = ret["StackResourceDetail"]["ResourceStatus"]
    if status not in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
        raise ValueError(
            "Resource %s in stack %s not in valid state" % (argv[1], argv[0])
        )

    return ret["StackResourceDetail"]["PhysicalResourceId"]

def fn_if(cwd, argv):
    cond = process_object(cwd, argv[0])
    if(type(cond) != type(True)):
        raise ValueError("condition must be 'True' or 'False'")
    if cond:
        return process_object(cwd, argv[1])
    else:
        return process_object(cwd, argv[2])

def fn_equals(cwd, argv):
    return process_object(cwd, argv[0]) == process_object(cwd, argv[1])

def fn_and(cwd, argv):
    cond1 = process_object(cwd, argv[0])
    cond2 = process_object(cwd, argv[1])
    if(type(cond1) != type(True) or type(cond2) != type(True)):
        raise ValueError("condition must be 'True' or 'False'")
    return cond1 and cond2

def fn_or(cwd, argv):
    cond1 = process_object(cwd, argv[0])
    cond2 = process_object(cwd, argv[1])
    if(type(cond1) != type(True) or type(cond2) != type(True)):
        raise ValueError("condition must be 'True' or 'False'")
    return cond1 or cond2

def fn_not(cwd, arg):
    cond = process_object(cwd, arg)
    if(type(cond) != type(True)):
        raise ValueError("condition must be 'True' or 'False'")
    return not cond


func_map = {
    "TVLK::Fn::FromFile": fn_process_file,
    "TVLK::Fn::FromFolders": fn_from_folders,
    "TVLK::Fn::FileAsBase64": fn_file_as_base64,
    "TVLK::Fn::GetConfig": fn_get_config,
    "TVLK::Fn::Merge": fn_merge,
    "TVLK::Fn::MergeList": fn_merge_list,
    "TVLK::Fn::Concat": fn_concat,

    "TVLK::Fn::If": fn_if,
    "TVLK::Fn::Equals": fn_equals,
    "TVLK::Fn::And": fn_and,
    "TVLK::Fn::Or": fn_or,
    "TVLK::Fn::Not": fn_not,

    "TVLK::Fn::AWSCFGetStackResource": fn_awscf_get_stack_resource
}


if __name__ == '__main__':
    main(sys.argv)
