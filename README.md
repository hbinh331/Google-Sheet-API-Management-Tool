## Quick guide

#### Step 1: Go to console.cloud.google.com. Create a new project
#### Step 2: In the viewpage of that project, head to "APIs and services" -> "Enabled APIs and services", then enable "Google Sheets API".
#### Step 3: In "Enabled APIs and services", look for "Create credentials". Go ahead and create a credential, make sure to set "Role" to "Editor"
#### Step 4: In "Enabled APIs and services", click on the "CREDENTIALS" tab -> click on the service account we just created -> click on "KEYS" -> create and download a new key in JSON format.
#### Step 5: Replace the credentials.json file in the project with your .json file.
#### Step 6: Share your spreadsheet with the email in the "Service Accounts", make sure to grant "Editor" permission.
#### Step 7: Run the file "googleAPIServer.py". Open your browser and connect to "localhost:8000". Finally, paste your spreadsheet's link and then you can start doing CRUD on your spreadsheet.

*Note: Refer to https://www.youtube.com/watch?v=zCEJurLGFRk for an intuitive tutorial*


