#!/usr/bin/env python3

import argparse
import boto3
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import yaml
from os import path

_s3_client = None
_cf_client = None

def get_s3_client():
    global _s3_client
    if _s3_client == None:
        _s3_client = boto3.client('s3')
    return _s3_client

def get_cf_client():
    global _cf_client
    if _cf_client == None:
        _cf_client = boto3.client('cloudformation')
    return _cf_client


tmpdir = path.join(tempfile.gettempdir(), "deploy-" + str(int(random.random() * 10000)))
generated_config = None
config = {}


def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("config", type=str, help="config.yaml to be used")
    parser.add_argument("-s", "--stack", type=str, default=None, help="which stack to deploy")

    argv = parser.parse_args(argv[1:])

    os.makedirs(tmpdir, exist_ok=True)
    try:
        global generated_config
        global config

        generated_config = path.join(tmpdir, "config.json")

        proc = subprocess.Popen([
            path.join(path.dirname(__file__), "generate.py"),
            "",
            generated_config,
            "--generate_config_only",
            "-c", argv.config
        ])
        proc.wait()

        if proc.returncode != 0:
            raise Exception("Cannot process config file")

        with open(generated_config) as file:
            config = yaml.load(file)

        if argv.stack == None:
            for stack in config['deploy']['stack']:
                deploy(stack)
        else:
            deploy(argv.stack)

    finally:
        shutil.rmtree(tmpdir)

def deploy(stack):
    stack_obj = config['deploy']['stack'][stack]

    if '_visited' not in stack_obj:
        stack_obj['_visited'] = False

    if stack_obj['_visited']:
        return

    stack_obj['_visited'] = True

    if 'ext_deps' in stack_obj:
        for tmp in stack_obj['ext_deps']:
            wait_stack_to_complete(tmp)

    if 'deps' in stack_obj:
        for tmp in stack_obj['deps']:
            deploy(tmp)

    if 'input' in stack_obj and 'name' in stack_obj:
        cf = get_cf_client()

        input_file = stack_obj['input']
        stack_name = stack_obj['name']

        stack_file = path.join(tmpdir, 'stack-' + stack_name)
        s3 = None
        stack_s3bucket = None
        stack_s3key = None

        if 's3_temp' in config['deploy']:
            s3 = get_s3_client()
            s3_temp = config['deploy']['s3_temp']
            match = re.search(r'^s3://(.*?)/(.*/)$', s3_temp)
            stack_s3bucket = match.group(1)
            stack_s3key = match.group(2) +  stack_name + ".json"

        print("Generating stack '%s'" % stack_name)
        proc = subprocess.Popen([
            path.join(path.dirname(__file__), "generate.py"),
            input_file,
            stack_file,
            "-c", generated_config
        ])
        proc.wait()

        if proc.returncode != 0:
            raise Exception("Cannot stack '%s'" % stack_name)

        if s3 != None:
            s3.upload_file(stack_file, stack_s3bucket, stack_s3key)

        cur_stack = None
        try:
            print("Getting current stack '%s' status" % stack_name)
            cur_stack = cf.describe_stacks(StackName=stack_name)
        except Exception:
            # possible error: stack does not exist
            pass

        if cur_stack == None:
            print("Creating stack '%s'" % stack_name)
            if s3 != None:
                cf.create_stack(
                    StackName=stack_name,
                    TemplateURL="https://s3.amazonaws.com/%s/%s" % (stack_s3bucket, stack_s3key),
                    Capabilities=['CAPABILITY_IAM'],
                )
            else:
                with open(stack_file) as file:
                    cf.create_stack(
                        StackName=stack_name,
                        TemplateBody=file.read(),
                        Capabilities=['CAPABILITY_IAM'],
                    )
        else:
            wait_stack_to_complete(stack_name, prev=cur_stack)
            print("Updating stack '%s'" % stack_name)
            try:
                if s3 != None:
                    cf.update_stack(
                        StackName=stack_name,
                        TemplateURL="https://s3.amazonaws.com/%s/%s" % (stack_s3bucket, stack_s3key),
                        Capabilities=['CAPABILITY_IAM'],
                    )
                else:
                    with open(stack_file) as file:
                        cf.update_stack(
                            StackName=stack_name,
                            TemplateBody=file.read(),
                            Capabilities=['CAPABILITY_IAM'],
                        )
            except Exception as e:
                # possible error: no updates are to be performed
                pass

        wait_stack_to_complete(stack_name)
        print("Stack '%s' deployed" % stack_name)
        print()

def wait_stack_to_complete(stack_name, prev=None):
    cf = get_cf_client()

    print("Waiting stack '%s' to complete" % stack_name)
    while True:
        if prev != None:
            cur_stack = prev
            prev = None
        else:
            cur_stack = cf.describe_stacks(StackName=stack_name)

        match = re.search(r'^.*_(PROGRESS|FAILED|COMPLETE)$', cur_stack['Stacks'][0]['StackStatus'])
        status = match.group(1)
        if status == "COMPLETE":
            return
        elif status == "FAILED":
            raise Exception("Stack '%s' is in failed state" % stack_name)

        time.sleep(10)

if __name__ == '__main__':
    main(sys.argv)
