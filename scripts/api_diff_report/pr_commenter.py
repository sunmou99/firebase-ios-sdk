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
import logging
import requests
import argparse

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


COMMENT_HIDDEN_IDENTIFIER = f'\r\n<hidden value="api-diff-report-comment"></hidden>\r\n'
GITHUB_API_URL = 'https://api.github.com/repos/firebase/firebase-ios-sdk'
PR_LABLE = "public-api-change"

RETRIES = 3
BACKOFF = 5
RETRY_STATUS = (403, 500, 502, 504)
TIMEOUT = 5

def main():
    logging.getLogger().setLevel(logging.INFO)

    # Parse command-line arguments
    args = parse_cmdline_args()

    token = args.token
    pr_number = args.pr_number
    comment = COMMENT_HIDDEN_IDENTIFIER + args.comment
    if comment:
        add_label(token, pr_number, PR_LABLE)
        comment = COMMENT_HIDDEN_IDENTIFIER + args.comment
    else:
        delete_label(token, pr_number, PR_LABLE)
        comment = COMMENT_HIDDEN_IDENTIFIER +  '## Generating Apple API Diff Report...'
    comment_id = get_comment_id(token, pr_number, COMMENT_HIDDEN_IDENTIFIER)
    if not comment_id:
        add_comment(token, pr_number, comment)
    else:
        update_comment(token, comment_id, comment)


def requests_retry_session(retries=RETRIES,
                           backoff_factor=BACKOFF,
                           status_forcelist=RETRY_STATUS):
    session = requests.Session()
    retry = Retry(total=retries,
                  read=retries,
                  connect=retries,
                  backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

  
def get_comment_id(token, issue_number, comment_identifier):
  comments = list_comments(token, issue_number)
  for comment in comments:
    if comment_identifier in comment['body']:
      return comment['id']
  return None


def list_comments(token, issue_number):
  """https://docs.github.com/en/rest/reference/issues#list-issue-comments"""
  url = f'{GITHUB_API_URL}/issues/{issue_number}/comments'
  headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {token}'}
  with requests_retry_session().get(url, headers=headers, timeout=TIMEOUT) as response:
    logging.info("list_comments: %s response: %s", url, response)
    return response.json()


def add_comment(token, issue_number, comment):
  """https://docs.github.com/en/rest/reference/issues#create-an-issue-comment"""
  url = f'{GITHUB_API_URL}/issues/{issue_number}/comments'
  headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {token}'}
  data = {'body': comment}
  with requests.post(url, headers=headers, data=json.dumps(data), timeout=TIMEOUT) as response:
    logging.info("add_comment: %s response: %s", url, response)


def update_comment(token, comment_id, comment):
  """https://docs.github.com/en/rest/reference/issues#update-an-issue-comment"""
  url = f'{GITHUB_API_URL}/issues/comments/{comment_id}'
  headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {token}'}
  data = {'body': comment}
  with requests_retry_session().patch(url, headers=headers, data=json.dumps(data), timeout=TIMEOUT) as response:
    logging.info("update_comment: %s response: %s", url, response)


def delete_comment(token, comment_id):
  """https://docs.github.com/en/rest/reference/issues#delete-an-issue-comment"""
  url = f'{GITHUB_API_URL}/issues/comments/{comment_id}'
  headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {token}'}
  with requests.delete(url, headers=headers, timeout=TIMEOUT) as response:
    logging.info("delete_comment: %s response: %s", url, response)


def add_label(token, issue_number, label):
  """https://docs.github.com/en/rest/reference/issues#add-labels-to-an-issue"""
  url = f'{GITHUB_API_URL}/issues/{issue_number}/labels'
  headers={}
  headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {token}'}
  data = [label]
  with requests.post(url, headers=headers, data=json.dumps(data), timeout=TIMEOUT) as response:
    logging.info("add_label: %s response: %s", url, response)


def delete_label(token, issue_number, label):
  """https://docs.github.com/en/rest/reference/issues#delete-a-label"""
  url = f'{GITHUB_API_URL}/issues/{issue_number}/labels/{label}'
  headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {token}'}
  with requests.delete(url, headers=headers, timeout=TIMEOUT) as response:
    logging.info("delete_label: %s response: %s", url, response)


def parse_cmdline_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--comment')
    parser.add_argument('-t', '--token')
    parser.add_argument('-n', '--pr_number')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()