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

KEY_KIND = {
  "source.lang.swift.decl.function.method.instance": "",
  "source.lang.swift.decl.function.method.static": "static"
}

def main():
  logging.getLogger().setLevel(logging.INFO)

  args = parse_cmdline_args()
  logging.info(args)
  
  merged_branch = os.path.expanduser(args.merged_branch)
  base_branch = os.path.expanduser(args.base_branch)
  
  for file_name in os.listdir(merged_branch):
    logging.info(f"\n\nDetect API changes in {file_name}")
    merged_file = os.path.join(merged_branch, file_name)
    base_file = os.path.join(base_branch, file_name)
    api_diff(merged_file, base_file)



def api_diff(merged_file, base_file):
  file_extension = merged_file.split(".")[1]
  if file_extension == OBJC_EXTENSION:
    pr_apis = get_objc_public_apis(json.load(open(merged_file)))
    base_apis = get_objc_public_apis(json.load(open(base_file)))

    pr_only_apis = get_objc_diff(pr_apis, base_apis)
    base_only_apis = get_objc_diff(base_apis, pr_apis)
    logging.info("Added APIs")
    print_objc_diff(pr_only_apis)
    logging.info("\nRemoved APIS")
    print_objc_diff(base_only_apis)
  elif file_extension == SWIFT_EXTENSION:
    pr_apis = get_swift_public_apis(json.load(open(merged_file)))
    base_apis = get_swift_public_apis(json.load(open(base_file)))

    pr_only_apis = get_swift_diff(pr_apis, base_apis)
    base_only_apis = get_swift_diff(base_apis, pr_apis)
    logging.info("Added APIs")
    print_swift_diff(pr_only_apis)
    logging.info("\nRemoved APIS")
    print_swift_diff(base_only_apis)


def get_swift_public_apis(api_json):
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


def get_swift_diff(target, base):
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


def print_swift_diff(diff):
  for c in diff["class"]:
    logging.info(f'{c["key.name"]}')
  for f in diff["function"]:
    logging.info(f'Function: public {KEY_KIND[f["key.kind"]]} func {f["key.name"]} -> {f["key.typename"]}')


def get_objc_public_apis(api_json):
  for key, value in api_json[0].items():
    return value["key.substructure"]


def get_objc_diff(target, base):
  diff = {"class":[], "function":[]}

  for tc in target:
    for bc in base:
      # check for same public classes
      if tc["key.kind"] == bc["key.kind"] and tc["key.name"] == bc["key.name"] and tc["key.parsed_declaration"] == bc["key.parsed_declaration"]:
        # check for same public functions
        if "key.substructure" in tc:
          for tf in tc["key.substructure"]:
            for bf in bc["key.substructure"]:
              if tf["key.kind"] == bf["key.kind"] and tf["key.name"] == bf["key.name"] and tf["key.parsed_declaration"] == bf["key.parsed_declaration"]:
                break
            else:
              diff["function"].append(tf)
        break
    else:
      diff["class"].append(tc)
  return diff


def print_objc_diff(diff):
  for c in diff["class"]:
    logging.info(f'Class: {c["key.kind"]} {c["key.name"]}')
  for f in diff["function"]:
    logging.info(f'OBJC Function: {f["key.parsed_declaration"]}')
  for f in diff["function"]:
    if "key.swift_declaration" in f:
      logging.info(f'SWIFT Function: {f["key.swift_declaration"]}')


def parse_cmdline_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-m', '--merged_branch')
  parser.add_argument('-b', '--base_branch')

  args = parser.parse_args()
  return args


if __name__ == '__main__':
  main()