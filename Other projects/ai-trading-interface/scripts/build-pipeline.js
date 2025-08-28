#!/usr/bin/env node

/**
 * Automated Build and Packaging Pipeline
 * Handles the complete build process with validation, optimization, and packaging
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const buildConfig = require('../build.config.js');

class BuildPipeline {
  constructor(options = {}) {
    this.environment = options.environment || 'production';
    this.target = options.target || 'desktop';
    this.skipTests = options.skipTests || false;
    this.verbose = options.verbose || false;
    this.config = buildConfig;
  }

  log(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
    
    if (this.verbose || level === 'error') {
      console.log(`${prefix} ${message}`);
    }
  }

  async run() {
    try {
      this.log('Starting build pipeline...', 'info');
      
      // Step 1: Pre-build validation
      await this.preBuildValidation();
      
      // Step 2: Clean previous builds
      await this.cleanBuild();
      
      // Step 3: Run tests (if not skipped)
      if (!this.skipTests) {
        await this.runTests();
      }
      
      // Step 4: Build frontend
      await this.buildFrontend();
      
      // Step 5: Build desktop app (if target is desktop)
      if (this.target === 'desktop') {
        await this.buildDesktop();
      }
      
      // Step 6: Post-build validation
      await this.postBuildValidation();
      
      // Step 7: Generate build report
      await this.generateBuildReport();
      
      this.log('Build pipeline completed successfully!', 'info');
      
    } catch (error) {
      this.log(`Build pipeline failed: ${error.message}`, 'error');
      process.exit(1);
    }
  }

  async preBuildValidation() {
    this.log('Running pre-build validation...', 'info');
    
    // Check Node.js version
    const nodeVersion = process.version;
    this.log(`Node.js version: ${nodeVersion}`, 'info');
    
    // Check if required files exist
    const requiredFiles = [
      'package.json',
      'tsconfig.json',
      'vite.config.ts',
      'src-tauri/tauri.conf.json'
    ];
    
    for (const file of requiredFiles) {
      if (!fs.existsSync(file)) {
        throw new Error(`Required file missing: ${file}`);
      }
    }
    
    // Validate package.json
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    if (!packageJson.name || !packageJson.version) {
      throw new Error('Invalid package.json: missing name or version');
    }
    
    this.log('Pre-build validation passed', 'info');
  }

  async cleanBuild() {
    this.log('Cleaning previous builds...', 'info');
    
    try {
      execSync('rm -rf dist', { stdio: this.verbose ? 'inherit' : 'pipe' });
      execSync('rm -rf src-tauri/target', { stdio: this.verbose ? 'inherit' : 'pipe' });
      this.log('Build directories cleaned', 'info');
    } catch (error) {
      this.log('Warning: Could not clean all build directories', 'warn');
    }
  }

  async runTests() {
    this.log('Running test suite...', 'info');
    
    try {
      // Type checking
      execSync('npm run type-check', { stdio: this.verbose ? 'inherit' : 'pipe' });
      this.log('Type checking passed', 'info');
      
      // Linting
      execSync('npm run lint', { stdio: this.verbose ? 'inherit' : 'pipe' });
      this.log('Linting passed', 'info');
      
      // Unit tests
      execSync('npm run test', { stdio: this.verbose ? 'inherit' : 'pipe' });
      this.log('Unit tests passed', 'info');
      
      // Performance tests
      execSync('npm run test:performance', { stdio: this.verbose ? 'inherit' : 'pipe' });
      this.log('Performance tests passed', 'info');
      
      // Accessibility tests
      execSync('npm run test:accessibility', { stdio: this.verbose ? 'inherit' : 'pipe' });
      this.log('Accessibility tests passed', 'info');
      
    } catch (error) {
      throw new Error(`Tests failed: ${error.message}`);
    }
  }

  async buildFrontend() {
    this.log('Building frontend...', 'info');
    
    try {
      const buildCommand = this.environment === 'production' 
        ? 'npm run build:prod' 
        : 'npm run build';
      
      execSync(buildCommand, { 
        stdio: this.verbose ? 'inherit' : 'pipe',
        env: { 
          ...process.env, 
          NODE_ENV: this.environment,
          VITE_BUILD_TARGET: this.target
        }
      });
      
      this.log('Frontend build completed', 'info');
    } catch (error) {
      throw new Error(`Frontend build failed: ${error.message}`);
    }
  }

  async buildDesktop() {
    this.log('Building desktop application...', 'info');
    
    try {
      const buildCommand = this.environment === 'production' 
        ? 'npx tauri build' 
        : 'npx tauri build --debug';
      
      execSync(buildCommand, { 
        stdio: this.verbose ? 'inherit' : 'pipe',
        env: { 
          ...process.env, 
          TAURI_ENV: this.environment
        }
      });
      
      this.log('Desktop application build completed', 'info');
    } catch (error) {
      throw new Error(`Desktop build failed: ${error.message}`);
    }
  }

  async postBuildValidation() {
    this.log('Running post-build validation...', 'info');
    
    // Check if build artifacts exist
    const requiredArtifacts = ['dist/index.html'];
    
    if (this.target === 'desktop') {
      // Add platform-specific artifacts
      const platform = process.platform;
      if (platform === 'darwin') {
        requiredArtifacts.push('src-tauri/target/release/bundle/macos');
      } else if (platform === 'win32') {
        requiredArtifacts.push('src-tauri/target/release/bundle/msi');
      } else if (platform === 'linux') {
        requiredArtifacts.push('src-tauri/target/release/bundle/deb');
      }
    }
    
    for (const artifact of requiredArtifacts) {
      if (!fs.existsSync(artifact)) {
        this.log(`Warning: Expected artifact not found: ${artifact}`, 'warn');
      }
    }
    
    // Validate bundle size
    const distStats = this.getDirectorySize('dist');
    this.log(`Bundle size: ${(distStats / 1024 / 1024).toFixed(2)} MB`, 'info');
    
    if (distStats > 50 * 1024 * 1024) { // 50MB threshold
      this.log('Warning: Bundle size is quite large', 'warn');
    }
    
    this.log('Post-build validation completed', 'info');
  }

  async generateBuildReport() {
    this.log('Generating build report...', 'info');
    
    const report = {
      timestamp: new Date().toISOString(),
      environment: this.environment,
      target: this.target,
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch,
      buildSize: this.getDirectorySize('dist'),
      artifacts: this.listArtifacts()
    };
    
    const reportPath = `dist/build-report-${Date.now()}.json`;
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    this.log(`Build report generated: ${reportPath}`, 'info');
  }

  getDirectorySize(dirPath) {
    let totalSize = 0;
    
    if (!fs.existsSync(dirPath)) {
      return 0;
    }
    
    const files = fs.readdirSync(dirPath);
    
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      const stats = fs.statSync(filePath);
      
      if (stats.isDirectory()) {
        totalSize += this.getDirectorySize(filePath);
      } else {
        totalSize += stats.size;
      }
    }
    
    return totalSize;
  }

  listArtifacts() {
    const artifacts = [];
    
    if (fs.existsSync('dist')) {
      const distFiles = fs.readdirSync('dist');
      artifacts.push(...distFiles.map(f => `dist/${f}`));
    }
    
    if (fs.existsSync('src-tauri/target/release/bundle')) {
      const bundleFiles = this.getAllFiles('src-tauri/target/release/bundle');
      artifacts.push(...bundleFiles);
    }
    
    return artifacts;
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
}

// CLI interface
if (require.main === module) {
  const args = process.argv.slice(2);
  const options = {};
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg === '--environment' || arg === '-e') {
      options.environment = args[++i];
    } else if (arg === '--target' || arg === '-t') {
      options.target = args[++i];
    } else if (arg === '--skip-tests') {
      options.skipTests = true;
    } else if (arg === '--verbose' || arg === '-v') {
      options.verbose = true;
    }
  }
  
  const pipeline = new BuildPipeline(options);
  pipeline.run();
}

module.exports = BuildPipeline;