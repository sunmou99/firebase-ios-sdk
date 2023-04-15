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
  
  merged_branch = os.path.expanduser(args.merged_branch)
  base_branch = os.path.expanduser(args.base_branch)
  
  new_api_json = json.load(open(os.path.join(merged_branch, "api_data.json")))
  old_api_json = json.load(open(os.path.join(base_branch, "api_data.json")))  # Replace with the second JSON object you want to compare

  diff = generate_diff(new_api_json, old_api_json)
  print(json.dumps(diff, indent=2))
  print(generate_text_report(diff))
  print(generate_markdown_report(diff))


def generate_diff(new_api_json, old_api_json, level=0):
  diff = {}
  for api_name in set(new_api_json.keys()).union(old_api_json.keys()):
    if api_name not in old_api_json:
      diff[api_name] = new_api_json[api_name]
      diff[api_name]["status"] = "added"
    elif api_name not in new_api_json:
      diff[api_name] = old_api_json[api_name]
      diff[api_name]["status"] = "removed"
    elif "declaration" in new_api_json[api_name] and new_api_json[api_name]["declaration"] != old_api_json[api_name]["declaration"]:
      diff[api_name] = new_api_json[api_name]
      diff[api_name]["declaration"].append(old_api_json[api_name]["declaration"])
      diff[api_name]["status"] = "modified"
    elif level == 0 or level == 1:
      key = "apis" if level == 0 else "sub_apis"
      child_diff = generate_diff(new_api_json[api_name][key], old_api_json[api_name][key], level + 1)
      if child_diff:
        diff[api_name] = {("apis" if level == 0 else "sub_apis"): child_diff}

  return diff

def generate_text_report(diff, indent=0):
    report = ""
    indent_str = "  " * indent

    for api_type, api_data in diff.items():
      if "status" in api_data:
        report += f"{indent_str}{api_data['status']}:\n"
      
      report += f"{indent_str}  {api_type}:\n"
      
      if "apis" in api_data:
        report += generate_text_report(api_data["apis"], indent + 1)
      elif "sub_apis" in api_data:
        report += generate_text_report(api_data["sub_apis"], indent + 1)
      elif "declaration" in api_data:
        for declaration in api_data["declaration"]:
          report += f"{indent_str}    {declaration}\n"

    return report


def generate_markdown_report(diff, indent=0):
  report = ""
  indent_str = "  " * indent

  for api_type, api_data in diff.items():
    if "status" in api_data:
      report += f"{indent_str}{api_data['status']}:\n"

    report += f"{indent_str}**{api_type}**:\n"
    
    if "apis" in api_data:
      report += generate_markdown_report(api_data["apis"], indent + 1)
    elif "sub_apis" in api_data:
      report += generate_markdown_report(api_data["sub_apis"], indent + 1)
    elif "declaration" in api_data:
      for declaration in api_data["declaration"]:
        report += f"{indent_str}  - `{declaration}`\n"

  return report


def parse_cmdline_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-m', '--merged_branch')
  parser.add_argument('-b', '--base_branch')

  args = parser.parse_args()
  return args


if __name__ == '__main__':
  main()