#!/usr/bin/python3
"""
Syncs bootstrap site to s3 bucket without extensions, invalidates
Cloudfront. Can be run both interactively and through a CircleCI CI/CD system
"""

import sys
import subprocess
import os
import shutil
import glob

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
DIST_DIR = os.path.join(ROOT_DIR, "dist")

def main():
    output_code = 0
    # Sync s3 bucket from jekyll build
    if 's3_bucket' in os.environ:
        bucket_name = os.environ['s3_bucket']
        output_code += deploy_to_s3_without_html_extensions(bucket_name)
    else:
        bucket_name = "bearcyclegame.com" 
        response = input("Sync s3 bucket with dist/*? (y/n)")
        if 'y' in response:
            output_code += deploy_to_s3_without_html_extensions(bucket_name)
    if output_code != 0:
        return output_code

    # Invalidate cloudfront to update actual site
    if 'cloudfront_distribution_id' in os.environ:
        dist_id = os.environ['cloudfront_distribution_id']
        output_code += invalidate_cloudfront(dist_id)
    else:
        response = input("Invalidate Cloudfront? (y/n) ")
        if 'y' in response:
            try:
                from _cloudfront_mappings import cloudfront_mappings
                dist_id = cloudfront_mappings[bucket_name]
                output_code += invalidate_cloudfront(dist_id)
            except Exception:
                dist_id = input("Enter Cloudfront Distribution ID: ")
                output_code += invalidate_cloudfront(dist_id)
    
    return output_code

def deploy_to_s3_without_html_extensions(bucket_name):
        output_code = 0

        output_code += run_shell_command(
            f'aws s3 sync --delete {DIST_DIR} s3://{bucket_name}')
        return output_code

def invalidate_cloudfront(dist_id):
    return run_shell_command(
            f"aws cloudfront create-invalidation " + \
            f"--distribution-id {dist_id} " + \
            f"--paths '/*'")

def run_shell_command(cmd):
    try:
        print("Currently running command '{}'".format(cmd))
        byte_output = subprocess.check_output(cmd,
                                              stderr=subprocess.STDOUT,
                                              shell=True)
        str_output = byte_output.decode("utf-8")
        print(f"output of command: {str_output}\n-----")
        return 0
    except subprocess.CalledProcessError as e:
        print("cmd failed, returned non-zero code. Output:\n"\
                 "{}".format(e.output.decode("utf-8")))
        return -1

if __name__ == "__main__":
    sys.exit(main())
