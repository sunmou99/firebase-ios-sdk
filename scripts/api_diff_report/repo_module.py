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

import os
import logging
import json
import subprocess

# List of Swift and Objective-C modules
SWIFT_MODULE = [
  "FirebaseAnalyticsSwift",
  "FirebaseDatabaseSwift",
  "FirebaseFirestoreSwift",
  "FirebaseFunctions",
  "FirebaseInAppMessagingSwift",
  "FirebaseMLModelDownloader",
  "FirebaseRemoteConfigSwift",
  "FirebaseStorage",
]

OBJC_MODULE = [
  "FirebaseAnalytics",
  "FirebaseAppCheck",
  "FirebaseAppDistribution",
  "FirebaseAuth",
  "FirebaseCore",
  "FirebaseABTesting",
  "FirebaseCrash",
  "FirebaseCrashlytics",
  "FirebaseDatabase",
  "FirebaseDynamicLinks",
  "FirebaseFirestore",
  "FirebaseInstallations",
  "FirebaseInAppMessaging",
  "FirebaseMessaging",
  "FirebasePerformance",
  "FirebaseRemoteConfig",
]

# Detect changed modules based on changed API files
def detect_changed_modules(changed_api_files):
  all_modules = module_info()
  changed_modules = {}
  for file_path in changed_api_files:
    for module in all_modules:
      if module["path"] in file_path:
        changed_modules[module["name"]] = module

  # print(changed_modules.values())
  return changed_modules.values()


# modules that exist in both `.podspecs` and `Package.swift` 
def module_info():
  module_info_1 = module_info_from_package_swift()
  module_info_2 = module_info_from_podspecs()

  all_modules = []
  for module in set(module_info_1.keys()).intersection(module_info_2.keys()):
    all_modules.append({"name": module, **module_info_1[module], **module_info_2[module]})
  # print(json.dumps(all_modules, indent=4))
  return all_modules


def module_info_from_package_swift():
  result = subprocess.Popen("swift package dump-package", 
                            universal_newlines=True, 
                            shell=True, 
                            stdout=subprocess.PIPE)
  
  package_json = json.loads(result.stdout.read())

  module_scheme = dict([(x['targets'][0], x['name']) for x in package_json['products']])
  module_path = dict([(x['name'], x['path']) for x in  package_json['targets'] if x['name'] in module_scheme])
  
  result = {}
  for k,v in module_scheme.items():
    result[k] = {"scheme": v, "path": module_path.get(k, "")}

  return result


def module_info_from_podspecs(root_dir=os.getcwd()):
  result = {}
  for filename in os.listdir(root_dir):
    if filename.endswith(".podspec"):
      podspec_data = parse_podspec(filename)
      umbrella_header = ""
      if "public_header_files" in podspec_data:
        if isinstance(podspec_data["public_header_files"], list):
          umbrella_header = podspec_data["public_header_files"][0].replace('*', podspec_data["name"])
        elif isinstance(podspec_data["public_header_files"], str):
          umbrella_header = podspec_data["public_header_files"].replace('*', podspec_data["name"])
      result[podspec_data["name"]] = {"umbrella-header": umbrella_header}
  return result


def parse_podspec(podspec_file):
  result = subprocess.run(f"pod ipc spec {podspec_file}", 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE, 
                        text=True, 
                        shell=True)
  if result.returncode != 0:
    print(f"Error: {result.stderr}")
    return None

  # Parse the JSON output
  podspec_data = json.loads(result.stdout)
  return podspec_data