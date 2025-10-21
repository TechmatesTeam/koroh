/**
 * Utility functions for testing responsive design
 */

export const viewports = {
  mobile: { width: 375, height: 667 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1024, height: 768 },
  largeDesktop: { width: 1440, height: 900 },
};

export const setViewport = (viewport: keyof typeof viewports) => {
  const { width, height } = viewports[viewport];
  
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
  
  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: height,
  });
  
  // Trigger resize event
  window.dispatchEvent(new Event('resize'));
};

export const testResponsiveClasses = (element: HTMLElement, expectedClasses: string[]) => {
  expectedClasses.forEach(className => {
    expect(element).toHaveClass(className);
  });
};

export const checkElementVisibility = (element: HTMLElement | null) => {
  if (!element) return false;
  
  const style = window.getComputedStyle(element);
  return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
};

export const mockMatchMedia = (query: string, matches: boolean = false) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((q) => ({
      matches: q === query ? matches : false,
      media: q,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
};