#!/usr/bin/env python3

import sys
import os
import yaml
import json
import re
import base64
from os import path

config = {}

def main(argv):
    if len(argv) < 2:
        print("Usage: %s <main.yml> [config.yaml]" % argv[0])
        exit(1)

    main_file = argv[1]

    if len(argv) >= 3:
        with open(argv[2]) as file:
            global config
            config = yaml.load(file)

    root_obj = fn_process_file(path.dirname(main_file), path.basename(main_file))
    print(json.dumps(root_obj))

def process_object(cwd, obj):
    if isinstance(obj, dict):
        for key in obj:
            if key in func_map:
                return func_map[key](cwd, obj[key])
            else:
                obj[key] = process_object(cwd, obj[key])

    elif isinstance(obj, list):
        return [process_object(cwd, tmp) for tmp in obj]

    return obj


def fn_process_file(cwd, file_name):
    obj = {}

    try:
        with open(path.join(cwd, file_name)) as file:
            obj = yaml.load(file)
        obj = process_object(cwd, obj)

    except Exception as e:
        print("Error Processing %s" % path.join(cwd, file_name), file=sys.stderr)
        raise e

    return obj

def fn_from_folders(cwd, dirlist):
    if not isinstance(dirlist, list):
        return fn_from_folders(cwd, [dirlist])

    obj = {}
    for diritem in dirlist:
        curcwd = path.join(cwd, diritem)

        for file_name in os.listdir(curcwd):
            match = re.search(r'(.*)\.yaml$', file_name)
            if match:
                key = match.group(1)
                if key in obj:
                    raise ValueError("'%s' is already declared" % key)
                obj[key] = fn_process_file(curcwd, file_name)

    return obj

def fn_file_as_base64(cwd, file_name):
    file_name = path.join(cwd, file_name)
    with open(file_name, "rb") as file:
        return base64.b64encode(file.read()).decode("UTF-8")

def fn_get_config(cwd, conf_path):
    if not isinstance(conf_path, list):
        return fn_get_config(cwd, [conf_path])

    ret = config
    for key in conf_path:
        ret = ret[key]

    return ret

def fn_merge(cwd, listobj):
    obj = {}
    for item in listobj:
        item = process_object(cwd, item)
        for key in item:
            if key in obj:
                raise ValueError("'%s' is already declared" % key)
            obj[key] = item[key]

    return obj

def fn_concat(cwd, liststr):
    liststr = [process_object(cwd, item) for item in liststr]
    return "".join(liststr)


func_map = {
    "TVLK::Fn::FromFile": fn_process_file,
    "TVLK::Fn::FromFolders": fn_from_folders,
    "TVLK::Fn::FileAsBase64": fn_file_as_base64,
    "TVLK::Fn::GetConfig": fn_get_config,
    "TVLK::Fn::Merge": fn_merge,
    "TVLK::Fn::Concat": fn_concat
}


if __name__ == '__main__':
    main(sys.argv)
