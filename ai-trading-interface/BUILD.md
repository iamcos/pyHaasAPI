# Build System Documentation

## Overview

The AI Trading Interface uses a comprehensive build system that handles development, testing, building, code signing, and distribution across multiple platforms.

## Quick Start

### Development
```bash
npm run dev:desktop          # Start development server with Tauri
npm run dev                  # Start web development server only
```

### Building
```bash
npm run build:desktop        # Build desktop application
npm run build:pipeline:prod  # Full production build pipeline
npm run release              # Complete release build with distribution
```

## Build Pipeline

The build pipeline consists of several stages:

1. **Pre-build Validation**
   - Node.js version check
   - Required files validation
   - Package.json validation

2. **Testing**
   - Type checking (`npm run type-check`)
   - Linting (`npm run lint`)
   - Unit tests (`npm run test`)
   - Performance tests (`npm run test:performance`)
   - Accessibility tests (`npm run test:accessibility`)

3. **Frontend Build**
   - TypeScript compilation
   - Vite bundling with optimization
   - Asset processing and minification

4. **Desktop Build**
   - Tauri application compilation
   - Platform-specific bundling
   - Code signing (if configured)

5. **Post-build Validation**
   - Artifact verification
   - Bundle size analysis
   - Build report generation

## Environment Configuration

### Development
- Source maps enabled
- Console logs preserved
- Mock data available
- Hot reloading enabled

### Staging
- Source maps enabled
- Balanced optimization
- Performance monitoring
- Error tracking

### Production
- Source maps disabled
- Aggressive optimization
- Console logs removed
- Full security features

## Code Signing

### macOS
Set the following environment variables:
```bash
export MACOS_SIGNING_IDENTITY="Developer ID Application: Your Name"
export MACOS_PROVISIONING_PROFILE="path/to/profile.provisionprofile"
export APPLE_ID="your-apple-id@example.com"
export APPLE_PASSWORD="app-specific-password"
export APPLE_TEAM_ID="TEAM123456"
```

### Windows
Set the following environment variables:
```bash
export WINDOWS_CERTIFICATE_THUMBPRINT="certificate-thumbprint"
export WINDOWS_TIMESTAMP_URL="http://timestamp.digicert.com"
```

### Linux
Set the following environment variables:
```bash
export LINUX_GPG_KEY="gpg-key-id"
```

## Distribution

The distribution system creates platform-specific packages:

- **macOS**: `.dmg` installer
- **Windows**: `.zip` archive with MSI installer
- **Linux**: `.tar.gz` archive with DEB package

### Creating Distribution
```bash
npm run create:distribution
```

This generates:
- Platform-specific packages
- Checksums for verification
- Release notes
- Update manifest

## Scripts Reference

### Build Scripts
- `npm run build` - Basic frontend build
- `npm run build:prod` - Production frontend build
- `npm run build:desktop` - Desktop application build
- `npm run build:pipeline` - Full build pipeline
- `npm run build:pipeline:prod` - Production pipeline
- `npm run build:pipeline:staging` - Staging pipeline

### Development Scripts
- `npm run dev` - Web development server
- `npm run dev:desktop` - Desktop development mode
- `npm run preview` - Preview production build

### Testing Scripts
- `npm run test` - Unit tests
- `npm run test:watch` - Watch mode testing
- `npm run test:coverage` - Coverage report
- `npm run test:integration` - Integration tests
- `npm run test:performance` - Performance tests
- `npm run test:accessibility` - Accessibility tests
- `npm run test:all` - All tests

### Quality Scripts
- `npm run lint` - ESLint checking
- `npm run type-check` - TypeScript validation

### Tauri Scripts
- `npm run tauri:dev` - Tauri development mode
- `npm run tauri:build` - Tauri build
- `npm run tauri:build:debug` - Debug Tauri build

### Utility Scripts
- `npm run setup:signing` - Setup code signing
- `npm run create:distribution` - Create distribution packages
- `npm run release` - Complete release process

## Build Configuration

### Vite Configuration
The Vite configuration (`vite.config.ts`) handles:
- TypeScript compilation
- Asset optimization
- Code splitting
- Environment variables
- Development server setup

### Tauri Configuration
The Tauri configuration (`src-tauri/tauri.conf.json`) handles:
- Application metadata
- Window configuration
- Security settings
- Bundle configuration
- Platform-specific settings

### Build Configuration
The build configuration (`build.config.js`) handles:
- Environment-specific settings
- Optimization levels
- Asset processing
- Bundle analysis

## Continuous Integration

The project includes GitHub Actions workflows for:
- Automated testing on pull requests
- Multi-platform builds
- Security scanning
- Automated releases

### Workflow Files
- `.github/workflows/build-and-release.yml` - Main CI/CD pipeline

## Troubleshooting

### Common Issues

1. **Build fails with missing dependencies**
   ```bash
   npm ci  # Clean install dependencies
   ```

2. **Tauri build fails**
   ```bash
   # Install Rust if not present
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # Update Rust
   rustup update
   ```

3. **Code signing fails**
   - Verify signing certificates are installed
   - Check environment variables are set correctly
   - Ensure proper permissions for keychain access

4. **Bundle size too large**
   - Enable bundle analyzer: `ANALYZE=true npm run build`
   - Review chunk splitting configuration
   - Optimize asset sizes

### Debug Mode

Enable verbose logging for build scripts:
```bash
npm run build:pipeline -- --verbose
```

## Performance Optimization

The build system includes several optimization strategies:

1. **Code Splitting**
   - Vendor chunks for third-party libraries
   - Feature-based chunks
   - Dynamic imports for lazy loading

2. **Asset Optimization**
   - Image compression and format conversion
   - Font subsetting and preloading
   - CSS minification and purging

3. **Bundle Analysis**
   - Size analysis and reporting
   - Dependency visualization
   - Performance metrics

4. **Caching**
   - Build cache for faster rebuilds
   - Asset fingerprinting
   - Service worker caching

## Security Considerations

1. **Content Security Policy (CSP)**
   - Configured for production builds
   - Prevents XSS attacks
   - Restricts resource loading

2. **Code Signing**
   - Ensures application integrity
   - Prevents tampering
   - Required for distribution

3. **Dependency Scanning**
   - Automated vulnerability checks
   - Regular security audits
   - Update notifications

## Support

For build system issues:
1. Check this documentation
2. Review error logs with verbose mode
3. Verify environment configuration
4. Check GitHub Issues for known problems