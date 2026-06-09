import { act } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import { useToastStore, useToast } from '@/stores/useToastStore';

describe('useToastStore', () => {
  beforeEach(() => {
    act(() => {
      useToastStore.getState().clearToasts();
    });
  });

  describe('addToast', () => {
    it('should add a toast to the store', () => {
      act(() => {
        useToastStore.getState().addToast('success', 'Test message');
      });

      const toasts = useToastStore.getState().toasts;
      expect(toasts).toHaveLength(1);
      expect(toasts[0].type).toBe('success');
      expect(toasts[0].message).toBe('Test message');
    });

    it('should add multiple toasts', () => {
      act(() => {
        useToastStore.getState().addToast('success', 'Message 1');
        useToastStore.getState().addToast('error', 'Message 2');
        useToastStore.getState().addToast('info', 'Message 3');
      });

      expect(useToastStore.getState().toasts).toHaveLength(3);
    });

    it('should generate unique ids for toasts', () => {
      act(() => {
        useToastStore.getState().addToast('success', 'Message 1');
        useToastStore.getState().addToast('success', 'Message 2');
      });

      const toasts = useToastStore.getState().toasts;
      expect(toasts[0].id).not.toBe(toasts[1].id);
    });

    it('should use custom duration', () => {
      act(() => {
        useToastStore.getState().addToast('success', 'Test message', 10000);
      });

      const toasts = useToastStore.getState().toasts;
      expect(toasts).toHaveLength(1);
      expect(toasts[0].duration).toBe(10000);
    });

    it('should auto-remove toast after duration', () => {
      jest.useFakeTimers();

      act(() => {
        useToastStore.getState().addToast('success', 'Test message', 1000);
      });

      expect(useToastStore.getState().toasts).toHaveLength(1);

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(useToastStore.getState().toasts).toHaveLength(0);

      jest.useRealTimers();
    });

    it('should not auto-remove toast when duration is 0', () => {
      jest.useFakeTimers();

      act(() => {
        useToastStore.getState().addToast('success', 'Test message', 0);
      });

      expect(useToastStore.getState().toasts).toHaveLength(1);

      act(() => {
        jest.advanceTimersByTime(10000);
      });

      expect(useToastStore.getState().toasts).toHaveLength(1);

      jest.useRealTimers();
    });
  });

  describe('removeToast', () => {
    it('should remove toast by id', () => {
      act(() => {
        useToastStore.getState().addToast('success', 'Message 1');
        useToastStore.getState().addToast('error', 'Message 2');
      });

      const toastId = useToastStore.getState().toasts[0].id;

      act(() => {
        useToastStore.getState().removeToast(toastId);
      });

      const toasts = useToastStore.getState().toasts;
      expect(toasts).toHaveLength(1);
      expect(toasts[0].type).toBe('error');
    });

    it('should do nothing if toast not found', () => {
      act(() => {
        useToastStore.getState().addToast('success', 'Message 1');
      });

      act(() => {
        useToastStore.getState().removeToast('non-existent-id');
      });

      expect(useToastStore.getState().toasts).toHaveLength(1);
    });
  });

  describe('clearToasts', () => {
    it('should remove all toasts', () => {
      act(() => {
        useToastStore.getState().addToast('success', 'Message 1');
        useToastStore.getState().addToast('error', 'Message 2');
        useToastStore.getState().addToast('info', 'Message 3');
      });

      expect(useToastStore.getState().toasts).toHaveLength(3);

      act(() => {
        useToastStore.getState().clearToasts();
      });

      expect(useToastStore.getState().toasts).toHaveLength(0);
    });
  });
});

describe('useToast', () => {
  beforeEach(() => {
    act(() => {
      useToastStore.getState().clearToasts();
    });
  });

  it('should add success toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.success('Success message');
    });

    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].type).toBe('success');
    expect(toasts[0].message).toBe('Success message');
  });

  it('should add error toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.error('Error message');
    });

    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].type).toBe('error');
  });

  it('should add info toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.info('Info message');
    });

    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].type).toBe('info');
  });

  it('should add warning toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.warning('Warning message');
    });

    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].type).toBe('warning');
  });

  it('should remove toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.success('Success message');
    });

    const toastId = useToastStore.getState().toasts[0].id;

    act(() => {
      result.current.remove(toastId);
    });

    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it('should clear all toasts', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.success('Message 1');
      result.current.error('Message 2');
    });

    act(() => {
      result.current.clear();
    });

    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it('should pass custom duration', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.success('Success message', 3000);
    });

    const toasts = useToastStore.getState().toasts;
    expect(toasts[0].duration).toBe(3000);
  });
});
