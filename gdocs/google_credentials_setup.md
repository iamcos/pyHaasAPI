# Google Credentials Setup Guide

Follow these steps to get your Google Service Account credentials and publish data to your spreadsheet.

## Step 1: Google Cloud Console Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create or Select Project**: 
   - Create a new project or select existing one
   - Name it something like "pyHaasAPI Integration"

## Step 2: Enable Required APIs

1. **Enable Google Sheets API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click on it and press "Enable"

2. **Enable Google Drive API**:
   - In the same library, search for "Google Drive API"
   - Click on it and press "Enable"

## Step 3: Create Service Account

1. **Go to Service Accounts**:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"

2. **Service Account Details**:
   - **Name**: `pyhaasapi-sheets-integration`
   - **Description**: `Service account for pyHaasAPI Google Sheets integration`
   - Click "Create and Continue"

3. **Grant Access** (optional for now):
   - Skip the role assignment for now
   - Click "Continue"

4. **Grant Users Access** (optional):
   - Skip this step
   - Click "Done"

## Step 4: Create and Download Credentials

1. **Find Your Service Account**:
   - In the Service Accounts list, find your newly created account
   - Click on the email address (it will be something like `pyhaasapi-sheets-integration@your-project.iam.gserviceaccount.com`)

2. **Create Key**:
   - Go to the "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose "JSON" format
   - Click "Create"

3. **Download the JSON File**:
   - The JSON file will download automatically
   - Save it as `google_credentials.json` in the `gdocs/` folder

## Step 5: Share Your Spreadsheet

1. **Open Your Spreadsheet**: https://docs.google.com/spreadsheets/d/1cGdTBWDj96Fk3L5GIWnNJlRjLuCo3K3GJoNqdz_vbIo/edit

2. **Share with Service Account**:
   - Click the "Share" button (top right)
   - Add the service account email (from the JSON file, it's the "client_email" field)
   - Give it "Editor" permissions
   - Click "Send"

## Step 6: Set Environment Variable

```bash
export GOOGLE_CREDENTIALS_PATH=gdocs/google_credentials.json
```

## Step 7: Test the Integration

```bash
python gdocs/simple_google_sheets.py setup --sheet-id "1cGdTBWDj96Fk3L5GIWnNJlRjLuCo3K3GJoNqdz_vbIo"
```

## Troubleshooting

### Common Issues:

1. **"Credentials file not found"**:
   - Make sure the JSON file is saved as `google_credentials.json` in the `gdocs/` folder
   - Check the file path in the environment variable

2. **"Sheet not found or access denied"**:
   - Make sure you shared the spreadsheet with the service account email
   - Check that the service account has "Editor" permissions

3. **"Authentication failed"**:
   - Make sure the JSON credentials file is valid
   - Check that the Google Sheets API and Google Drive API are enabled

### Test Your Setup:

```bash
# Test if credentials are working
python -c "
import gspread
from google.oauth2.service_account import Credentials
import json

# Load credentials
with open('gdocs/google_credentials.json', 'r') as f:
    creds_info = json.load(f)

# Create credentials
creds = Credentials.from_service_account_file('gdocs/google_credentials.json', 
    scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

# Test connection
gc = gspread.authorize(creds)
print('✅ Google Sheets authentication successful!')
"
```

## Next Steps

Once you have the credentials set up:

1. **Run the setup**: `python gdocs/simple_google_sheets.py setup --sheet-id "1cGdTBWDj96Fk3L5GIWnNJlRjLuCo3K3GJoNqdz_vbIo"`
2. **Check your spreadsheet**: You should see new sheets created
3. **Review the data structure**: Labs, bots, and performance metrics
4. **Connect real data**: Replace sample data with your actual server data

## Your Spreadsheet Structure

After setup, you'll have:

- **Summary Sheet**: Overview of all servers
- **srv01 Sheet**: Labs and bots from server 1
- **srv02 Sheet**: Labs and bots from server 2  
- **srv03 Sheet**: Labs and bots from server 3

Each server sheet contains:
- **LABS Section**: Lab ID, name, script, market, status, performance metrics
- **BOTS Section**: Bot ID, name, performance, trading statistics
- **PERFORMANCE SUMMARY**: Total labs, bots, active bots, ROI statistics

