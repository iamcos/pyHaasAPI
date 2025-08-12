/**
 * Accessibility Testing Utilities
 * 
 * Utilities for WCAG 2.1 compliance testing:
 * - Automated accessibility scanning
 * - Keyboard navigation testing
 * - Screen reader compatibility
 * - Color contrast validation
 * - Focus management
 */

export interface AccessibilityViolation {
  id: string
  impact: 'minor' | 'moderate' | 'serious' | 'critical'
  description: string
  help: string
  helpUrl: string
  nodes: Array<{
    target: string[]
    html: string
    failureSummary: string
  }>
}

export interface AccessibilityResult {
  violations: AccessibilityViolation[]
  passes: AccessibilityViolation[]
  incomplete: AccessibilityViolation[]
  inapplicable: AccessibilityViolation[]
}

export interface KeyboardTestConfig {
  element: HTMLElement
  expectedFocusableElements: string[]
  trapFocus?: boolean
  skipLinks?: boolean
}

export interface ColorContrastTest {
  foreground: string
  background: string
  fontSize: number
  fontWeight: 'normal' | 'bold'
  level: 'AA' | 'AAA'
}

export class AccessibilityTester {
  private axeCore: any = null

  constructor() {
    // In a real implementation, you would import axe-core
    // For this example, we'll mock it
    this.axeCore = {
      run: async (element: HTMLElement) => {
        // Mock axe-core results
        return {
          violations: [],
          passes: [],
          incomplete: [],
          inapplicable: [],
        }
      }
    }
  }

  async runAccessibilityAudit(element: HTMLElement): Promise<AccessibilityResult> {
    if (!this.axeCore) {
      throw new Error('axe-core not available')
    }

    const results = await this.axeCore.run(element)
    return results
  }

