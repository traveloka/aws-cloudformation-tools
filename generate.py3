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

    root_obj = process_file(path.dirname(main_file), path.basename(main_file))
    print(json.dumps(root_obj))


def process_file(cwd, file_name):
    obj = {}

    with open(path.join(cwd, file_name)) as file:
        obj = yaml.load(file)

    try:
        obj = process_object(cwd, obj)
    except Exception as e:
        print("Error Processing %s" % path.join(cwd, file_name), file=sys.stderr)
        raise e

    return obj


def process_object(cwd, obj):
    if isinstance(obj, dict):
        for key in obj.keys():
            if key in func_map:
                return func_map[key](cwd, obj[key])
            else:
                obj[key] = process_object(cwd, obj[key])

    elif isinstance(obj, list):
        return [process_object(cwd, tmp) for tmp in obj]

    return obj


def fn_from_folders(cwd, dirname):
    if not isinstance(dirname, list):
        return fn_from_folders(cwd, [dirname])

    obj = {}
    for diritem in dirname:
        curcwd = path.join(cwd, diritem)

        for file_name in os.listdir(curcwd):
            match = re.search(r'(.*)\.yaml$', file_name)
            if match and path.isfile(path.join(curcwd, file_name)):
                key = match.group(1)
                obj[key] = process_file(curcwd, file_name)

    return obj

def fn_file_as_base64(cwd, file_name):
    file_name = path.join(cwd, file_name)
    if path.isfile(file_name):
        with open(file_name, "rb") as file:
            return base64.b64encode(file.read()).decode("UTF-8")
    else:
        raise ValueError("%s is not a file" % file_name)

def fn_get_config(cwd, conf_path):
    if not isinstance(conf_path, list):
        return fn_get_config(cwd, [conf_path])

    ret = config
    for key in conf_path:
        ret = ret[key]

    return ret

func_map = {
    "TVLK::Fn::FromFolder": fn_from_folders,
    "TVLK::Fn::FromFolders": fn_from_folders,
    "TVLK::Fn::FileAsBase64": fn_file_as_base64,
    "TVLK::Fn::GetConfig": fn_get_config
}

if __name__ == '__main__':
    main(sys.argv)
