import { render, screen, fireEvent } from '@testing-library/react';
import { RateLimitToast } from '@/components/auth/RateLimitToast';

describe('RateLimitToast', () => {
  it('should not render when isVisible is false', () => {
    render(
      <RateLimitToast
        isVisible={false}
        remainingSeconds={60}
        endpoint="/api/v1/auth/login"
      />
    );

    expect(screen.queryByText(/слишком много/i)).not.toBeInTheDocument();
  });

  it('should render when isVisible is true', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
        endpoint="/api/v1/auth/login"
      />
    );

    expect(screen.getByText(/слишком много/i)).toBeInTheDocument();
  });

  it('should display remaining time in seconds', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={45}
        endpoint="/api/v1/auth/login"
      />
    );

    expect(screen.getByText(/45 секунд/)).toBeInTheDocument();
  });

  it('should display remaining time in minutes', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={120}
        endpoint="/api/v1/auth/login"
      />
    );

    expect(screen.getByText(/2 минуты/)).toBeInTheDocument();
  });

  it('should show login-specific message for login endpoint', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
        endpoint="/api/v1/auth/login"
      />
    );

    expect(screen.getByText(/слишком много попыток входа/i)).toBeInTheDocument();
  });

  it('should show register-specific message for register endpoint', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
        endpoint="/api/v1/auth/register"
      />
    );

    expect(screen.getByText(/слишком много регистраций/i)).toBeInTheDocument();
  });

  it('should show reset-password-specific message for reset-password endpoint', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
        endpoint="/api/v1/auth/reset-password/request"
      />
    );

    expect(screen.getByText(/слишком много запросов сброса пароля/i)).toBeInTheDocument();
  });

  it('should show verify-email-specific message for verify-email endpoint', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
        endpoint="/api/v1/auth/verify-email"
      />
    );

    expect(screen.getByText(/слишком много попыток верификации/i)).toBeInTheDocument();
  });

  it('should show generic message for unknown endpoint', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
        endpoint="/api/v1/unknown"
      />
    );

    expect(screen.getByText(/слишком много запросов/i)).toBeInTheDocument();
  });

  it('should show generic English message when endpoint is not provided', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
      />
    );

    expect(screen.getByText(/too many requests/i)).toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', () => {
    const onClose = jest.fn();

    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
        endpoint="/api/v1/auth/login"
        onClose={onClose}
      />
    );

    const closeButton = screen.getByRole('button', { name: /закрыть/i });
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should not render close button when onClose is not provided', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
        endpoint="/api/v1/auth/login"
      />
    );

    expect(screen.queryByRole('button', { name: /закрыть/i })).not.toBeInTheDocument();
  });

  it('should render progress bar', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
        endpoint="/api/v1/auth/login"
      />
    );

    const progressBar = document.querySelector('.bg-amber-200');
    
    expect(progressBar).toBeInTheDocument();
  });

  it('should have warning icon', () => {
    render(
      <RateLimitToast
        isVisible={true}
        remainingSeconds={60}
        endpoint="/api/v1/auth/login"
      />
    );

    const container = screen.getByText(/слишком много/i).closest('div');
    expect(container?.querySelector('svg')).toBeInTheDocument();
  });
});
