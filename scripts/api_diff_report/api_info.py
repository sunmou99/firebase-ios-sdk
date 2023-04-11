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

PRODUCT_LIST = [
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
  
  swift_to_objc = {}
  for file_path in args.file_list:
    logging.info(file_path)
    if file_path.endswith('.swift'):
      result = subprocess.Popen(f"sourcekitten doc --single-file {file_path}", 
                                universal_newlines=True, 
                                shell=True, 
                                stdout=subprocess.PIPE)
      logging.info("------------")
      api_info = result.stdout.read()
      output_path = os.path.join(output_dir, os.path.basename(file_path) + ".json")
      logging.info(output_path)
      with open(output_path, 'w') as f:
        f.write(api_info)

      match = re.search(fr"Firebase(.*?){os.sep}", file_path)
      if match:
        scheme = f"Firebase{match.groups()[0]}"
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        if scheme not in swift_to_objc:
          swift_to_objc[scheme] = []
        swift_to_objc[scheme].append(f"{file_name}-Swift.h")
      else:
        logging.error(f"no target matching file: {file_path}")
    elif file_path.endswith('.h') and "Public" in file_path:
      result = subprocess.Popen(f"sourcekitten doc --objc {file_path} -- -x objective-c -isysroot $(xcrun --show-sdk-path) -I $(pwd)", 
                                universal_newlines=True, 
                                shell=True, 
                                stdout=subprocess.PIPE)
      logging.info("------------")
      api_info = result.stdout.read()
      output_path = os.path.join(output_dir, os.path.basename(file_path) + ".json")
      logging.info(output_path)
      with open(output_path, 'w') as f:
        f.write(api_info)

  for scheme, files in swift_to_objc.items():
      result = subprocess.Popen("scripts/setup_spm_tests.sh", 
                                universal_newlines=True, 
                                shell=True, 
                                stdout=subprocess.PIPE)
      logging.info("------------")
      build_info = result.stdout.read()
      logging.info(build_info)
      result = subprocess.Popen(f"xcodebuild -scheme {scheme} -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 11' ONLY_ACTIVE_ARCH=YES CODE_SIGNING_REQUIRED=NO CODE_SIGNING_ALLOWED=YES COMPILER_INDEX_STORE_ENABLE=NO CC=clang CPLUSPLUS=clang++ LD=clang LDPLUSPLUS=clang++ IPHONEOS_DEPLOYMENT_TARGET=13.0 TVOS_DEPLOYMENT_TARGET=13.0 BUILD_DIR={output_dir}", 
                                universal_newlines=True, 
                                shell=True, 
                                stdout=subprocess.PIPE)
      logging.info("------------")
      build_info = result.stdout.read()
      logging.info(build_info)

      for file_dir, _, file_names in os.walk(output_dir):
        for file_name in file_names:
          if file_name in files:
            logging.info(file_path)
            file_path = os.path.join(file_dir, file_name)
            result = subprocess.Popen(f"sourcekitten doc --objc {file_path} -- -x objective-c -isysroot $(xcrun --show-sdk-path) -I $(pwd)", 
                                      universal_newlines=True, 
                                      shell=True, 
                                      stdout=subprocess.PIPE)
            logging.info("------------")
            api_info = result.stdout.read()
            output_path = os.path.join(output_dir, file_name + ".json")
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