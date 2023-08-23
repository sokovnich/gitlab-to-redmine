# gitlab-to-redmine

Simple cron script to sync Gitlab Merge Request statuses with corresponding Redmine issues.

## How to use

First you need to create access tokens for Gitlab/Redmine APIs:  
https://www.redmine.org/projects/redmine/wiki/rest_api#Authentication  
https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html  
Gitlab account must have read access to all required projects.  
Redmine account must have read/write access to all required projects.  
For Redmine issues in you project you need to create `Custom field`  
with type `Long text` and `Text formatting` support enabled  
(https://www.redmine.org/projects/redmine/wiki/redminecustomfields).  
Write access for Redmine account may be limited to this single field.  

To link Redmine issue with corresponding Gitlab Merge Requests  
the issue number should be mentioned in Merge Request title  
or inside any of commit messages in the following format:
```
#<issue-number>
```
Every Merge Request conforming to these requirements will be mentioned  
inside Redmine issue and be kept up to date.  

![redmine](https://github.com/sokovnich/gitlab-to-redmine/assets/20459727/4373dfe8-d2cb-43e1-920a-b99be16a14df)

### VENV

```bash
python3 -m virtualenv venv
source ./venv/bin/activate
./venv/bin/pip install -r ./requirements.txt

export GLRM_GITLAB_TOKEN='<token>'
export GLRM_GITLAB_URL='<url>'
export GLRM_REDMINE_TOKEN='<token>'
export GLRM_REDMINE_URL='<url>'
export GLRM_GITLAB_PROJECT_IDS=1,2,3,4
export GLRM_REDMINE_MRS_FIELD_ID=123
export GLRM_GITLAB_MRS_LIMIT=20

./venv/bin/python ./gitlab_to_redmine.py
```

### Docker
```bash
docker build -t gitlab-to-redmine .

cat << EOF > .env
GLRM_GITLAB_TOKEN='<token>'
GLRM_GITLAB_URL='<url>'
GLRM_REDMINE_TOKEN='<token>'
GLRM_REDMINE_URL='<url>'
GLRM_GITLAB_PROJECT_IDS=1,2,3,4
GLRM_REDMINE_MRS_FIELD_ID=123
GLRM_GITLAB_MRS_LIMIT=20
EOF

docker run --rm --env-file=.env gitlab-to-redmine
```

Pre-built images are also available on Docker Hub.  
https://hub.docker.com/r/sokovnich/gitlab-to-redmine  
```
docker pull sokovnich/gitlab-to-redmine:latest
```
