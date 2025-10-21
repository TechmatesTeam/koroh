import { render, screen } from '@testing-library/react';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

describe('LoadingSpinner', () => {
  it('renders spinner with default size', () => {
    render(<LoadingSpinner />);
    
    const spinner = screen.getByRole('status');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('h-8', 'w-8');
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<LoadingSpinner size="sm" />);
    expect(screen.getByRole('status')).toHaveClass('h-4', 'w-4');

    rerender(<LoadingSpinner size="lg" />);
    expect(screen.getByRole('status')).toHaveClass('h-12', 'w-12');

    rerender(<LoadingSpinner size="default" />);
    expect(screen.getByRole('status')).toHaveClass('h-8', 'w-8');
  });

  it('applies custom className', () => {
    render(<LoadingSpinner className="custom-spinner" />);
    
    expect(screen.getByRole('status')).toHaveClass('custom-spinner');
  });

  it('has proper animation and styling classes', () => {
    render(<LoadingSpinner />);
    
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass(
      'animate-spin',
      'rounded-full',
      'border-2',
      'border-gray-300',
      'border-t-indigo-600'
    );
  });

  it('has implicit accessibility role', () => {
    render(<LoadingSpinner />);
    
    // The spinner should have an implicit role of "status" for screen readers
    const spinner = screen.getByRole('status');
    expect(spinner).toBeInTheDocument();
  });

  it('combines size and custom className correctly', () => {
    render(<LoadingSpinner size="lg" className="my-custom-class" />);
    
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('h-12', 'w-12', 'my-custom-class');
  });
});