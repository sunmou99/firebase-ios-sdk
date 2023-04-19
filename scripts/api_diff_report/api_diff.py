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
  
  new_api_json = json.load(open(os.path.join(merged_branch, "api_info.json")))
  old_api_json = json.load(open(os.path.join(base_branch, "api_info.json")))  # Replace with the second JSON object you want to compare

  diff = generate_diff(new_api_json, old_api_json)
  print(json.dumps(diff, indent=2))
  print(generate_text_report(diff))
  # print(generate_markdown_report(diff))


def generate_diff(new_api, old_api, level="module"):
  NEXT_LEVEL = {"module": "api_types", "api_types": "apis", "apis": "sub_apis"}
  next_level = NEXT_LEVEL.get(level)

  diff = {}
  for key in set(new_api.keys()).union(old_api.keys()):
    if key not in old_api:
      diff[key] = new_api[key]
      diff[key]["status"] = "added"
    elif key not in new_api:
      diff[key] = old_api[key]
      diff[key]["status"] = "removed"
    else:
      child_diff = generate_diff(new_api[key][next_level], old_api[key][next_level], level=next_level) if next_level else {}
      declaration_diff = new_api[key].get("declaration") != old_api[key].get("declaration") if level in ["apis", "sub_apis"] else False

      if not child_diff and not declaration_diff:
        continue
      
      diff[key] = new_api[key]
      if child_diff:
        diff[key][next_level] = child_diff
      if declaration_diff:
        diff[key]["status"] = "modified"
        diff[key]["declaration"] = ["new_api"] + new_api[key]["declaration"] + ["old_api"] + old_api[key]["declaration"]

  return diff


def generate_text_report(diff, level=0):
  report = ''
  indent_str = '  ' * level
  for key, value in diff.items():
    if isinstance(value, dict): # filter out  ["path", "api_type_link", "api_link", "declaration", "status"]
      if key not in ["api_types", "apis", "sub_apis"]:
        status_text = f"[{value.get('status', '').capitalize()}] " if 'status' in value else ''
        report += f"{indent_str}{status_text}{key}\n"
        declaration_text = ' '.join(value.get('declaration', ''))
        if declaration_text:
          report += f"{indent_str}  Declaration: {declaration_text}\n"
      
      report += generate_text_report(value, level=level + 1)

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