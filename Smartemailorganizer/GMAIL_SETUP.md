# Gmail App Password Setup Guide

This application requires a Gmail App Password to fetch and send emails. Follow these steps to create one:

## Prerequisites

- A Gmail account
- 2-Step Verification enabled on your Google Account

## Step-by-Step Instructions

### 1. Enable 2-Step Verification (if not already enabled)

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click on **2-Step Verification**
3. Follow the prompts to set it up (you'll need your phone)

### 2. Create an App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click on **App passwords**
   - If you don't see this option, make sure 2-Step Verification is enabled
3. You may need to sign in again
4. At the bottom, select:
   - **Select app**: Choose "Mail"
   - **Select device**: Choose "Other (Custom name)"
5. Enter a name like "Local Email Manager"
6. Click **Generate**

### 3. Copy Your App Password

You'll see a 16-character password like this:

```
abcd efgh ijkl mnop
```

**Important**: 
- Remove all spaces when entering it: `abcdefghijklmnop`
- This password is shown only once - copy it now!
- It's all lowercase letters (no digits or special characters)

### 4. Use It in the Application

When registering in the Email Manager:

1. **Email**: your.email@gmail.com
2. **Password**: abcdefghijklmnop (your 16-character app password, no spaces)
3. **Confirm Password**: Same as above

## Security Notes

✓ **Safe**: App passwords are designed for this purpose
✓ **Revocable**: You can revoke it anytime from your Google Account
✓ **Encrypted**: The app stores it encrypted in your local database
✓ **Local**: All data stays on your machine

## Troubleshooting

### "App passwords" option not showing

- Make sure 2-Step Verification is enabled
- Try signing out and back into your Google Account
- Some Google Workspace accounts may have this disabled by admins

### Authentication failed when syncing

- Double-check you removed all spaces from the app password
- Make sure you're using the app password, not your regular Gmail password
- Try generating a new app password

### Want to revoke access?

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click on **App passwords**
3. Find "Local Email Manager" and click the trash icon

## Example

Here's what a valid registration looks like:

```
Email: john.doe@gmail.com
Password: abcdefghijklmnop
Confirm Password: abcdefghijklmnop
```

After registration, click "Sync" to fetch your emails!

---

**Need help?** Check the [README.md](README.md) for more information.
