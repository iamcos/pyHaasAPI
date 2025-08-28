#!/usr/bin/env node

/**
 * Distribution Setup and Management
 * Handles packaging and distribution of the application
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class Distribution {
  constructor(options = {}) {
    this.platform = process.platform;
    this.environment = options.environment || 'production';
    this.version = options.version || this.getVersionFromPackage();
    this.verbose = options.verbose || false;
    this.outputDir = options.outputDir || 'dist/releases';
  }

  log(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
    
    if (this.verbose || level === 'error') {
      console.log(`${prefix} ${message}`);
    }
  }

  getVersionFromPackage() {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    return packageJson.version;
  }

  async createDistribution() {
    this.log('Creating distribution packages...', 'info');
    
    try {
      // Ensure output directory exists
      if (!fs.existsSync(this.outputDir)) {
        fs.mkdirSync(this.outputDir, { recursive: true });
      }
      
      // Copy build artifacts
      await this.copyBuildArtifacts();
      
      // Create platform-specific packages
      await this.createPlatformPackages();
      
      // Generate checksums
      await this.generateChecksums();
      
      // Create release notes
      await this.createReleaseNotes();
      
      // Generate update manifest
      await this.generateUpdateManifest();
      
      this.log('Distribution packages created successfully', 'info');
      
    } catch (error) {
      this.log(`Distribution creation failed: ${error.message}`, 'error');
      throw error;
    }
  }

  async copyBuildArtifacts() {
    this.log('Copying build artifacts...', 'info');
    
    const bundlePath = 'src-tauri/target/release/bundle';
    
    if (!fs.existsSync(bundlePath)) {
      throw new Error('Build artifacts not found. Please run the build process first.');
    }
    
    // Copy platform-specific bundles
    const platformDirs = fs.readdirSync(bundlePath);
    
    for (const platformDir of platformDirs) {
      const sourcePath = path.join(bundlePath, platformDir);
      const destPath = path.join(this.outputDir, platformDir);
      
      if (fs.statSync(sourcePath).isDirectory()) {
        this.copyDirectory(sourcePath, destPath);
        this.log(`Copied ${platformDir} artifacts`, 'info');
      }
    }
  }

  async createPlatformPackages() {
    this.log('Creating platform-specific packages...', 'info');
    
    switch (this.platform) {
      case 'darwin':
        await this.createMacOSPackage();
        break;
      case 'win32':
        await this.createWindowsPackage();
        break;
      case 'linux':
        await this.createLinuxPackage();
        break;
      default:
        this.log(`Platform-specific packaging not implemented for: ${this.platform}`, 'warn');
    }
  }

  async createMacOSPackage() {
    this.log('Creating macOS package...', 'info');
    
    const appPath = path.join(this.outputDir, 'macos', 'AI Trading Interface.app');
    const dmgPath = path.join(this.outputDir, `AI-Trading-Interface-${this.version}-macos.dmg`);
    
    if (fs.existsSync(appPath)) {
      try {
        // Create DMG
        execSync(`hdiutil create -volname "AI Trading Interface" -srcfolder "${appPath}" -ov -format UDZO "${dmgPath}"`, {
          stdio: this.verbose ? 'inherit' : 'pipe'
        });
        
        this.log(`macOS DMG created: ${dmgPath}`, 'info');
      } catch (error) {
        this.log(`DMG creation failed: ${error.message}`, 'warn');
      }
    }
  }

  async createWindowsPackage() {
    this.log('Creating Windows package...', 'info');
    
    const msiPath = path.join(this.outputDir, 'msi');
    const zipPath = path.join(this.outputDir, `AI-Trading-Interface-${this.version}-windows.zip`);
    
    if (fs.existsSync(msiPath)) {
      try {
        // Create ZIP archive
        execSync(`powershell Compress-Archive -Path "${msiPath}\\*" -DestinationPath "${zipPath}"`, {
          stdio: this.verbose ? 'inherit' : 'pipe'
        });
        
        this.log(`Windows ZIP created: ${zipPath}`, 'info');
      } catch (error) {
        this.log(`ZIP creation failed: ${error.message}`, 'warn');
      }
    }
  }

  async createLinuxPackage() {
    this.log('Creating Linux package...', 'info');
    
    const debPath = path.join(this.outputDir, 'deb');
    const tarPath = path.join(this.outputDir, `AI-Trading-Interface-${this.version}-linux.tar.gz`);
    
    if (fs.existsSync(debPath)) {
      try {
        // Create tar.gz archive
        execSync(`tar -czf "${tarPath}" -C "${debPath}" .`, {
          stdio: this.verbose ? 'inherit' : 'pipe'
        });
        
        this.log(`Linux tar.gz created: ${tarPath}`, 'info');
      } catch (error) {
        this.log(`tar.gz creation failed: ${error.message}`, 'warn');
      }
    }
  }

  async generateChecksums() {
    this.log('Generating checksums...', 'info');
    
    const checksumFile = path.join(this.outputDir, 'checksums.txt');
    const checksums = [];
    
    const files = this.getAllFiles(this.outputDir).filter(file => 
      !file.endsWith('checksums.txt') && 
      !file.endsWith('.json') &&
      (file.endsWith('.dmg') || file.endsWith('.zip') || file.endsWith('.tar.gz') || file.endsWith('.msi') || file.endsWith('.deb'))
    );
    
    for (const file of files) {
      const hash = this.calculateFileHash(file);
      const relativePath = path.relative(this.outputDir, file);
      checksums.push(`${hash}  ${relativePath}`);
      this.log(`Generated checksum for ${relativePath}`, 'info');
    }
    
    fs.writeFileSync(checksumFile, checksums.join('\n') + '\n');
    this.log(`Checksums written to: ${checksumFile}`, 'info');
  }

  async createReleaseNotes() {
    this.log('Creating release notes...', 'info');
    
    const releaseNotesPath = path.join(this.outputDir, 'release-notes.md');
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    
    const releaseNotes = `# AI Trading Interface v${this.version}

## Release Information

- **Version**: ${this.version}
- **Release Date**: ${new Date().toISOString().split('T')[0]}
- **Build Environment**: ${this.environment}
- **Platform**: ${this.platform}

## Features

- AI-powered trading strategy development
- Real-time market data visualization
- Advanced risk management console
- Chain-of-thought optimization workflows
- Comprehensive analytics and reporting

## Installation

### macOS
1. Download the \`.dmg\` file
2. Open the DMG and drag the application to Applications folder
3. Launch the application

### Windows
1. Download the \`.zip\` file
2. Extract the contents
3. Run the installer (MSI file)

### Linux
1. Download the \`.tar.gz\` file
2. Extract: \`tar -xzf AI-Trading-Interface-${this.version}-linux.tar.gz\`
3. Install the DEB package: \`sudo dpkg -i *.deb\`

## System Requirements

- **Operating System**: macOS 10.13+, Windows 10+, or Linux (Ubuntu 18.04+)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB available space
- **Network**: Internet connection required for real-time data

## Support

For support and documentation, please visit our GitHub repository or contact support.

## Checksums

Please verify your download using the checksums provided in \`checksums.txt\`.
`;

    fs.writeFileSync(releaseNotesPath, releaseNotes);
    this.log(`Release notes created: ${releaseNotesPath}`, 'info');
  }

  async generateUpdateManifest() {
    this.log('Generating update manifest...', 'info');
    
    const manifestPath = path.join(this.outputDir, 'update-manifest.json');
    
    const manifest = {
      version: this.version,
      releaseDate: new Date().toISOString(),
      platforms: {},
      changelog: `Release v${this.version}`,
      minimumVersion: '1.0.0'
    };
    
    // Add platform-specific download URLs and checksums
    const files = this.getAllFiles(this.outputDir);
    
    for (const file of files) {
      const filename = path.basename(file);
      const checksum = this.calculateFileHash(file);
      
      if (filename.includes('macos') && filename.endsWith('.dmg')) {
        manifest.platforms.darwin = {
          url: filename,
          checksum: checksum,
          size: fs.statSync(file).size
        };
      } else if (filename.includes('windows') && filename.endsWith('.zip')) {
        manifest.platforms.win32 = {
          url: filename,
          checksum: checksum,
          size: fs.statSync(file).size
        };
      } else if (filename.includes('linux') && filename.endsWith('.tar.gz')) {
        manifest.platforms.linux = {
          url: filename,
          checksum: checksum,
          size: fs.statSync(file).size
        };
      }
    }
    
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
    this.log(`Update manifest created: ${manifestPath}`, 'info');
  }

  copyDirectory(source, destination) {
    if (!fs.existsSync(destination)) {
      fs.mkdirSync(destination, { recursive: true });
    }
    
    const files = fs.readdirSync(source);
    
    for (const file of files) {
      const sourcePath = path.join(source, file);
      const destPath = path.join(destination, file);
      
      if (fs.statSync(sourcePath).isDirectory()) {
        this.copyDirectory(sourcePath, destPath);
      } else {
        fs.copyFileSync(sourcePath, destPath);
      }
    }
  }

  getAllFiles(dirPath, arrayOfFiles = []) {
    if (!fs.existsSync(dirPath)) {
      return arrayOfFiles;
    }
    
    const files = fs.readdirSync(dirPath);
    
    files.forEach(file => {
      const filePath = path.join(dirPath, file);
      if (fs.statSync(filePath).isDirectory()) {
        arrayOfFiles = this.getAllFiles(filePath, arrayOfFiles);
      } else {
        arrayOfFiles.push(filePath);
      }
    });
    
    return arrayOfFiles;
  }

  calculateFileHash(filePath) {
    const fileBuffer = fs.readFileSync(filePath);
    const hashSum = crypto.createHash('sha256');
    hashSum.update(fileBuffer);
    return hashSum.digest('hex');
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
    } else if (arg === '--version' || arg === '-v') {
      options.version = args[++i];
    } else if (arg === '--output' || arg === '-o') {
      options.outputDir = args[++i];
    } else if (arg === '--verbose') {
      options.verbose = true;
    }
  }
  
  const distribution = new Distribution(options);
  distribution.createDistribution();
}

module.exports = Distribution;