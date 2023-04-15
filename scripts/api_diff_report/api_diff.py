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
  
  merged_branch = os.path.expanduser(args.merged_branch)
  base_branch = os.path.expanduser(args.base_branch)
  
  new_api_json = json.load(open(os.path.join(merged_branch, "api_data.json")))
  old_api_json = json.load(open(os.path.join(base_branch, "api_data.json")))  # Replace with the second JSON object you want to compare

  diff = generate_diff(new_api_json, old_api_json)
  print(json.dumps(diff, indent=2))
  print(print_diff_report_text(diff))
  print(print_diff_report_markdown(diff))


def generate_diff(new_api_json, old_api_json):
  diff = {}
  for api_type in set(new_api_json.keys()).union(old_api_json.keys()):
    if api_type not in old_api_json:
      diff[api_type] = new_api_json[api_type]
      diff[api_type]["status"] = "added"
    elif api_type not in new_api_json:
      diff[api_type] = old_api_json[api_type]
      diff[api_type]["status"] = "removed"
    else:
      child_diff = generate_diff_1(new_api_json[api_type]["apis"], old_api_json[api_type]["apis"])
      if child_diff:
        diff[api_type] = {"apis": child_diff}

  return diff

def generate_diff_1(new_api_json, old_api_json):
  diff = {}
  for api_name in set(new_api_json.keys()).union(old_api_json.keys()):
    if api_name not in old_api_json:
      diff[api_name] = new_api_json[api_name]
      diff[api_name]["status"] = "added"
    elif api_name not in new_api_json:
      diff[api_name] = old_api_json[api_name]
      diff[api_name]["status"] = "removed"
    elif new_api_json[api_name]["declaration"] != old_api_json[api_name]["declaration"]:
      diff[api_name] = new_api_json[api_name]
      diff[api_name]["declaration"].append(old_api_json[api_name]["declaration"])
      diff[api_name]["status"] = "modified"
    else:
      child_diff = generate_diff_2(new_api_json[api_name]["sub_apis"], old_api_json[api_name]["sub_apis"])
      if child_diff:
        diff[api_name] = {"sub_apis": child_diff}

  return diff


def generate_diff_2(new_api_json, old_api_json):
  diff = {}
  for sub_api_name in set(new_api_json.keys()).union(old_api_json.keys()):
    if sub_api_name not in old_api_json:
      diff[sub_api_name] = new_api_json[sub_api_name]
      diff[sub_api_name]["status"] = "added"
    elif sub_api_name not in new_api_json:
      diff[sub_api_name] = old_api_json[sub_api_name]
      diff[sub_api_name]["status"] = "removed"
    elif new_api_json[sub_api_name]["declaration"] != old_api_json[sub_api_name]["declaration"]:
      diff[sub_api_name] = new_api_json[sub_api_name]
      diff[sub_api_name]["declaration"].append(old_api_json[sub_api_name]["declaration"])
      diff[sub_api_name]["status"] = "modified"

  return diff


def print_diff_report_text(diff_report):
    if not diff_report:
      print("No differences found.")
      return

    text_output = []
    for api_type, api_data in diff_report.items():
      text_output.append(f"{api_type}")

      for api_name, api_info in api_data["apis"].items():
        if "declaration" in api_info:
          for status, declarations in api_info["declaration"].items():
            text_output.append(f"  *{status}*: {api_name}")
            for declaration in declarations:
              text_output.append(f"    {declaration}")

        if "sub_apis" in api_info:
          for sub_api_name, sub_api_diff in api_info["sub_apis"].items():
            for status, declarations in sub_api_diff.items():
              text_output.append(f"    *{status}*: {sub_api_name}")
              for declaration in declarations:
                text_output.append(f"        {declaration}")

    return "\n".join(text_output)


def print_diff_report_markdown(diff_report):
  if not diff_report:
    print("No differences found.")
    return

  markdown_output = []
  for api_type, api_data in diff_report.items():
    markdown_output.append(f"### {api_type}")

    for api_name, api_info in api_data["apis"].items():
      markdown_output.append(f"#### `{api_name}`")
      if "declaration" in api_info:
        markdown_output.append("##### Declaration changed:")
        for status, declarations in api_info["declaration"].items():
          for declaration in declarations:
            markdown_output.append(f"- **{status}**: `{declaration}`")

      if "sub_apis" in api_info:
        for sub_api_name, sub_api_diff in api_info["sub_apis"].items():
          for status, declarations in sub_api_diff.items():
            markdown_output.append(f"###### **{status}**: `{sub_api_name}`")
            for declaration in declarations:
              markdown_output.append(f" - `{declaration}`")

  return "\n".join(markdown_output)


def parse_cmdline_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-m', '--merged_branch')
  parser.add_argument('-b', '--base_branch')

  args = parser.parse_args()
  return args


if __name__ == '__main__':
  main()