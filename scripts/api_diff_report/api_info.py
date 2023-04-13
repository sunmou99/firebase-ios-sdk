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
import re

SWIFT_MODULE = [
  "AnalyticsSwift",
  "DatabaseSwift",
  "FirestoreSwift",
  "Functions",
  "InAppMessagingSwift",
  "MLModelDownloader",
  "RemoteConfigSwift",
  "Storage"
]

def main():
  logging.getLogger().setLevel(logging.INFO)

  args = parse_cmdline_args()
  logging.info(args)
  
  output_dir = os.path.expanduser(args.output_dir)
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  changed_api_files = [f for f in args.file_list if f.endswith('.swift') or (f.endswith('.h') and "Public" in f)]
  
  result = subprocess.Popen("swift package dump-package", 
                            universal_newlines=True, 
                            shell=True, 
                            stdout=subprocess.PIPE)
  logging.info("------------")
  package_json = json.loads(result.stdout.read())

  module_scheme = dict([(x['targets'][0], x['name']) for x in package_json['products']])
  path_module = dict([(x['path'], x['name']) for x in  package_json['targets'] if x['name'] in module_scheme])
  
  logging.info(module_scheme)
  logging.info(path_module)

  changed_modules = set()
  for file_path in changed_api_files:
    logging.info(file_path)
    for path, module in path_module.items():
      if path in file_path:
        changed_modules.add(module)
 
  logging.info(changed_modules)

  # # for product in changed_products:
  # result = subprocess.Popen(f"jazzy --module FirebaseMLModelDownloader --swift-build-tool spm --build-tool-arguments --target,FirebaseMLModelDownloader --output {output_dir}/m", 
  #                           universal_newlines=True, 
  #                           shell=True, 
  #                           stdout=subprocess.PIPE)
  # logging.info("------------")
  # api_info = result.stdout.read()
  # output_path = os.path.join(output_dir, os.path.basename(file_path) + ".json")
  # logging.info(output_path)
  # with open(output_path, 'w') as f:
  #   f.write(api_info)

  # result = subprocess.Popen(f"jazzy --objc --framework-root FirebaseAppDistribution/Sources --umbrella-header FirebaseAppDistribution/Sources/Public/FirebaseAppDistribution/FIRAppDistribution.h --output {output_dir}/d", 
  #                           universal_newlines=True, 
  #                           shell=True, 
  #                           stdout=subprocess.PIPE)
  # logging.info("------------")
  # api_info = result.stdout.read()
  # output_path = os.path.join(output_dir, os.path.basename(file_path) + ".json")
  # logging.info(output_path)
  # with open(output_path, 'w') as f:
  #   f.write(api_info)



def parse_cmdline_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file_list', nargs='+', default=[])
  parser.add_argument('-o', '--output_dir', default="")

  args = parser.parse_args()
  return args


if __name__ == '__main__':
  main()