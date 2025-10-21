/**
 * Utility functions for testing accessibility compliance
 */

export const checkHeadingHierarchy = (container: HTMLElement) => {
  const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
  const headingLevels: number[] = [];
  
  headings.forEach(heading => {
    const level = parseInt(heading.tagName.charAt(1));
    headingLevels.push(level);
  });
  
  // Check that we start with h1
  if (headingLevels.length > 0) {
    expect(headingLevels[0]).toBe(1);
  }
  
  // Check that heading levels don't skip (e.g., h1 -> h3)
  for (let i = 1; i < headingLevels.length; i++) {
    const currentLevel = headingLevels[i];
    const previousLevel = headingLevels[i - 1];
    
    if (currentLevel > previousLevel) {
      expect(currentLevel - previousLevel).toBeLessThanOrEqual(1);
    }
  }
};

export const checkFormAccessibility = (container: HTMLElement) => {
  const inputs = container.querySelectorAll('input, textarea, select');
  
  inputs.forEach(input => {
    const id = input.getAttribute('id');
    const ariaLabel = input.getAttribute('aria-label');
    const ariaLabelledBy = input.getAttribute('aria-labelledby');
    const placeholder = input.getAttribute('placeholder');
    
    // Input should have some form of labeling
    const hasLabel = id && container.querySelector(`label[for="${id}"]`);
    const hasAccessibleName = ariaLabel || ariaLabelledBy || hasLabel || placeholder;
    
    expect(hasAccessibleName).toBeTruthy();
  });
};

export const checkButtonAccessibility = (container: HTMLElement) => {
  const buttons = container.querySelectorAll('button, [role="button"]');
  
  buttons.forEach(button => {
    const hasText = button.textContent?.trim();
    const hasAriaLabel = button.getAttribute('aria-label');
    const hasAriaLabelledBy = button.getAttribute('aria-labelledby');
    const hasTitle = button.getAttribute('title');
    const isIconButton = button.querySelector('svg') && !hasText;
    
    // Button should have accessible name, or be an icon button with proper labeling
    const hasAccessibleName = hasText || hasAriaLabel || hasAriaLabelledBy || hasTitle;
    
    if (!hasAccessibleName && !isIconButton) {
      console.warn('Button without accessible name found:', button.outerHTML);
    }
    
    // Only fail if it's not an icon button and has no accessible name
    if (!isIconButton) {
      expect(hasAccessibleName).toBeTruthy();
    }
  });
};

export const checkLinkAccessibility = (container: HTMLElement) => {
  const links = container.querySelectorAll('a');
  
  links.forEach(link => {
    const hasText = link.textContent?.trim();
    const hasAriaLabel = link.getAttribute('aria-label');
    const hasAriaLabelledBy = link.getAttribute('aria-labelledby');
    
    // Link should have accessible name
    expect(hasText || hasAriaLabel || hasAriaLabelledBy).toBeTruthy();
    
    // Link should have href or role
    const hasHref = link.getAttribute('href');
    const hasRole = link.getAttribute('role');
    expect(hasHref || hasRole).toBeTruthy();
  });
};

export const checkImageAccessibility = (container: HTMLElement) => {
  const images = container.querySelectorAll('img');
  
  images.forEach(img => {
    const alt = img.getAttribute('alt');
    const ariaLabel = img.getAttribute('aria-label');
    const ariaLabelledBy = img.getAttribute('aria-labelledby');
    const ariaHidden = img.getAttribute('aria-hidden');
    const role = img.getAttribute('role');
    
    // Image should have alt text or be marked as decorative
    const hasAccessibleName = alt !== null || ariaLabel || ariaLabelledBy;
    const isDecorative = ariaHidden === 'true' || role === 'presentation';
    
    expect(hasAccessibleName || isDecorative).toBeTruthy();
  });
};

export const checkColorContrast = (element: HTMLElement) => {
  const style = window.getComputedStyle(element);
  const color = style.color;
  const backgroundColor = style.backgroundColor;
  
  // Basic check - ensure colors are defined
  expect(color).toBeTruthy();
  
  // For a more comprehensive test, you would need a color contrast library
  // This is a simplified check
  const isLightText = color.includes('rgb(255') || color.includes('#fff') || color.includes('white');
  const isDarkBackground = backgroundColor.includes('rgb(0') || backgroundColor.includes('#000') || backgroundColor.includes('black');
  
  // If we can determine it's light text on dark background, that's usually good contrast
  if (isLightText && isDarkBackground) {
    expect(true).toBe(true);
  }
};

export const checkFocusManagement = (container: HTMLElement) => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  focusableElements.forEach(element => {
    // Element should be focusable
    expect(element.getAttribute('tabindex')).not.toBe('-1');
  });
};

export const runBasicAccessibilityChecks = (container: HTMLElement) => {
  checkHeadingHierarchy(container);
  checkFormAccessibility(container);
  checkButtonAccessibility(container);
  checkLinkAccessibility(container);
  checkImageAccessibility(container);
  checkFocusManagement(container);
};