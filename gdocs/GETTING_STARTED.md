# Getting Started with Google Sheets Integration

Follow these steps to publish your real pyHaasAPI data to your Google Sheets spreadsheet.

## 🚀 Quick Start (5 Steps)

### Step 1: Get Google Credentials
1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create/Select Project**: Create a new project or select existing one
3. **Enable APIs**: Enable Google Sheets API and Google Drive API
4. **Create Service Account**:
   - Go to IAM & Admin > Service Accounts
   - Create new service account
   - Download JSON credentials file
5. **Save Credentials**: Save as `google_credentials.json` in the `gdocs/` folder

### Step 2: Share Your Spreadsheet
1. **Open Your Spreadsheet**: https://docs.google.com/spreadsheets/d/1cGdTBWDj96Fk3L5GIWnNJlRjLuCo3K3GJoNqdz_vbIo/edit
2. **Share with Service Account**: 
   - Click "Share" button
   - Add the service account email (from your JSON file)
   - Give "Editor" permissions
   - Click "Send"

### Step 3: Set Environment Variable
```bash
export GOOGLE_CREDENTIALS_PATH=gdocs/google_credentials.json
```

### Step 4: Test Connection
```bash
python gdocs/test_connection.py
```

### Step 5: Publish Real Data
```bash
python gdocs/publish_real_data.py
```

## 📊 What You'll Get

After publishing, your spreadsheet will have:

### Summary Sheet
- **Server Status**: Connection status for srv01, srv02, srv03
- **Statistics**: Total labs, bots, active bots, best ROI
- **Quick Actions**: Sync data, create bots, run analysis

### Server Sheets (srv01, srv02, srv03)
Each server gets its own sheet with:

**LABS Section:**
- Lab ID, Name, Script, Market, Status
- Number of Backtests, Best ROI %, Best Win Rate %
- Best Trades, Created/Updated timestamps

**BOTS Section:**
- Bot ID, Name, Script, Market, Status, Account
- ROI %, Win Rate %, Trades, Max Drawdown %
- Profit Factor, Leverage, Trade Amount

**PERFORMANCE SUMMARY:**
- Total Labs, Total Bots, Active Bots
- Real-time statistics from your servers

## 🔧 Available Scripts

### Test Connection
```bash
python gdocs/test_connection.py
```
Tests your Google Sheets connection and credentials.

### Publish Real Data
```bash
python gdocs/publish_real_data.py
```
Publishes your actual pyHaasAPI data to Google Sheets.

### Simple Setup (Sample Data)
```bash
python gdocs/simple_google_sheets.py setup --sheet-id "1cGdTBWDj96Fk3L5GIWnNJlRjLuCo3K3GJoNqdz_vbIo"
```
Creates the sheet structure with sample data.

### Real Data Publisher
```bash
python gdocs/real_data_publisher.py --sheet-id "1cGdTBWDj96Fk3L5GIWnNJlRjLuCo3K3GJoNqdz_vbIo"
```
Publishes real data from your pyHaasAPI servers.

## 🚨 Troubleshooting

### Common Issues

1. **"Credentials file not found"**:
   - Make sure `google_credentials.json` is in the `gdocs/` folder
   - Check the file path in the environment variable

2. **"Sheet not found or access denied"**:
   - Make sure you shared the spreadsheet with the service account email
   - Check that the service account has "Editor" permissions

3. **"Authentication failed"**:
   - Make sure the JSON credentials file is valid
   - Check that Google Sheets API and Google Drive API are enabled

4. **"pyHaasAPI not found"**:
   - Make sure you're running from the project root directory
   - Check that pyHaasAPI is properly installed

### Debug Steps

1. **Check Credentials**:
   ```bash
   ls -la gdocs/google_credentials.json
   ```

2. **Test Google Connection**:
   ```bash
   python gdocs/test_connection.py
   ```

3. **Check Environment**:
   ```bash
   echo $GOOGLE_CREDENTIALS_PATH
   ```

4. **Verify Spreadsheet Access**:
   - Open your spreadsheet in browser
   - Check if service account email is in the sharing list

## 📈 Data Flow

1. **Connect to Servers**: Script connects to srv01, srv02, srv03
2. **Fetch Data**: Retrieves labs, bots, and performance data
3. **Process Data**: Calculates statistics and finds best performers
4. **Publish to Sheets**: Updates Google Sheets with real data
5. **Format**: Applies formatting and creates structure

## 🎯 Next Steps

After publishing your data:

1. **Review the Data**: Check your spreadsheet for the new sheets
2. **Analyze Performance**: Look at ROI, win rates, and trading statistics
3. **Identify Top Performers**: Find your best labs and bots
4. **Create Action Plan**: Use the data to make trading decisions
5. **Set Up Automation**: Consider setting up regular data sync

## 🔄 Regular Updates

To keep your data fresh:

```bash
# Run this regularly to update your data
python gdocs/publish_real_data.py
```

Or set up a cron job for automatic updates:

```bash
# Add to crontab for daily updates at 9 AM
0 9 * * * cd /path/to/pyHaasAPI && python gdocs/publish_real_data.py
```

## 📚 Documentation

- **Complete Setup Guide**: `google_credentials_setup.md`
- **API Reference**: `README.md`
- **Troubleshooting**: This file

## 🎉 Success!

Once everything is working, you'll have:
- ✅ Real-time data from all your servers
- ✅ Performance metrics and statistics
- ✅ Beautifully formatted Google Sheets
- ✅ Easy access to your trading data
- ✅ Persistent authentication (no re-auth needed)

Your pyHaasAPI data is now live in Google Sheets! 🚀

