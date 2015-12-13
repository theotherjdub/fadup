import json
from apiclient.discovery import build
from httplib2 import Http
from oauth2client.client import SignedJwtAssertionCredentials

def GetAllUsersInAccount(customerId, superAdmin, jsonKey):
  '''
This issues 1 call to the Admin SDK API to get a list of all active users in the Apps account.
The return value is a list of the primary email address for each active user.
A user may or may not have a Cloud Platfrom project.
  '''

  userList = []
  credential = SignedJwtAssertionCredentials(jsonKey['client_email'], jsonKey['private_key'], 
      'https://www.googleapis.com/auth/admin.directory.user', sub=superAdmin)
  httpAuth = credential.authorize(Http())
  service = build('admin', 'directory_v1', http=httpAuth)
  request = service.users().list(customer=customerId, fields='users/primaryEmail',
      query='isSuspended=false')
  while (request != None):
    results = request.execute()
    userList += results['users']
    request = service.users().list_next(request, results)

  return results['users']


def GetUsersProjects(emails, jsonKey):
  '''
This issues 1 call to the Cloud Resource Manager API for EACH user passed in emails.
An account with 50,000 users will have 50,000 API calls, but this should still be well within
normal quotas.
The API lists all the Cloud Platform projects the user has access to. The list may be empty.
This function returns a list of (user, project) where user has access to project.
  '''

  userProjectList = []
  for user in emails:
    credential = SignedJwtAssertionCredentials(jsonKey['client_email'], jsonKey['private_key'], 
        'https://www.googleapis.com/auth/cloud-platform', sub=user['primaryEmail'])
    httpAuth = credential.authorize(Http())
    service = build('cloudresourcemanager', 'v1beta1', http=httpAuth)
    request = service.projects().list()
    while request != None:
      results = request.execute()
      if len(results) > 0:
        for project in results['projects']:
          userProjectList.append((user['primaryEmail'], project['name'], project['projectId'],
              project['projectNumber']))
      request = service.projects().list_next(request, results)

  return userProjectList

def main():
  '''
This code is provided as-is with no support, no warranty, and no guarantee for fitness of any use.
This is only an example.

YOU MUST:
- modify this code to make it usable in your environment.
- test your modified code in a test environment before using in production.
- test pagination if your account has more than 500 users.

fadup: Find All Domain User Projects

This script will find all the Google Cloud Platform projects for all users in your Google Apps account.
Before using this you need to do the following:

1. In the Developers Console, enable Google Cloud Resource Manager API and Admin SDK for your project.

2. In the Developers Console, create a service account and download the JSON key file.

3. Make the key file available to this script and change the value of the variable
jsonKeyFile in main() to that path/filename.

4. Get the client ID from step 2. Go to the Apps Admin Console > Security > Manage API client access.
Authorize the client ID for these 2 scopes:
https://www.googleapis.com/auth/cloud-platform, https://www.googleapis.com/auth/admin.directory.user

5. Find your Google Apps account immutable customer ID. Use the API Explorer to execute users.get
on your own account at https://developers.google.com/admin-sdk/directory/v1/reference/users/get.
The customer ID will be at the bottom of the response. Change the value of the variable
customerId in main() to that value.

6. Change the value of the variable superAdmin in main() to an Apps super admin account. This account
is not used except that the users.list API call requires it.

You may also have to activate the service account you created in step 2:
gcloud auth activate-service-account account-1@findalldomainprojects.iam.gserviceaccount.com
 --key-file <path to key file from step 3>

The output of this script is a CSV list of users (primary email address) that have GCP projects and
their projects. This is probably the most useful format for the data. You can then import that CSV
into a spreadsheet or other tool to manipulate it as you like.

Regarding pagination: This script has code to support pagination for accounts with more than 500 users
but that code has not been tested. The script has code to support pagination if 1 user has more
Cloud Platform projects than can be returned by one call. However, the doc says this is
currently unsupported (https://cloud.google.com/resource-manager/reference/rest/v1beta1/projects/list).

IMPORTANT:
There are 3 hard-coded values which need to be changed in the first 3 lines of main().
These are customerId, superAdmin, jsonKeyFile.

  '''

  customerId = 'XXXXXXXXXX'
  superAdmin = 'XXXXXXXX@domain.com'
  jsonKeyFile = 'fadup-XXXXXXXXXXXX.json'

  jsonData = json.load(open(jsonKeyFile))

  userList = GetAllUsersInAccount(customerId, superAdmin, jsonData)

  projectList = GetUsersProjects(userList, jsonData)

  for user, projectName, projectId, projectNumber in projectList:
    print '{0}, {1}, {2}, {3}'.format(user, projectName, projectId, projectNumber)


if __name__ == "__main__":
  main()
