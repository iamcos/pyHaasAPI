/**
 * Build Configuration for AI Trading Interface
 * Handles different build environments and optimization settings
 */

const path = require('path');

const buildConfig = {
  // Environment configurations
  environments: {
    development: {
      sourcemap: true,
      minify: false,
      dropConsole: false,
      optimization: 'minimal'
    },
    staging: {
      sourcemap: true,
      minify: true,
      dropConsole: false,
      optimization: 'balanced'
    },
    production: {
      sourcemap: false,
      minify: true,
      dropConsole: true,
      optimization: 'aggressive'
    }
  },

  // Build targets
  targets: {
    web: {
      outDir: 'dist',
      format: 'es',
      target: 'esnext'
    },
    desktop: {
      outDir: 'dist',
      format: 'es',
      target: 'esnext',
      tauri: true
    }
  },

  // Optimization settings
  optimization: {
    minimal: {
      treeshake: false,
      manualChunks: false,
      compress: false
    },
    balanced: {
      treeshake: true,
      manualChunks: true,
      compress: true,
      chunkSizeLimit: 1000
    },
    aggressive: {
      treeshake: true,
      manualChunks: true,
      compress: true,
      chunkSizeLimit: 500,
      splitVendorChunks: true,
      inlineStyles: true
    }
  },

  // Asset optimization
  assets: {
    images: {
      formats: ['webp', 'avif', 'png'],
      quality: 85,
      progressive: true
    },
    fonts: {
      preload: ['Inter', 'JetBrains Mono'],
      display: 'swap'
    }
  },

  // Bundle analysis
  analysis: {
    enabled: process.env.ANALYZE === 'true',
    outputDir: 'dist/analysis',
    formats: ['html', 'json']
  }
};

module.exports = buildConfig;