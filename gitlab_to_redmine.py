import argparse
import logging
import os
import re
import urllib3

import gitlab

from redminelib import Redmine
from redminelib.exceptions import ResourceNotFoundError


logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
    format='%(asctime)s %(message)s'
)

MRS_FIELD_ID = int(os.environ["GLRM_REDMINE_MRS_FIELD_ID"])
MRS_LIMIT = int(os.environ["GLRM_GITLAB_MRS_LIMIT"])
GITLAB_PROJECT_IDS = set(map(int, os.environ["GLRM_GITLAB_PROJECT_IDS"].split(",")))

GITLAB_TOKEN = os.environ["GLRM_GITLAB_TOKEN"]
GITLAB_URL = os.environ["GLRM_GITLAB_URL"]
REDMINE_TOKEN = os.environ["GLRM_REDMINE_TOKEN"]
REDMINE_URL = os.environ["GLRM_REDMINE_URL"]

if MRS_LIMIT > 100:
    raise RuntimeError("GLRM_GITLAB_MRS_LIMIT can't be greater than 100")


def get_issue_ids(string):
    return set(map(int, re.findall("#(\d{3,})", string)))


def get_issue_ids_from_commits(gitlab_commits):
    return {issue_id for commit in gitlab_commits for issue_id in get_issue_ids(commit.message)}


def get_mr_string(gitlab_mr):
    tags_map = {
        'merged': '%{background:lightgreen}MERGED%',
        'opened': '%{background:lightblue}OPENED%',
        'draft': '%{background:lightblue}DRAFT%',
        'closed': '%{background:red}CLOSED%',
    }
    draft_prefixes = ['Draft:', '[Draft]', '(Draft)', 'WIP:', '[WIP]']

    tags = [tags_map[gitlab_mr.state]]
    for prefix in draft_prefixes:
        if gitlab_mr.title.startswith(prefix):
            tags.append(tags_map['draft'])
            break

    return f'''"{gitlab_mr.references['full']}":{gitlab_mr.web_url} {' '.join(tags)}'''


def redmine_update_mrs(issue, string):
    logging.info(f'Update {issue.id}')
    issue.custom_fields = [{"id": MRS_FIELD_ID, "value": string}]
    issue.save()


def update_issues(gl_project, mrs_per_page=100, mrs_pages=1):
    redmine = Redmine(
        REDMINE_URL,
        key=REDMINE_TOKEN
    )

    for page in range(1, mrs_pages+1):
        for gl_mr in gl_project.mergerequests.list(
                state='all', order_by='updated_at',
                per_page=mrs_per_page, page=page
        ):
            logging.debug(f'Processing {gl_mr.web_url}')
            issue_ids = get_issue_ids_from_commits(gl_mr.commits()) | get_issue_ids(gl_mr.title)
            for issue_id in issue_ids:
                logging.debug(f'Get issue {issue_id}')
                try:
                    issue = redmine.issue.get(issue_id)
                except ResourceNotFoundError:
                    logging.error(f'Issue {issue_id} is not found')
                    continue

                issue_mrs = issue.custom_fields.get(resource_id=MRS_FIELD_ID)
                if not issue_mrs:
                    continue

                issue_mrs = issue_mrs.value.split('\n') if issue_mrs.value else []
                for issue_mr_id, issue_mr in enumerate(issue_mrs):
                    if gl_mr.web_url in issue_mr:
                        mr_string = get_mr_string(gl_mr)
                        if mr_string != issue_mr:
                            issue_mrs[issue_mr_id] = mr_string
                            logging.info(f'Replace {gl_mr.web_url} for {issue_id}')
                            redmine_update_mrs(issue, '\n'.join(issue_mrs))
                        break
                else:
                    issue_mrs.append(get_mr_string(gl_mr))
                    logging.info(f'Append {gl_mr.web_url} to {issue_id}')
                    redmine_update_mrs(issue, '\n'.join(issue_mrs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gitlab to Redmine')
    parser.add_argument('gitlab_project_ids', type=int, nargs='+', help='Gitlab project IDs')
    parser.add_argument('gitlab_project_mrs_limit', type=int, help='Gitlab MRs limit')
    parser.add_argument('redmine_mrs_field_id', type=int, help='Redmine MRs description custom-field ID')

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    logging.info('Started')

    gl = gitlab.Gitlab(url=GITLAB_URL, private_token=GITLAB_TOKEN, ssl_verify=False)

    for project_id in GITLAB_PROJECT_IDS:
        update_issues(gl.projects.get(project_id), mrs_per_page=MRS_LIMIT)

    logging.info('Completed')
