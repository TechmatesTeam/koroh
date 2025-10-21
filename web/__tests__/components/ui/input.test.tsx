import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '@/components/ui/input';

describe('Input', () => {
  it('renders input with default attributes', () => {
    render(<Input placeholder="Enter text" />);
    
    const input = screen.getByPlaceholderText(/enter text/i);
    expect(input).toBeInTheDocument();
    expect(input).toHaveClass('h-10', 'w-full', 'rounded-md', 'border');
  });

  it('applies correct type attribute', () => {
    const { rerender } = render(<Input type="email" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('type', 'email');

    rerender(<Input type="password" />);
    expect(screen.getByDisplayValue('')).toHaveAttribute('type', 'password');
  });

  it('handles value changes', () => {
    const handleChange = jest.fn();
    render(<Input onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test value' } });
    
    expect(handleChange).toHaveBeenCalled();
    expect(input).toHaveValue('test value');
  });

  it('is disabled when disabled prop is true', () => {
    render(<Input disabled />);
    
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
    expect(input).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50');
  });

  it('applies custom className', () => {
    render(<Input className="custom-input" />);
    
    expect(screen.getByRole('textbox')).toHaveClass('custom-input');
  });

  it('forwards ref correctly', () => {
    const ref = { current: null };
    render(<Input ref={ref} />);
    
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it('passes through HTML input attributes', () => {
    render(
      <Input
        id="test-input"
        name="testName"
        autoComplete="email"
        required
        aria-label="Test input"
      />
    );
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('id', 'test-input');
    expect(input).toHaveAttribute('name', 'testName');
    expect(input).toHaveAttribute('autoComplete', 'email');
    expect(input).toHaveAttribute('aria-label', 'Test input');
    expect(input).toBeRequired();
  });

  it('has proper focus styles for accessibility', () => {
    render(<Input />);
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('focus-visible:outline-none', 'focus-visible:ring-2');
  });

  it('handles placeholder text correctly', () => {
    render(<Input placeholder="Search..." />);
    
    const input = screen.getByPlaceholderText('Search...');
    expect(input).toBeInTheDocument();
    expect(input).toHaveClass('placeholder:text-gray-500');
  });

  it('supports file input type with proper styling', () => {
    render(<Input type="file" />);
    
    const input = screen.getByDisplayValue(''); // File inputs don't have textbox role
    expect(input).toHaveAttribute('type', 'file');
    expect(input).toHaveClass('file:border-0', 'file:bg-transparent');
  });
});