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

OBJC_EXTENSION = "h"
SWIFT_EXTENSION = "swift"

def main():
  logging.getLogger().setLevel(logging.INFO)

  args = parse_cmdline_args()
  logging.info(args)
  
  merged_branch = os.path.expanduser(args.merged_branch)
  base_branch = os.path.expanduser(args.base_branch)
  
  # for file_name in os.listdir(merged_branch):
  #   logging.info(file_name)
  #   merged_file = os.path.join(merged_branch, file_name)
  #   base_file = os.path.join(base_branch, file_name)
  #   api_diff(merged_file, base_file)



def api_diff(merged_file, base_file):
  # result = subprocess.run(
  #         args=["git", "diff", "--no-index", "--word-diff", merged_file, base_file],
  #         capture_output=True,
  #         text=True, 
  #         check=False)
  # logging.info(result.stdout)
  # logging.info("------------")
  file_extension = merged_file.split(".")[1]
  print(file_extension)
  pr_apis = get_public_apis(json.load(open(merged_file)), file_extension)
  # print(json.dumps(pr_apis, indent=2))
  base_apis = get_public_apis(json.load(open(base_file)), file_extension)
  # print(json.dumps(base_apis, indent=2))

  pr_only_apis = get_diff(pr_apis, base_apis)
  base_only_apis = get_diff(base_apis, pr_apis)
  print("pr_only_apis")
  print_diff(pr_only_apis)
  print("base_only_apis")
  print_diff(base_only_apis)

def get_public_apis(api_json, file_extension):
  if file_extension == OBJC_EXTENSION:
    for _, value in api_json[0].items():
      return value["key.substructure"]["key.substructure"]
  elif file_extension == SWIFT_EXTENSION:
    # key: file name
    # value: all classes and functions
    # only one key, value pair
    for key, value in api_json.items():
      # filter out non-public classes
      public_apis = [sc for sc in value["key.substructure"] if "key.accessibility" in sc and sc["key.accessibility"] == "source.lang.swift.accessibility.public"]
      for sc in public_apis:
        # filter out non-public functions
        sc["key.substructure"] = [f for f in sc["key.substructure"] if "key.accessibility" in f and f["key.accessibility"] == "source.lang.swift.accessibility.public"]
    return public_apis


def get_diff(target, base):
  diff = {"class":[], "function":[]}

  for tc in target:
    for bc in base:
      # check for same public classes
      if tc["key.kind"] == bc["key.kind"] and tc["key.name"] == bc["key.name"]:
        # check for same public functions
        for tf in tc["key.substructure"]:
          if "key.typename" in tf:
            for bf in bc["key.substructure"]:
              if tf["key.kind"] == bf["key.kind"] and tf["key.name"] == bf["key.name"] and tf["key.typename"] == bf["key.typename"]:
                break
            else:
              diff["function"].append(tf)
        break
    else:
      diff["class"].append(tc)
  return diff


def print_diff(diff):
  for c in diff["class"]:
    logging.info(f'Class {c["key.kind"]} {c["key.name"]}')
  for f in diff["function"]:
    logging.info(f'Function {f["key.kind"]} {f["key.name"]} {f["key.typename"]}')


def parse_cmdline_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-m', '--merged_branch')
  parser.add_argument('-b', '--base_branch')

  args = parser.parse_args()
  return args


if __name__ == '__main__':
  main()