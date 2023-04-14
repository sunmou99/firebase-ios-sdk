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

from urllib.parse import unquote
from bs4 import BeautifulSoup

# https://source.corp.google.com/piper///depot/google3/googlemac/iPhone/Firebase/Docs/jazzy/jazzyFirebase.sh;l=22?q=jazzyfirebase.sh
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

OBJC_MODULE = [
  "Analytics",
  "AppCheck",
  "AppDistribution",
  "Auth",
  "Core",
  "ABTesting",
  "Crash",
  "Crashlytics",
  "Database",
  "DynamicLinks",
  "Firestore",
  "Installations",
  "InAppMessaging",
  "Messaging",
  "Performance",
  "RemoteConfig"
]

def main():
  logging.getLogger().setLevel(logging.INFO)

  args = parse_cmdline_args()
  output_dir = os.path.expanduser(args.output_dir)
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  changed_api_files = [f for f in args.file_list if f.endswith('.swift') or (f.endswith('.h') and "Public" in f)]
  changed_modules = detect_changed_modules(changed_api_files)
  changed_modules = ["MLModelDownloader"]
  for module in changed_modules:
    api_doc_path = os.path.join(output_dir, "doc", module)
    build_api_doc(module, api_doc_path)

    module_data = parse_module(api_doc_path)
    output_path = os.path.join(output_dir, "module_data.json")
    logging.info(output_path)
    with open(output_path, 'w') as f:
      f.write(json.dumps(module_data, indent=2))

    api_data_conatiner = {}
    for _, api_abstract in module_data.items():
      parse_api(api_doc_path, api_abstract, api_data_conatiner)
    output_path = os.path.join(output_dir, "api_data.json")
    logging.info(output_path)
    with open(output_path, 'w') as f:
      f.write(json.dumps(api_data_conatiner, indent=2))


def collect_module_info():
  result = subprocess.Popen("swift package dump-package", 
                            universal_newlines=True, 
                            shell=True, 
                            stdout=subprocess.PIPE)
  logging.info("------------")
  package_json = json.loads(result.stdout.read())

  module_scheme = dict([(x['targets'][0], x['name']) for x in package_json['products']])
  module_path = dict([(x['name'], x['path']) for x in  package_json['targets'] if x['name'] in module_scheme])
  path_module = {v: k for k, v in module_path.items()}
  
  logging.info(json.dumps(module_scheme, indent=2))
  logging.info(json.dumps(module_path, indent=2))


def detect_changed_modules(changed_api_files):
  changed_modules = set()
  for file_path in changed_api_files:
    logging.info(file_path)
    for path, module in path_module.items():
      if path in file_path:
        changed_modules.add(module)

def build_api_doc(module, output_dir):
  if module in SWIFT_MODULE:
    logging.info("------------")
    module = "Firebase"+module
    logging.info(f"jazzy --module {module} --swift-build-tool xcodebuild --build-tool-arguments -scheme,{module},-destination,generic/platform=iOS,build --output {output_dir}")
    result = subprocess.Popen(f"jazzy --module {module} --swift-build-tool xcodebuild --build-tool-arguments -scheme,{module},-destination,generic/platform=iOS,build --output {output_dir}", 
                              universal_newlines=True, 
                              shell=True, 
                              stdout=subprocess.PIPE)
    logging.info(result.stdout.read())
  # elif module in OBJC_MODULE:
  #   logging.info("------------")
  #   logging.info(f"jazzy --objc --framework-root {module_path[module]} --umbrella-header {module_path[module]}/Public/{module}/{module}.h --output {output_dir}/{module}")
  #   result = subprocess.Popen(f"jazzy --objc --framework-root {module_path[module]} --umbrella-header {module_path[module]}/Public/{module}/{module}.h --output {output_dir}/{module}", 
  #                             universal_newlines=True, 
  #                             shell=True, 
  #                             stdout=subprocess.PIPE)
  #   logging.info(result.stdout.read())


# {$api_type: {"api_type_link": $api_type_link, "apis": { $api_name: $api_link }}}
def parse_module(api_doc_path):
  module_data_container = {}
  # Read the HTML content from the file
  index_link = f"{api_doc_path}/index.html"
  with open(index_link, "r") as file:
    html_content = file.read()

  # Parse the HTML content
  soup = BeautifulSoup(html_content, "html.parser")

  # Locate the element with class="nav-groups"
  nav_groups_element = soup.find("ul", class_="nav-groups")
  # Extract data and convert to JSON format
  
  for nav_group in nav_groups_element.find_all("li", class_="nav-group-name"):
    api_type = nav_group.find("a").text
    api_type_link = nav_group.find("a")["href"]

    apis = {}
    for nav_group_task in nav_group.find_all("li", class_="nav-group-task"):
      api_name = nav_group_task.find("a").text
      api_link = nav_group_task.find("a")["href"]
      apis[api_name] = api_link

    module_data_container[api_type] = {
      "api_type_link": api_type_link,
      "apis": apis
    }

  return module_data_container


# {$api_name: {"declaration": $api_declaration, "sub_apis": { $sub_api_name: $_declaration }}}
def parse_api(api_doc_path, api_abstract, api_data_container):
  api_type_link = f'{api_doc_path}/{unquote(api_abstract["api_type_link"])}'
  with open(api_type_link, "r") as file:
    html_content = file.read()

  # Parse the HTML content
  soup = BeautifulSoup(html_content, "html.parser")
  for api in soup.find("div", class_="task-group").find_all("li", class_="item"):
    api_name = api.find("a", class_="token").text
    api_data_container[api_name] = {"declaration":[], "sub_apis":{}}
    for api_declaration in api.find_all("div", class_="language"):
      api_declaration_text = ' '.join(api_declaration.stripped_strings)
      api_data_container[api_name]["declaration"].append(api_declaration_text)

  for api, api_link in api_abstract["apis"].items():
    if api_link.endswith(".html"):
      parse_sub_api(f'{api_doc_path}/{unquote(api_link)}', api_data_container[api])


def parse_sub_api(api_link, sub_api_data_container):
  with open(api_link, "r") as file:
    html_content = file.read()

  soup = BeautifulSoup(html_content, "html.parser")
  for s_api in soup.find("div", class_="task-group").find_all("li", class_="item"):
    api_name = s_api.find("a", class_="token").text
    sub_api_data_container["sub_apis"][api_name] = []
    for api_declaration in s_api.find_all("div", class_="language"):
      api_declaration_text = ' '.join(api_declaration.stripped_strings)
      sub_api_data_container["sub_apis"][api_name].append(api_declaration_text)


def parse_cmdline_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--file_list', nargs='+', default=[])
  parser.add_argument('-o', '--output_dir', default="")

  args = parser.parse_args()
  return args


if __name__ == '__main__':
  main()