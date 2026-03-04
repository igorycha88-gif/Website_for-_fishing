import { render, screen, fireEvent } from '@testing-library/react';
import ToastContainer from '@/components/ToastContainer';
import { useToastStore } from '@/stores/useToastStore';

describe('ToastContainer', () => {
  beforeEach(() => {
    useToastStore.getState().clearToasts();
  });

  it('should render empty container when no toasts', () => {
    render(<ToastContainer />);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('should render success toast', () => {
    const store = useToastStore.getState();
    store.addToast('success', 'Success message');

    render(<ToastContainer />);

    expect(screen.getByText('Success message')).toBeInTheDocument();
  });

  it('should render error toast', () => {
    const store = useToastStore.getState();
    store.addToast('error', 'Error message');

    render(<ToastContainer />);

    expect(screen.getByText('Error message')).toBeInTheDocument();
  });

  it('should render info toast', () => {
    const store = useToastStore.getState();
    store.addToast('info', 'Info message');

    render(<ToastContainer />);

    expect(screen.getByText('Info message')).toBeInTheDocument();
  });

  it('should render warning toast', () => {
    const store = useToastStore.getState();
    store.addToast('warning', 'Warning message');

    render(<ToastContainer />);

    expect(screen.getByText('Warning message')).toBeInTheDocument();
  });

  it('should render multiple toasts', () => {
    const store = useToastStore.getState();
    store.addToast('success', 'Success message');
    store.addToast('error', 'Error message');

    render(<ToastContainer />);

    expect(screen.getByText('Success message')).toBeInTheDocument();
    expect(screen.getByText('Error message')).toBeInTheDocument();
  });

  it('should remove toast when close button clicked', () => {
    const store = useToastStore.getState();
    store.addToast('success', 'Test message');

    render(<ToastContainer />);

    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);

    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it('should apply correct styling for success toast', () => {
    const store = useToastStore.getState();
    store.addToast('success', 'Success message');

    render(<ToastContainer />);

    const toastElement = screen.getByText('Success message').closest('div');
    expect(toastElement).toHaveClass('bg-green-50');
  });

  it('should apply correct styling for error toast', () => {
    const store = useToastStore.getState();
    store.addToast('error', 'Error message');

    render(<ToastContainer />);

    const toastElement = screen.getByText('Error message').closest('div');
    expect(toastElement).toHaveClass('bg-red-50');
  });

  it('should apply correct styling for info toast', () => {
    const store = useToastStore.getState();
    store.addToast('info', 'Info message');

    render(<ToastContainer />);

    const toastElement = screen.getByText('Info message').closest('div');
    expect(toastElement).toHaveClass('bg-blue-50');
  });

  it('should apply correct styling for warning toast', () => {
    const store = useToastStore.getState();
    store.addToast('warning', 'Warning message');

    render(<ToastContainer />);

    const toastElement = screen.getByText('Warning message').closest('div');
    expect(toastElement).toHaveClass('bg-amber-50');
  });
});
