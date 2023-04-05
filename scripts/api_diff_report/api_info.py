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
  
  output_dir = os.path.expanduser(args.output_dir)
  isExist = os.path.exists(output_dir)
  if not isExist:
    os.makedirs(output_dir)
  
  for file_name in args.file_list:
    logging.info(file_name)
    if file_name.endswith('.swift'):
      result = subprocess.run(
                args=["sourcekitten", "doc", "--single-file", file_name],
                capture_output=True,
                text=True, 
                check=False)
      logging.info("------------")
      api_info = result.stdout
      logging.info(api_info)
      file_path = os.path.join(output_dir, os.path.basename(file_name) + ".json")
      logging.info(file_path)
      with open(file_path, 'w') as f:
        f.write(api_info)
    elif file_name.endswith('.h'):
      result = subprocess.Popen(f"sourcekitten doc --objc {file_name} -- -x objective-c -isysroot $(xcrun --show-sdk-path) -I $(pwd)", 
                                universal_newlines=True, 
                                shell=True, 
                                stdout=subprocess.PIPE)
      logging.info("------------")
      api_info = result.stdout.read()
      logging.info(api_info)
      file_path = os.path.join(output_dir, os.path.basename(file_name) + ".json")
      logging.info(file_path)
      with open(file_path, 'w') as f:
        f.write(api_info)



def parse_cmdline_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file_list', nargs='+', default=[])
  parser.add_argument('-o', '--output_dir', default="")

  args = parser.parse_args()
  return args


if __name__ == '__main__':
  main()