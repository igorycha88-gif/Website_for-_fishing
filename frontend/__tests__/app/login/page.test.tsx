import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from '@/app/login/page';
import { useAuthStore } from '@/app/stores/useAuthStore';
import { useRateLimit } from '@/hooks/useRateLimit';

jest.mock('@/app/stores/useAuthStore', () => ({
  useAuthStore: jest.fn(),
}));

jest.mock('@/hooks/useRateLimit', () => ({
  useRateLimit: jest.fn(),
  formatRemainingTime: (seconds: number) => {
    if (seconds <= 0) return '';
    if (seconds < 60) return `${seconds} секунд`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (secs === 0) return `${minutes} минут`;
    return `${minutes} минут ${secs} секунд`;
  },
}));

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode }) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const mockFetch = global.fetch as jest.Mock;

describe('LoginPage', () => {
  const mockLogin = jest.fn();
  const mockStartLimit = jest.fn();
  const mockClearLimit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    (useAuthStore as jest.Mock).mockReturnValue({
      login: mockLogin,
    });
    
    (useRateLimit as jest.Mock).mockReturnValue({
      isLimited: false,
      remainingSeconds: 0,
      startLimit: mockStartLimit,
      clearLimit: mockClearLimit,
    });
    
    mockFetch.mockReset();
    
    delete (window as unknown as { location?: { href: string } }).location;
    window.location = { href: '' } as Location;
  });

  describe('Button blocking during rate limit', () => {
    it('should have submit button enabled when not rate limited', () => {
      render(<LoginPage />);
      
      const submitButton = screen.getByRole('button', { name: /войти/i });
      expect(submitButton).not.toBeDisabled();
    });

    it('should have submit button disabled when rate limited', () => {
      (useRateLimit as jest.Mock).mockReturnValue({
        isLimited: true,
        remainingSeconds: 45,
        startLimit: mockStartLimit,
        clearLimit: mockClearLimit,
      });
      
      render(<LoginPage />);
      
      const submitButton = screen.getByRole('button', { name: /подождите/i });
      expect(submitButton).toBeDisabled();
    });

    it('should show remaining seconds in button text when rate limited', () => {
      (useRateLimit as jest.Mock).mockReturnValue({
        isLimited: true,
        remainingSeconds: 30,
        startLimit: mockStartLimit,
        clearLimit: mockClearLimit,
      });
      
      render(<LoginPage />);
      
      const submitButton = screen.getByRole('button', { name: /подождите/i });
      expect(submitButton).toHaveTextContent(/30 сек/);
    });

    it('should re-enable button when rate limit expires', () => {
      const { rerender } = render(<LoginPage />);
      
      let submitButton = screen.getByRole('button', { name: /войти/i });
      expect(submitButton).not.toBeDisabled();
      
      (useRateLimit as jest.Mock).mockReturnValue({
        isLimited: true,
        remainingSeconds: 10,
        startLimit: mockStartLimit,
        clearLimit: mockClearLimit,
      });
      
      rerender(<LoginPage />);
      submitButton = screen.getByRole('button', { name: /подождите/i });
      expect(submitButton).toBeDisabled();
      
      (useRateLimit as jest.Mock).mockReturnValue({
        isLimited: false,
        remainingSeconds: 0,
        startLimit: mockStartLimit,
        clearLimit: mockClearLimit,
      });
      
      rerender(<LoginPage />);
      submitButton = screen.getByRole('button', { name: /войти/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Rate limit handling on 429 response', () => {
    it('should call startLimit when receiving 429 response', async () => {
      mockFetch.mockResolvedValueOnce({
        status: 429,
        headers: {
          get: (name: string) => name === 'Retry-After' ? '45' : null,
        },
        json: async () => ({
          error: {
            details: { endpoint: '/api/v1/auth/login' }
          }
        }),
      });
      
      render(<LoginPage />);
      
      const emailInput = screen.getByPlaceholderText(/your@email.com/i);
      const passwordInput = screen.getByPlaceholderText(/••••••••/);
      const submitButton = screen.getByRole('button', { name: /войти/i });
      
      fireEvent.change(emailInput, { target: { value: 'test@test.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockStartLimit).toHaveBeenCalledWith(45);
      });
    });

    it('should use default retry-after value of 60 when header is missing', async () => {
      mockFetch.mockResolvedValueOnce({
        status: 429,
        headers: {
          get: () => null,
        },
        json: async () => ({
          error: {
            details: { endpoint: '/api/v1/auth/login' }
          }
        }),
      });
      
      render(<LoginPage />);
      
      const emailInput = screen.getByPlaceholderText(/your@email.com/i);
      const passwordInput = screen.getByPlaceholderText(/••••••••/);
      const submitButton = screen.getByRole('button', { name: /войти/i });
      
      fireEvent.change(emailInput, { target: { value: 'test@test.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockStartLimit).toHaveBeenCalledWith(60);
      });
    });
  });

  describe('Input field disabling during rate limit', () => {
    it('should disable email input when rate limited', () => {
      (useRateLimit as jest.Mock).mockReturnValue({
        isLimited: true,
        remainingSeconds: 30,
        startLimit: mockStartLimit,
        clearLimit: mockClearLimit,
      });
      
      render(<LoginPage />);
      
      const emailInput = screen.getByPlaceholderText(/your@email.com/i);
      expect(emailInput).toBeDisabled();
    });

    it('should disable password input when rate limited', () => {
      (useRateLimit as jest.Mock).mockReturnValue({
        isLimited: true,
        remainingSeconds: 30,
        startLimit: mockStartLimit,
        clearLimit: mockClearLimit,
      });
      
      render(<LoginPage />);
      
      const passwordInput = screen.getByPlaceholderText(/••••••••/);
      expect(passwordInput).toBeDisabled();
    });

    it('should enable inputs when not rate limited', () => {
      render(<LoginPage />);
      
      const emailInput = screen.getByPlaceholderText(/your@email.com/i);
      const passwordInput = screen.getByPlaceholderText(/••••••••/);
      
      expect(emailInput).not.toBeDisabled();
      expect(passwordInput).not.toBeDisabled();
    });
  });

  describe('Rate limit toast visibility', () => {
    it('should show rate limit toast when rate limited', () => {
      (useRateLimit as jest.Mock).mockReturnValue({
        isLimited: true,
        remainingSeconds: 45,
        startLimit: mockStartLimit,
        clearLimit: mockClearLimit,
      });
      
      render(<LoginPage />);
      
      expect(screen.getByText(/слишком много попыток входа/i)).toBeInTheDocument();
    });

    it('should hide rate limit toast when not rate limited', () => {
      render(<LoginPage />);
      
      expect(screen.queryByText(/слишком много попыток входа/i)).not.toBeInTheDocument();
    });
  });

  describe('Form submission during rate limit', () => {
    it('should not submit form when rate limited', async () => {
      (useRateLimit as jest.Mock).mockReturnValue({
        isLimited: true,
        remainingSeconds: 30,
        startLimit: mockStartLimit,
        clearLimit: mockClearLimit,
      });
      
      render(<LoginPage />);
      
      const submitButton = screen.getByRole('button', { name: /подождите/i });
      fireEvent.click(submitButton);
      
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });
});