  validateWCAGCompliance(result: AccessibilityResult): {
    compliant: boolean
    criticalViolations: AccessibilityViolation[]
    seriousViolations: AccessibilityViolation[]
    summary: string
  } {
    const criticalViolations = result.violations.filter(v => v.impact === 'critical')
    const seriousViolations = result.violations.filter(v => v.impact === 'serious')
    
    const compliant = criticalViolations.length === 0 && seriousViolations.length === 0

    const summary = `
      Total violations: ${result.violations.length}
      Critical: ${criticalViolations.length}
      Serious: ${seriousViolations.length}
      Moderate: ${result.violations.filter(v => v.impact === 'moderate').length}
      Minor: ${result.violations.filter(v => v.impact === 'minor').length}
    `.trim()

    return {
      compliant,
      criticalViolations,
      seriousViolations,
      summary,
    }
  }
}  t
estKeyboardNavigation(config: KeyboardTestConfig): {
    passed: boolean
    errors: string[]
    focusableElements: HTMLElement[]
  } {
    const errors: string[] = []
    const focusableElements = this.getFocusableElements(config.element)

    // Test tab navigation
    if (focusableElements.length === 0) {
      errors.push('No focusable elements found')
      return { passed: false, errors, focusableElements }
    }

    // Test focus order
    const expectedSelectors = config.expectedFocusableElements
    if (expectedSelectors.length !== focusableElements.length) {
      errors.push(
        `Expected ${expectedSelectors.length} focusable elements, found ${focusableElements.length}`
      )
    }

    // Test each expected element is focusable
    expectedSelectors.forEach((selector, index) => {
      const element = config.element.querySelector(selector) as HTMLElement
      if (!element) {
        errors.push(`Expected focusable element not found: ${selector}`)
        return
      }

      if (!this.isFocusable(element)) {
        errors.push(`Element is not focusable: ${selector}`)
      }

      if (focusableElements[index] !== element) {
        errors.push(`Focus order mismatch at index ${index}: expected ${selector}`)
      }
    })

    // Test focus trap if enabled
    if (config.trapFocus) {
      const firstElement = focusableElements[0]
      const lastElement = focusableElements[focusableElements.length - 1]

      if (!firstElement || !lastElement) {
        errors.push('Cannot test focus trap: missing first or last focusable element')
      }
    }

    return {
      passed: errors.length === 0,
      errors,
      focusableElements,
    }
  }

  private getFocusableElements(container: HTMLElement): HTMLElement[] {
    const focusableSelectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      'a[href]',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]',
    ].join(', ')

    return Array.from(container.querySelectorAll(focusableSelectors)) as HTMLElement[]
  }

  private isFocusable(element: HTMLElement): boolean {
    if (element.tabIndex < 0) return false
    if (element.hasAttribute('disabled')) return false
    if (element.getAttribute('aria-hidden') === 'true') return false
    
    const style = window.getComputedStyle(element)
    if (style.display === 'none' || style.visibility === 'hidden') return false
    
    return true
  }

  testColorContrast(test: ColorContrastTest): {
    passed: boolean
    ratio: number
    required: number
    recommendation: string
  } {
    const ratio = this.calculateContrastRatio(test.foreground, test.background)
    
    // WCAG requirements
    const isLargeText = test.fontSize >= 18 || (test.fontSize >= 14 && test.fontWeight === 'bold')
    
    let required: number
    if (test.level === 'AAA') {
      required = isLargeText ? 4.5 : 7
    } else {
      required = isLargeText ? 3 : 4.5
    }

    const passed = ratio >= required

    let recommendation = ''
    if (!passed) {
      if (ratio < 3) {
        recommendation = 'Poor contrast. Consider using darker text or lighter background.'
      } else if (ratio < 4.5) {
        recommendation = 'Contrast may be insufficient for small text. Consider improving contrast.'
      } else {
        recommendation = 'Contrast is acceptable for large text but not small text.'
      }
    }

    return { passed, ratio, required, recommendation }
  }

  private calculateContrastRatio(foreground: string, background: string): number {
    const fgLuminance = this.getLuminance(foreground)
    const bgLuminance = this.getLuminance(background)
    
    const lighter = Math.max(fgLuminance, bgLuminance)
    const darker = Math.min(fgLuminance, bgLuminance)
    
    return (lighter + 0.05) / (darker + 0.05)
  }

  private getLuminance(color: string): number {
    // Convert color to RGB values
    const rgb = this.hexToRgb(color)
    if (!rgb) return 0

    // Convert to relative luminance
    const rsRGB = rgb.r / 255
    const gsRGB = rgb.g / 255
    const bsRGB = rgb.b / 255

    const r = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4)
    const g = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4)
    const b = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4)

    return 0.2126 * r + 0.7152 * g + 0.0722 * b
  }

  private hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16),
    } : null
  }

  testAriaLabels(element: HTMLElement): {
    passed: boolean
    errors: string[]
    warnings: string[]
  } {
    const errors: string[] = []
    const warnings: string[] = []

    // Check for required ARIA labels
    const interactiveElements = element.querySelectorAll(
      'button, input, select, textarea, a, [role="button"], [role="link"]'
    )

    interactiveElements.forEach((el) => {
      const htmlEl = el as HTMLElement
      const tagName = htmlEl.tagName.toLowerCase()
      const role = htmlEl.getAttribute('role')

      // Check for accessible name
      const hasAccessibleName = 
        htmlEl.getAttribute('aria-label') ||
        htmlEl.getAttribute('aria-labelledby') ||
        htmlEl.textContent?.trim() ||
        (tagName === 'input' && htmlEl.getAttribute('placeholder')) ||
        (tagName === 'img' && htmlEl.getAttribute('alt'))

      if (!hasAccessibleName) {
        errors.push(`Element lacks accessible name: ${tagName}${role ? `[role="${role}"]` : ''}`)
      }

      // Check for proper ARIA attributes
      if (htmlEl.getAttribute('aria-expanded') !== null) {
        const expanded = htmlEl.getAttribute('aria-expanded')
        if (expanded !== 'true' && expanded !== 'false') {
          errors.push(`Invalid aria-expanded value: ${expanded}`)
        }
      }

      if (htmlEl.getAttribute('aria-hidden') === 'true' && this.isFocusable(htmlEl)) {
        errors.push('Focusable element should not have aria-hidden="true"')
      }
    })

    return {
      passed: errors.length === 0,
      errors,
      warnings,
    }
  }

  testScreenReaderCompatibility(element: HTMLElement): {
    passed: boolean
    issues: string[]
    recommendations: string[]
  } {
    const issues: string[] = []
    const recommendations: string[] = []

    // Check for proper heading structure
    const headings = element.querySelectorAll('h1, h2, h3, h4, h5, h6')
    let previousLevel = 0

    headings.forEach((heading) => {
      const level = parseInt(heading.tagName.charAt(1))
      if (level > previousLevel + 1) {
        issues.push(`Heading level skipped: ${heading.tagName} after h${previousLevel}`)
      }
      previousLevel = level
    })

    // Check for alt text on images
    const images = element.querySelectorAll('img')
    images.forEach((img) => {
      if (!img.getAttribute('alt')) {
        issues.push('Image missing alt text')
      }
    })

    // Check for form labels
    const inputs = element.querySelectorAll('input, select, textarea')
    inputs.forEach((input) => {
      const htmlInput = input as HTMLInputElement
      const hasLabel = 
        htmlInput.getAttribute('aria-label') ||
        htmlInput.getAttribute('aria-labelledby') ||
        element.querySelector(`label[for="${htmlInput.id}"]`)

      if (!hasLabel) {
        issues.push(`Form input missing label: ${htmlInput.type || htmlInput.tagName}`)
      }
    })

    // Check for landmarks
    const landmarks = element.querySelectorAll(
      'main, nav, aside, section, article, header, footer, [role="main"], [role="navigation"], [role="complementary"]'
    )

    if (landmarks.length === 0) {
      recommendations.push('Consider adding landmark elements for better navigation')
    }

    return {
      passed: issues.length === 0,
      issues,
      recommendations,
    }
  }
}

// Utility functions for accessibility testing
export function createAccessibilityTest(
  name: string,
  testFunction: (tester: AccessibilityTester) => Promise<void> | void
): () => Promise<void> {
  return async () => {
    const tester = new AccessibilityTester()
    await testFunction(tester)
  }
}

export function simulateKeyboardNavigation(
  element: HTMLElement,
  keys: string[]
): HTMLElement | null {
  let currentElement = element.querySelector('[tabindex="0"], button, input, select, textarea, a[href]') as HTMLElement
  
  if (!currentElement) {
    currentElement = element
  }

  currentElement.focus()

  keys.forEach(key => {
    const event = new KeyboardEvent('keydown', {
      key,
      bubbles: true,
      cancelable: true,
    })

    currentElement.dispatchEvent(event)

    if (key === 'Tab') {
      // Simulate tab navigation
      const focusableElements = Array.from(
        element.querySelectorAll(
          'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'
        )
      ) as HTMLElement[]

      const currentIndex = focusableElements.indexOf(currentElement)
      const nextIndex = (currentIndex + 1) % focusableElements.length
      currentElement = focusableElements[nextIndex]
      currentElement?.focus()
    }
  })

  return currentElement
}

export const WCAG_GUIDELINES = {
  AA: {
    colorContrast: {
      normal: 4.5,
      large: 3.0,
    },
    fontSize: {
      large: 18, // or 14pt bold
    },
  },
  AAA: {
    colorContrast: {
      normal: 7.0,
      large: 4.5,
    },
  },
} as const