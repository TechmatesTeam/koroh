import { render, screen, fireEvent } from '@testing-library/react';
import { Modal } from '@/components/ui/modal';

describe('Modal', () => {
  it('renders modal when isOpen is true', () => {
    render(
      <Modal isOpen={true} onClose={jest.fn()} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render modal when isOpen is false', () => {
    render(
      <Modal isOpen={false} onClose={jest.fn()} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();
    expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const handleClose = jest.fn();
    render(
      <Modal isOpen={true} onClose={handleClose} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );

    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('renders without title when title is not provided', () => {
    render(
      <Modal isOpen={true} onClose={jest.fn()}>
        <p>Modal content</p>
      </Modal>
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Modal content')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument(); // No close button without title
  });

  it('applies correct size classes', () => {
    const { rerender } = render(
      <Modal isOpen={true} onClose={jest.fn()} size="sm">
        <p>Small modal</p>
      </Modal>
    );

    expect(screen.getByText('Small modal').closest('[role="dialog"]')).toHaveClass('max-w-md');

    rerender(
      <Modal isOpen={true} onClose={jest.fn()} size="lg">
        <p>Large modal</p>
      </Modal>
    );

    expect(screen.getByText('Large modal').closest('[role="dialog"]')).toHaveClass('max-w-2xl');

    rerender(
      <Modal isOpen={true} onClose={jest.fn()} size="xl">
        <p>Extra large modal</p>
      </Modal>
    );

    expect(screen.getByText('Extra large modal').closest('[role="dialog"]')).toHaveClass('max-w-4xl');
  });

  it('uses medium size by default', () => {
    render(
      <Modal isOpen={true} onClose={jest.fn()}>
        <p>Default modal</p>
      </Modal>
    );

    expect(screen.getByText('Default modal').closest('[role="dialog"]')).toHaveClass('max-w-lg');
  });

  it('has proper accessibility attributes', () => {
    render(
      <Modal isOpen={true} onClose={jest.fn()} title="Accessible Modal">
        <p>Modal content</p>
      </Modal>
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    
    const title = screen.getByText('Accessible Modal');
    expect(title).toBeInTheDocument();
  });

  it('renders children content correctly', () => {
    render(
      <Modal isOpen={true} onClose={jest.fn()}>
        <div>
          <h2>Custom Content</h2>
          <p>This is custom modal content</p>
          <button>Action Button</button>
        </div>
      </Modal>
    );

    expect(screen.getByText('Custom Content')).toBeInTheDocument();
    expect(screen.getByText('This is custom modal content')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Action Button' })).toBeInTheDocument();
  });

  it('has proper styling classes for visual appearance', () => {
    render(
      <Modal isOpen={true} onClose={jest.fn()} title="Styled Modal">
        <p>Content</p>
      </Modal>
    );

    const dialogPanel = screen.getByText('Content').closest('[role="dialog"]');
    expect(dialogPanel).toHaveClass('bg-white', 'rounded-2xl', 'shadow-xl');
  });
});