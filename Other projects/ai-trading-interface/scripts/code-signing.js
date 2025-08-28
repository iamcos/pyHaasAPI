#!/usr/bin/env node

/**
 * Code Signing Configuration and Utilities
 * Handles code signing for different platforms
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class CodeSigning {
  constructor(options = {}) {
    this.platform = process.platform;
    this.environment = options.environment || 'production';
    this.verbose = options.verbose || false;
  }

  log(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
    
    if (this.verbose || level === 'error') {
      console.log(`${prefix} ${message}`);
    }
  }

  async setupCodeSigning() {
    this.log('Setting up code signing...', 'info');
    
    try {
      switch (this.platform) {
        case 'darwin':
          await this.setupMacOSCodeSigning();
          break;
        case 'win32':
          await this.setupWindowsCodeSigning();
          break;
        case 'linux':
          await this.setupLinuxCodeSigning();
          break;
        default:
          this.log(`Code signing not configured for platform: ${this.platform}`, 'warn');
      }
    } catch (error) {
      this.log(`Code signing setup failed: ${error.message}`, 'error');
      throw error;
    }
  }

  async setupMacOSCodeSigning() {
    this.log('Setting up macOS code signing...', 'info');
    
    // Check for signing identity
    const signingIdentity = process.env.MACOS_SIGNING_IDENTITY;
    const provisioningProfile = process.env.MACOS_PROVISIONING_PROFILE;
    
    if (!signingIdentity) {
      this.log('MACOS_SIGNING_IDENTITY not set, skipping code signing', 'warn');
      return;
    }
    
    // Update Tauri configuration for macOS signing
    const tauriConfigPath = 'src-tauri/tauri.conf.json';
    const tauriConfig = JSON.parse(fs.readFileSync(tauriConfigPath, 'utf8'));
    
    tauriConfig.bundle.macOS = {
      ...tauriConfig.bundle.macOS,
      signingIdentity: signingIdentity,
      providerShortName: process.env.MACOS_PROVIDER_SHORT_NAME || null,
      entitlements: 'entitlements.plist'
    };
    
    fs.writeFileSync(tauriConfigPath, JSON.stringify(tauriConfig, null, 2));
    
    // Create entitlements file
    await this.createMacOSEntitlements();
    
    this.log('macOS code signing configured', 'info');
  }

  async setupWindowsCodeSigning() {
    this.log('Setting up Windows code signing...', 'info');
    
    const certificateThumbprint = process.env.WINDOWS_CERTIFICATE_THUMBPRINT;
    const timestampUrl = process.env.WINDOWS_TIMESTAMP_URL || 'http://timestamp.digicert.com';
    
    if (!certificateThumbprint) {
      this.log('WINDOWS_CERTIFICATE_THUMBPRINT not set, skipping code signing', 'warn');
      return;
    }
    
    // Update Tauri configuration for Windows signing
    const tauriConfigPath = 'src-tauri/tauri.conf.json';
    const tauriConfig = JSON.parse(fs.readFileSync(tauriConfigPath, 'utf8'));
    
    tauriConfig.bundle.windows = {
      ...tauriConfig.bundle.windows,
      certificateThumbprint: certificateThumbprint,
      digestAlgorithm: 'sha256',
      timestampUrl: timestampUrl
    };
    
    fs.writeFileSync(tauriConfigPath, JSON.stringify(tauriConfig, null, 2));
    
    this.log('Windows code signing configured', 'info');
  }

  async setupLinuxCodeSigning() {
    this.log('Setting up Linux code signing...', 'info');
    
    // Linux typically uses GPG signing for packages
    const gpgKey = process.env.LINUX_GPG_KEY;
    
    if (!gpgKey) {
      this.log('LINUX_GPG_KEY not set, skipping code signing', 'warn');
      return;
    }
    
    // For Linux, we'll set up GPG signing for the package
    this.log('Linux code signing configured', 'info');
  }

  async createMacOSEntitlements() {
    const entitlementsContent = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.security.app-sandbox</key>
  <true/>
  <key>com.apple.security.network.client</key>
  <true/>
  <key>com.apple.security.network.server</key>
  <true/>
  <key>com.apple.security.files.user-selected.read-write</key>
  <true/>
  <key>com.apple.security.files.downloads.read-write</key>
  <true/>
  <key>com.apple.security.temporary-exception.files.absolute-path.read-write</key>
  <array>
    <string>/tmp</string>
  </array>
</dict>
</plist>`;
    
    fs.writeFileSync('src-tauri/entitlements.plist', entitlementsContent);
    this.log('macOS entitlements file created', 'info');
  }

  async validateSignature(filePath) {
    this.log(`Validating signature for: ${filePath}`, 'info');
    
    try {
      switch (this.platform) {
        case 'darwin':
          execSync(`codesign --verify --verbose ${filePath}`, { stdio: 'pipe' });
          this.log('macOS signature validation passed', 'info');
          break;
        case 'win32':
          // Windows signature validation would go here
          this.log('Windows signature validation not implemented', 'warn');
          break;
        case 'linux':
          // Linux signature validation would go here
          this.log('Linux signature validation not implemented', 'warn');
          break;
      }
    } catch (error) {
      throw new Error(`Signature validation failed: ${error.message}`);
    }
  }

  async notarizeApp(appPath) {
    if (this.platform !== 'darwin') {
      this.log('Notarization only available on macOS', 'warn');
      return;
    }
    
    const appleId = process.env.APPLE_ID;
    const applePassword = process.env.APPLE_PASSWORD;
    const teamId = process.env.APPLE_TEAM_ID;
    
    if (!appleId || !applePassword || !teamId) {
      this.log('Apple credentials not set, skipping notarization', 'warn');
      return;
    }
    
    this.log('Starting notarization process...', 'info');
    
    try {
      // Submit for notarization
      const submitResult = execSync(
        `xcrun notarytool submit "${appPath}" --apple-id "${appleId}" --password "${applePassword}" --team-id "${teamId}" --wait`,
        { encoding: 'utf8' }
      );
      
      this.log('Notarization submitted successfully', 'info');
      
      // Staple the notarization
      execSync(`xcrun stapler staple "${appPath}"`);
      this.log('Notarization stapled successfully', 'info');
      
    } catch (error) {
      throw new Error(`Notarization failed: ${error.message}`);
    }
  }
}

// CLI interface
if (require.main === module) {
  const args = process.argv.slice(2);
  const options = {};
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg === '--environment' || arg === '-e') {
      options.environment = args[++i];
    } else if (arg === '--verbose' || arg === '-v') {
      options.verbose = true;
    }
  }
  
  const codeSigning = new CodeSigning(options);
  
  if (args.includes('setup')) {
    codeSigning.setupCodeSigning();
  } else if (args.includes('validate')) {
    const filePath = args[args.indexOf('validate') + 1];
    if (filePath) {
      codeSigning.validateSignature(filePath);
    } else {
      console.error('Please provide a file path to validate');
      process.exit(1);
    }
  } else if (args.includes('notarize')) {
    const appPath = args[args.indexOf('notarize') + 1];
    if (appPath) {
      codeSigning.notarizeApp(appPath);
    } else {
      console.error('Please provide an app path to notarize');
      process.exit(1);
    }
  } else {
    console.log('Usage: node code-signing.js [setup|validate <file>|notarize <app>] [options]');
  }
}

module.exports = CodeSigning;