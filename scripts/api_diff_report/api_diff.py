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


def generate_diff(json_new, json_old):
  diff_report = {}

  for api_type, api_data in json_old.items():
    api_type_diff = {"apis": {}}

    for api_name, api_info in api_data["apis"].items():
      api_diff = {}

      # Compare API declaration
      old_declaration = set(api_info["declaration"])
      new_declaration = set(json_new[api_type]["apis"][api_name]["declaration"])

      if old_declaration != new_declaration:
        api_diff["declaration"] = {
          "removed": list(old_declaration - new_declaration),
          "added": list(new_declaration - old_declaration)
        }

      # Compare sub-APIs
      old_sub_apis = api_info["sub_apis"]
      new_sub_apis = json_new[api_type]["apis"][api_name]["sub_apis"]
      common_sub_apis = set(old_sub_apis.keys()) & set(new_sub_apis.keys())

      sub_apis_diff = {}

      for sub_api in common_sub_apis:
        old_declaration = set(old_sub_apis[sub_api])
        new_declaration = set(new_sub_apis[sub_api])

        if old_declaration != new_declaration:
          sub_apis_diff[sub_api] = {
            "removed": list(old_declaration - new_declaration),
            "added": list(new_declaration - old_declaration)
          }

      # Check for removed sub-APIs
      removed_sub_apis = set(old_sub_apis.keys()) - set(new_sub_apis.keys())
      for removed_sub_api in removed_sub_apis:
        sub_apis_diff[removed_sub_api] = {
          "removed": old_sub_apis[removed_sub_api]
        }

      # Check for added sub-APIs
      added_sub_apis = set(new_sub_apis.keys()) - set(old_sub_apis.keys())
      for added_sub_api in added_sub_apis:
        sub_apis_diff[added_sub_api] = {
          "added": new_sub_apis[added_sub_api]
        }

      if sub_apis_diff:
        api_diff["sub_apis"] = sub_apis_diff

      if api_diff:
        api_type_diff["apis"][api_name] = api_diff

    if api_type_diff["apis"]:
      diff_report[api_type] = api_type_diff

  return diff_report


def print_diff_report_text(diff_report):
    if not diff_report:
      print("No differences found.")
      return

    text_output = []
    for api_type, api_data in diff_report.items():
      text_output.append(f"{api_type}")

      for api_name, api_info in api_data["apis"].items():
        text_output.append(f"  {api_name}")
        if "declaration" in api_info:
          for status, declarations in api_info["declaration"].items():
            for declaration in declarations:
              text_output.append(f"      *{status}*: {declaration}")

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