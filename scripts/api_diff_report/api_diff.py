# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import argparse
import logging
import os 
import subprocess

def main():
  logging.getLogger().setLevel(logging.INFO)

  args = parse_cmdline_args()
  logging.info(args)
  
  merged_branch = os.path.expanduser(args.merged_branch)
  base_branch = os.path.expanduser(args.base_branch)
  
  for file_name in os.listdir(merged_branch):
    logging.info(file_name)
    merged_file = os.path.join(merged_branch, file_name)
    base_file = os.path.join(base_branch, file_name)
    result = subprocess.run(
            args=["git", "diff", "--no-index", "--word-diff", merged_file, base_file],
            capture_output=True,
            text=True, 
            check=False)
    logging.info(result.stdout)
    logging.info("------------")
    pr_api = json.load(open(merged_file))
    base_api = json.load(open(base_file))


def parse_cmdline_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-m', '--merged_branch')
  parser.add_argument('-b', '--base_branch')

  args = parser.parse_args()
  return args


if __name__ == '__main__':
  main()