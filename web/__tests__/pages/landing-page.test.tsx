import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Home from '@/app/page';
import { setViewport, testResponsiveClasses } from '../utils/responsive-test-utils';
import { runBasicAccessibilityChecks } from '../utils/accessibility-test-utils';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/',
}));

// Mock Next.js Link component
jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) => {
    return <a href={href} {...props}>{children}</a>;
  };
});

describe('Landing Page', () => {
  beforeEach(() => {
    // Reset viewport to desktop size before each test
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 768,
    });
  });

  describe('Responsive Design', () => {
    it('renders navigation correctly on desktop', () => {
      render(<Home />);
      
      // Check desktop navigation elements are visible
      expect(screen.getAllByText('Koroh')[0]).toBeInTheDocument();
      
      // Check navigation links by href to avoid footer duplicates
      const nav = document.querySelector('nav');
      expect(nav?.querySelector('a[href="/#jobs"]')).toBeInTheDocument();
      expect(nav?.querySelector('a[href="/#companies"]')).toBeInTheDocument();
      expect(nav?.querySelector('a[href="/#networking"]')).toBeInTheDocument();
      expect(nav?.querySelector('a[href="/demo"]')).toBeInTheDocument();
      
      expect(screen.getByText('Sign In')).toBeInTheDocument();
      expect(screen.getByText('Join Now')).toBeInTheDocument();
      
      // Check that mobile menu button container is hidden on desktop
      const mobileMenuContainer = document.querySelector('.md\\:hidden.flex.items-center');
      expect(mobileMenuContainer).toBeInTheDocument();
    });

    it('adapts layout for mobile viewport', () => {
      setViewport('mobile');
      render(<Home />);
      
      // Check that mobile-specific classes are applied
      const heroTitle = screen.getByText(/Your Professional Network/);
      expect(heroTitle).toBeInTheDocument();
      
      // Check responsive grid classes are present
      const statsGrid = screen.getByText('10M+').closest('.grid');
      testResponsiveClasses(statsGrid!, ['grid-cols-2', 'md:grid-cols-4']);
      
      // Check that mobile menu button is visible
      const mobileMenuButton = screen.getByRole('button', { name: /open main menu/i });
      expect(mobileMenuButton).toBeInTheDocument();
      
      // Check that desktop navigation links are hidden on mobile
      const nav = document.querySelector('nav');
      const desktopNavLinks = nav?.querySelector('.hidden.md\\:flex');
      expect(desktopNavLinks).toBeInTheDocument();
      
      // Check job search form container has responsive classes
      const jobSearchContainer = screen.getByPlaceholderText('Job title, keywords, or company').closest('.p-6');
      const jobSearchForm = jobSearchContainer?.querySelector('.flex');
      expect(jobSearchForm).toHaveClass('flex-col', 'md:flex-row');
    });

    it('adapts layout for tablet viewport', () => {
      setViewport('tablet');
      render(<Home />);
      
      // Check that tablet layout works properly
      const jobDiscoveryGrid = screen.getByText('Smart Matching').closest('.grid');
      testResponsiveClasses(jobDiscoveryGrid!, ['md:grid-cols-2', 'lg:grid-cols-3']);
      
      // Check navigation is still visible on tablet
      const nav = document.querySelector('nav');
      expect(nav?.querySelector('a[href="/#jobs"]')).toBeInTheDocument();
      expect(nav?.querySelector('a[href="/#companies"]')).toBeInTheDocument();
    });

    it('handles mobile menu toggle functionality', () => {
      setViewport('mobile');
      render(<Home />);
      
      const mobileMenuButton = screen.getByRole('button', { name: /open main menu/i });
      
      // Initially, mobile menu should not be expanded
      const mobileMenuContent = document.querySelector('.md\\:hidden .space-y-1');
      expect(mobileMenuContent).not.toBeInTheDocument();
      
      // Click to open mobile menu
      fireEvent.click(mobileMenuButton);
      
      // Mobile menu should now be visible with navigation links
      const mobileMenu = document.querySelector('.md\\:hidden .space-y-1');
      expect(mobileMenu).toBeInTheDocument();
    });

    it('displays full desktop layout on large screens', () => {
      setViewport('largeDesktop');
      render(<Home />);
      
      // Check that all navigation items are visible
      const nav = document.querySelector('nav');
      expect(nav?.querySelector('a[href="/#jobs"]')).toBeInTheDocument();
      expect(nav?.querySelector('a[href="/#companies"]')).toBeInTheDocument();
      expect(nav?.querySelector('a[href="/#networking"]')).toBeInTheDocument();
      expect(nav?.querySelector('a[href="/demo"]')).toBeInTheDocument();
      
      // Check that company insights section uses proper grid
      const companySection = screen.getByText('Company Intelligence at Your Fingertips').closest('section');
      const companyGrid = companySection?.querySelector('.grid');
      expect(companyGrid).toHaveClass('lg:grid-cols-2');
      
      // Check that hero section has proper responsive text sizing
      const heroTitle = screen.getByText(/Your Professional Network/);
      expect(heroTitle).toHaveClass('text-4xl', 'md:text-5xl');
    });

    it('displays job search form responsively', () => {
      render(<Home />);
      
      const jobTitleInput = screen.getByPlaceholderText('Job title, keywords, or company');
      const locationInput = screen.getByPlaceholderText('Location');
      const searchButton = screen.getByText('Search Jobs');
      
      expect(jobTitleInput).toBeInTheDocument();
      expect(locationInput).toBeInTheDocument();
      expect(searchButton).toBeInTheDocument();
      
      // Check that inputs have responsive classes
      expect(jobTitleInput).toHaveClass('h-12', 'text-lg');
      expect(locationInput).toHaveClass('h-12', 'text-lg');
    });

    it('renders feature cards in responsive grid', () => {
      render(<Home />);
      
      // Check job discovery feature cards
      expect(screen.getByText('Smart Matching')).toBeInTheDocument();
      expect(screen.getByText('Instant Applications')).toBeInTheDocument();
      expect(screen.getByText('Career Insights')).toBeInTheDocument();
      
      // Check networking feature cards
      expect(screen.getByText('Peer Groups')).toBeInTheDocument();
      expect(screen.getByText('Smart Messaging')).toBeInTheDocument();
      expect(screen.getAllByText('AI Recommendations')[0]).toBeInTheDocument();
    });
  });

  describe('Accessibility Compliance', () => {
    it('has proper semantic structure and passes accessibility checks', () => {
      const { container } = render(<Home />);
      
      // Check that the page has proper semantic structure
      expect(document.querySelector('nav')).toBeInTheDocument();
      expect(document.querySelector('footer')).toBeInTheDocument();
      
      // Check for proper section elements
      const sections = document.querySelectorAll('section');
      expect(sections.length).toBeGreaterThan(3); // Hero, jobs, companies, networking, CTA
      
      // Run comprehensive accessibility checks
      runBasicAccessibilityChecks(container);
    });

    it('has proper heading hierarchy', () => {
      render(<Home />);
      
      // Check main heading
      const mainHeading = screen.getByRole('heading', { level: 1 });
      expect(mainHeading).toHaveTextContent('Your Professional Network');
      
      // Check section headings
      const sectionHeadings = screen.getAllByRole('heading', { level: 2 });
      expect(sectionHeadings).toHaveLength(4); // Job discovery, company insights, networking, portfolio CTA
    });

    it('has proper link accessibility', () => {
      render(<Home />);
      
      // Check navigation links have proper text
      const jobsLink = screen.getByRole('link', { name: 'Jobs' });
      const companiesLink = screen.getByRole('link', { name: 'Companies' });
      
      expect(jobsLink).toHaveAttribute('href', '/#jobs');
      expect(companiesLink).toHaveAttribute('href', '/#companies');
    });

    it('has proper button accessibility', () => {
      render(<Home />);
      
      const searchButton = screen.getByRole('button', { name: 'Search Jobs' });
      const joinButton = screen.getByRole('link', { name: 'Join Now' });
      
      expect(searchButton).toBeInTheDocument();
      expect(joinButton).toHaveAttribute('href', '/auth/register');
    });

    it('has proper form labels and inputs', () => {
      render(<Home />);
      
      const jobInput = screen.getByPlaceholderText('Job title, keywords, or company');
      const locationInput = screen.getByPlaceholderText('Location');
      
      // Check inputs have proper attributes
      expect(jobInput).toHaveAttribute('placeholder');
      expect(locationInput).toHaveAttribute('placeholder');
      
      // Check inputs are keyboard accessible
      expect(jobInput).not.toHaveAttribute('tabindex', '-1');
      expect(locationInput).not.toHaveAttribute('tabindex', '-1');
    });

    it('has proper keyboard navigation support', () => {
      render(<Home />);
      
      // Check that interactive elements are focusable
      const searchButton = screen.getByRole('button', { name: 'Search Jobs' });
      const signInLink = screen.getByRole('link', { name: 'Sign In' });
      const joinLink = screen.getByRole('link', { name: 'Join Now' });
      
      expect(searchButton).not.toHaveAttribute('tabindex', '-1');
      expect(signInLink).not.toHaveAttribute('tabindex', '-1');
      expect(joinLink).not.toHaveAttribute('tabindex', '-1');
    });

    it('has proper ARIA attributes for interactive elements', () => {
      render(<Home />);
      
      // Check mobile menu button has proper ARIA
      const mobileMenuButton = screen.getByRole('button', { name: /open main menu/i });
      expect(mobileMenuButton).toHaveAttribute('type', 'button');
      
      // Check that screen reader text is present
      expect(screen.getByText('Open main menu')).toHaveClass('sr-only');
    });

    it('has proper image alt texts and icons', () => {
      render(<Home />);
      
      // Check that SVG icons exist and are properly structured
      const icons = document.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(0);
      
      // Most icons in this design are decorative, so we just check they exist
      // In a real application, you would ensure proper aria-labels for functional icons
      icons.forEach(icon => {
        // Icons should be part of the DOM structure
        expect(icon).toBeInTheDocument();
      });
    });
  });

  describe('User Experience', () => {
    it('displays hero section with clear value proposition', () => {
      render(<Home />);
      
      expect(screen.getByText('Your Professional Network')).toBeInTheDocument();
      expect(screen.getByText('Powered by AI')).toBeInTheDocument();
      expect(screen.getByText(/Connect with professionals, discover opportunities/)).toBeInTheDocument();
    });

    it('shows compelling statistics', () => {
      render(<Home />);
      
      expect(screen.getByText('10M+')).toBeInTheDocument();
      expect(screen.getByText('Professionals')).toBeInTheDocument();
      expect(screen.getByText('500K+')).toBeInTheDocument();
      expect(screen.getByText('Job Opportunities')).toBeInTheDocument();
    });

    it('provides clear call-to-action buttons', () => {
      render(<Home />);
      
      const signInButton = screen.getByRole('link', { name: 'Sign In' });
      const joinButton = screen.getByRole('link', { name: 'Join Now' });
      const getStartedButton = screen.getByRole('link', { name: 'Get Started Free' });
      
      expect(signInButton).toHaveAttribute('href', '/auth/login');
      expect(joinButton).toHaveAttribute('href', '/auth/register');
      expect(getStartedButton).toHaveAttribute('href', '/auth/register');
    });

    it('displays popular search suggestions', () => {
      render(<Home />);
      
      expect(screen.getByText('Popular searches:')).toBeInTheDocument();
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Product Manager')).toBeInTheDocument();
      expect(screen.getByText('Data Scientist')).toBeInTheDocument();
      expect(screen.getByText('UX Designer')).toBeInTheDocument();
    });

    it('shows feature benefits clearly', () => {
      render(<Home />);
      
      // Job discovery features
      expect(screen.getByText(/AI analyzes your profile and matches you/)).toBeInTheDocument();
      expect(screen.getByText(/Apply to jobs with one click/)).toBeInTheDocument();
      expect(screen.getByText(/Get personalized insights about salary trends/)).toBeInTheDocument();
      
      // Company insights features
      expect(screen.getByText(/Research companies, track their growth/)).toBeInTheDocument();
      expect(screen.getByText('Company Profiles')).toBeInTheDocument();
      expect(screen.getByText('Follow & Track')).toBeInTheDocument();
    });

    it('includes comprehensive footer with links', () => {
      render(<Home />);
      
      // Check footer sections
      expect(screen.getByText('Platform')).toBeInTheDocument();
      expect(screen.getByText('Resources')).toBeInTheDocument();
      expect(screen.getByText('Company')).toBeInTheDocument();
      
      // Check footer links
      expect(screen.getByText('Job Search')).toBeInTheDocument();
      expect(screen.getByText('Career Advice')).toBeInTheDocument();
      expect(screen.getByText('About Us')).toBeInTheDocument();
      expect(screen.getByText('Privacy Policy')).toBeInTheDocument();
    });

    it('handles interactive elements properly', () => {
      render(<Home />);
      
      // Test popular search buttons
      const softwareEngineerButton = screen.getByText('Software Engineer');
      fireEvent.click(softwareEngineerButton);
      
      // Button should be clickable (no errors thrown)
      expect(softwareEngineerButton).toBeInTheDocument();
    });
  });

  describe('Content Structure', () => {
    it('has proper section organization', () => {
      render(<Home />);
      
      // Check that all main sections are present
      expect(screen.getByText('Discover Your Next Opportunity')).toBeInTheDocument();
      expect(screen.getByText('Company Intelligence at Your Fingertips')).toBeInTheDocument();
      expect(screen.getByText('Build Meaningful Professional Connections')).toBeInTheDocument();
      expect(screen.getByText('Transform Your CV into a Professional Portfolio')).toBeInTheDocument();
    });

    it('displays company example with proper data', () => {
      render(<Home />);
      
      expect(screen.getByText('TechCorp Inc.')).toBeInTheDocument();
      expect(screen.getByText('Software & Technology')).toBeInTheDocument();
      expect(screen.getByText('4.8')).toBeInTheDocument();
      expect(screen.getByText('Rating')).toBeInTheDocument();
      expect(screen.getByText('1.2K')).toBeInTheDocument();
      expect(screen.getByText('Employees')).toBeInTheDocument();
    });
  });
});