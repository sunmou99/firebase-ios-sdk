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

PROUDCT_LIST = [
  "ABTesting",
  "AppCheck",
  "AppDistribution",
  "Analytics",
  "Authentication",
  "Core",
  "Crashlytics",
  "Database",
  "DynamicLinks",
  "Firestore",
  "Functions",
  "InAppMessaging",
  "Installations",
  "Messaging",
  "Performance",
  "RemoteConfig",
  "Storage"
]

def main():
  logging.getLogger().setLevel(logging.INFO)

  args = parse_cmdline_args()
  logging.info(args)
  
  output_dir = os.path.expanduser(args.output_dir)
  isExist = os.path.exists(output_dir)
  if not isExist:
    os.makedirs(output_dir)
  
  # product_list = [x for x in next(os.walk('.'))[1] if x.startswith("Firebase") or x=="Firestore"]
  # target_list = [os.path.splitext(x)[0] for x in next(os.walk('.'))[2] if x.startswith("Firebase") and x.endswith(".podspec")]
  # logging.info(product_list)
  # logging.info(target_list)

  changed_products = set()
  for file_path in args.file_list:
    logging.info(file_path)
    for product in PROUDCT_LIST:
      if product in file_path:
        changed_products.add(product)
  logging.info(changed_products)

  # for product in changed_products:
  result = subprocess.Popen(f"jazzy --module FirebaseMLModelDownloader --swift-build-tool spm --build-tool-arguments --target,FirebaseMLModelDownloader --output {output_dir}/m", 
                            universal_newlines=True, 
                            shell=True, 
                            stdout=subprocess.PIPE)
  logging.info("------------")
  api_info = result.stdout.read()
  output_path = os.path.join(output_dir, os.path.basename(file_path) + ".json")
  logging.info(output_path)
  with open(output_path, 'w') as f:
    f.write(api_info)

  result = subprocess.Popen(f"jazzy --objc --framework-root FirebaseAppDistribution/Sources --umbrella-header FirebaseAppDistribution/Sources/Public/FirebaseAppDistribution/FIRAppDistribution.h {output_dir}/d", 
                            universal_newlines=True, 
                            shell=True, 
                            stdout=subprocess.PIPE)
  logging.info("------------")
  api_info = result.stdout.read()
  output_path = os.path.join(output_dir, os.path.basename(file_path) + ".json")
  logging.info(output_path)
  with open(output_path, 'w') as f:
    f.write(api_info)



def parse_cmdline_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file_list', nargs='+', default=[])
  parser.add_argument('-o', '--output_dir', default="")

  args = parser.parse_args()
  return args


if __name__ == '__main__':
  main()