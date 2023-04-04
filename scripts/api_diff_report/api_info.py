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
  
  for file in args.file_list:
    if file.endswith('.swift'):
      result = subprocess.run(
                args=["sourcekitten", "doc", "--single-file", file],
                capture_output=True,
                text=True, 
                check=False)
      logging.info(file)
      logging.info(result.stdout)
      report_file_path = os.path.join(args.output_dir, os.path.join(os.path.basename(file), ".json"))
      with open(report_file_path, 'w') as f:
        f.write(result.stdout)


def parse_cmdline_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file_list', nargs='+', default=[])
  parser.add_argument('-o', '--output_dir', default="")

  args = parser.parse_args()
  return args


if __name__ == '__main__':
  main()