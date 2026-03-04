import { render, screen, fireEvent } from '@testing-library/react';
import ConfirmDialog from '@/components/ConfirmDialog';

describe('ConfirmDialog', () => {
  const mockOnConfirm = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should not render when isOpen is false', () => {
    render(
      <ConfirmDialog
        isOpen={false}
        title="Test Title"
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.queryByText('Test Title')).not.toBeInTheDocument();
  });

  it('should render when isOpen is true', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Test Title"
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('should call onCancel when cancel button clicked', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Test Title"
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    fireEvent.click(screen.getByText('Отмена'));

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
    expect(mockOnConfirm).not.toHaveBeenCalled();
  });

  it('should call onConfirm when confirm button clicked', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Test Title"
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    fireEvent.click(screen.getByText('Подтвердить'));

    expect(mockOnConfirm).toHaveBeenCalledTimes(1);
    expect(mockOnCancel).not.toHaveBeenCalled();
  });

  it('should display custom confirm text', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Test Title"
        message="Test message"
        confirmText="Delete"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  it('should display custom cancel text', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Test Title"
        message="Test message"
        cancelText="Close"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Close')).toBeInTheDocument();
  });

  it('should disable buttons when loading', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Test Title"
        message="Test message"
        loading={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByText('Отмена').closest('button');
    const confirmButton = screen.getByText('Удаление...').closest('button');

    expect(cancelButton).toBeDisabled();
    expect(confirmButton).toBeDisabled();
  });

  it('should show loading text when loading', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Test Title"
        message="Test message"
        loading={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Удаление...')).toBeInTheDocument();
  });

  it('should not call onConfirm when loading', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Test Title"
        message="Test message"
        loading={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const confirmButton = screen.getByText('Удаление...').closest('button');
    fireEvent.click(confirmButton!);

    expect(mockOnConfirm).not.toHaveBeenCalled();
  });

  it('should render danger variant by default', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Delete Item"
        message="Are you sure?"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const confirmButton = screen.getByText('Подтвердить').closest('button');
    expect(confirmButton).toHaveClass('bg-red-600');
  });

  it('should render primary variant when specified', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Confirm Action"
        message="Are you sure?"
        confirmVariant="primary"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const confirmButton = screen.getByText('Подтвердить').closest('button');
    expect(confirmButton).toHaveClass('bg-primary-sea');
  });

  it('should display alert icon', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Test Title"
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );

    const alertIcon = document.querySelector('.text-red-600');
    expect(alertIcon).toBeInTheDocument();
  });
});
