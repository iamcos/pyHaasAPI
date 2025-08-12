# Testing Documentation

This directory contains comprehensive testing infrastructure for the AI-powered trading interface, covering unit tests, integration tests, performance tests, and accessibility tests.

## Test Structure

```
src/test/
├── README.md                          # This documentation
├── setup.ts                          # Test environment setup
├── utils/
│   └── testUtils.tsx                 # Testing utilities and helpers
├── mocks/                            # Mock implementations
│   ├── aiService.ts                  # AI service mocks
│   ├── tradingService.ts             # Trading service mocks
│   └── workflowService.ts            # Workflow service mocks
├── integration/                      # Integration tests
│   ├── mcpIntegration.test.ts        # MCP Server integration
│   ├── ragIntegration.test.ts        # RAG system integration
│   ├── websocketIntegration.test.ts  # WebSocket integration
│   └── runIntegrationTests.ts        # Integration test runner
├── performance/                      # Performance tests
│   ├── performanceUtils.ts           # Performance testing utilities
│   └── performance.test.ts           # Performance test suite
└── accessibility/                    # Accessibility tests
    ├── accessibilityUtils.ts         # Accessibility testing utilities
    └── accessibility.test.ts         # WCAG 2.1 compliance tests
```

## Test Categories

### 1. Unit Tests

**Location**: `src/components/**/__tests__/`, `src/services/**/__tests__/`

**Purpose**: Test individual components and services in isolation

**Coverage**:
- React components with Jest and React Testing Library
- AI integration with mock responses
- Workflow state machine testing and validation
- Service layer functionality

**Requirements Addressed**: 8.4

**Example**:
```bash
npm test                    # Run all unit tests
npm run test:watch         # Run tests in watch mode
npm run test:coverage      # Run tests with coverage report
```

### 2. Integration Tests

**Location**: `src/test/integration/`

**Purpose**: Test end-to-end functionality with real external services

**Coverage**:
- MCP Server integration (60+ endpoints)
- RAG system integration with MongoDB
- WebSocket real-time data flow testing
- Cross-service communication

**Requirements Addressed**: 9.1, 9.2, 9.4

**Services Required**:
- MCP Server (port 8080)
- RAG Service (port 8081)
- WebSocket Server (port 8082)

**Example**:
```bash
npm run test:integration           # Run all integration tests
npm run test:integration:mcp       # Run only MCP integration tests
npm run test:integration:rag       # Run only RAG integration tests
npm run test:integration:ws        # Run only WebSocket integration tests
```

### 3. Performance Tests

**Location**: `src/test/performance/`

**Purpose**: Validate performance requirements and identify bottlenecks

**Coverage**:
- Response time validation (< 200ms requirement)
- Load testing for 100+ concurrent strategies
- Memory usage monitoring
- Rendering performance optimization

**Requirements Addressed**: 8.2, 8.5

**Key Metrics**:
- Response time: < 200ms
- Memory usage: < 512MB
- Render time: < 100ms
- Throughput: > 10 req/s
- Error rate: < 1%

**Example**:
```bash
npm run test:performance    # Run performance test suite
```

### 4. Accessibility Tests

**Location**: `src/test/accessibility/`

**Purpose**: Ensure WCAG 2.1 compliance and inclusive design

**Coverage**:
- Automated accessibility scanning with axe-core
- Keyboard navigation testing
- Screen reader compatibility
- Color contrast validation (AA/AAA levels)
- ARIA labels and attributes
- Focus management

**Requirements Addressed**: 10.4

**Standards**:
- WCAG 2.1 Level AA compliance
- Keyboard navigation support
- Screen reader compatibility
- Color contrast ratios (4.5:1 normal, 3:1 large text)

**Example**:
```bash
npm run test:accessibility  # Run accessibility test suite
```

## Test Configuration

### Vitest Configuration

The project uses Vitest for testing with the following configuration:

```typescript
// vitest.config.ts
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        'dist/',
      ],
    },
  },
})
```

### Test Environment Setup

The test environment includes:

- **JSDOM**: Browser environment simulation
- **Mock APIs**: IndexedDB, WebSocket, Speech Recognition
- **Test Utilities**: Custom render functions with providers
- **Global Mocks**: Zustand stores, service layers

## Running Tests

### All Tests
```bash
npm run test:all           # Run unit, performance, and accessibility tests
```

### Individual Test Suites
```bash
npm test                   # Unit tests only
npm run test:performance   # Performance tests only
npm run test:accessibility # Accessibility tests only
npm run test:integration   # Integration tests (requires services)
```

### Development Workflow
```bash
npm run test:watch         # Watch mode for development
npm run test:ui            # Interactive test UI
npm run test:coverage      # Coverage report
```

## Performance Thresholds

The following performance thresholds are enforced:

| Metric | Threshold | Requirement |
|--------|-----------|-------------|
| Response Time | < 200ms | 8.2 |
| Memory Usage | < 512MB | 8.5 |
| Render Time | < 100ms | UI Performance |
| Throughput | > 10 req/s | Load Handling |
| Error Rate | < 1% | Reliability |

## Accessibility Standards

The following accessibility standards are enforced:

| Standard | Level | Requirement |
|----------|-------|-------------|
| WCAG 2.1 | AA | 10.4 |
| Color Contrast | 4.5:1 (normal), 3:1 (large) | Visual |
| Keyboard Navigation | Full support | Motor |
| Screen Reader | Compatible | Visual |
| Focus Management | Proper indicators | Motor |

## Mock Services

### AI Service Mock
```typescript
export const mockAIService = {
  generateResponse: vi.fn().mockResolvedValue({
    content: 'Mock AI response',
    confidence: 0.85,
    chainOfThought: [...],
  }),
  analyzeStrategy: vi.fn().mockResolvedValue({...}),
  generateHaasScript: vi.fn().mockResolvedValue({...}),
}
```

### Trading Service Mock
```typescript
export const mockTradingService = {
  getMarkets: vi.fn().mockResolvedValue([...]),
  getPortfolio: vi.fn().mockResolvedValue({...}),
  getBots: vi.fn().mockResolvedValue([...]),
}
```

## Continuous Integration

Tests are designed to run in CI/CD environments with the following considerations:

- **Headless Mode**: All tests run without GUI dependencies
- **Service Detection**: Integration tests skip unavailable services
- **Performance Baselines**: Consistent performance measurement
- **Accessibility Automation**: Automated WCAG compliance checking

## Troubleshooting

### Common Issues

1. **Integration Tests Failing**
   - Ensure required services are running
   - Check service health endpoints
   - Verify network connectivity

2. **Performance Tests Inconsistent**
   - Run on consistent hardware
   - Close other applications
   - Use performance mode if available

3. **Accessibility Tests Failing**
   - Check for missing ARIA labels
   - Verify color contrast ratios
   - Test keyboard navigation manually

### Debug Commands

```bash
# Debug specific test
npm test -- --reporter=verbose ComponentName

# Debug integration tests
npm run test:integration -- --service=mcp --verbose

# Debug performance with profiling
npm run test:performance -- --reporter=verbose

# Debug accessibility with detailed output
npm run test:accessibility -- --reporter=verbose
```

## Contributing

When adding new tests:

1. **Follow Naming Conventions**: `*.test.ts` for unit tests, `*Integration.test.ts` for integration tests
2. **Use Appropriate Mocks**: Mock external dependencies, test real functionality
3. **Document Requirements**: Reference specific requirements in test descriptions
4. **Maintain Performance**: Ensure tests run efficiently
5. **Update Documentation**: Keep this README current with changes

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [axe-core Accessibility Testing](https://github.com/dequelabs/axe-core)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)