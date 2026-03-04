import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CalendarPopover from '@/components/CalendarPopover';
import { subDays, addDays, format } from 'date-fns';

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, initial, animate, exit, transition, onClick, ...props }: any) => (
      <div {...props} onClick={onClick}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('CalendarPopover', () => {
  const mockOnDateSelect = jest.fn();
  const minDate = subDays(new Date(), 30);
  const maxDate = addDays(new Date(), 3);
  const today = format(new Date(), 'yyyy-MM-dd');
  const tomorrow = format(addDays(new Date(), 1), 'yyyy-MM-dd');

  const defaultProps = {
    selectedDate: null,
    onDateSelect: mockOnDateSelect,
    minDate,
    maxDate,
    availableDates: [today, tomorrow],
    daySummaries: {
      [today]: {
        date: today,
        temperature: -3,
        weather_icon: '01d',
        wind_speed: 3.5,
      },
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render button with default text when no date selected', () => {
    render(<CalendarPopover {...defaultProps} />);

    expect(screen.getByText('Выберите дату')).toBeInTheDocument();
  });

  it('should render button with selected date', () => {
    render(<CalendarPopover {...defaultProps} selectedDate={today} />);

    expect(screen.getByRole('button', { name: /выбрать дату/i })).toBeInTheDocument();
  });

  it('should open modal on button click', () => {
    render(<CalendarPopover {...defaultProps} />);

    const button = screen.getByRole('button', { name: /выбрать дату/i });
    fireEvent.click(button);

    expect(screen.getByRole('button', { name: /закрыть/i })).toBeInTheDocument();
    expect(screen.getByText('Дни с прогнозом клева')).toBeInTheDocument();
  });

  it('should close modal on Escape key', async () => {
    render(<CalendarPopover {...defaultProps} />);

    const button = screen.getByRole('button', { name: /выбрать дату/i });
    fireEvent.click(button);

    fireEvent.keyDown(document, { key: 'Escape' });

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /закрыть/i })).not.toBeInTheDocument();
    });
  });

  it('should close modal on close button click', () => {
    render(<CalendarPopover {...defaultProps} />);

    const button = screen.getByRole('button', { name: /выбрать дату/i });
    fireEvent.click(button);

    const closeButton = screen.getByRole('button', { name: /закрыть/i });
    fireEvent.click(closeButton);
  });

  it('should have correct aria attributes', () => {
    render(<CalendarPopover {...defaultProps} />);

    const button = screen.getByRole('button', { name: /выбрать дату/i });
    expect(button).toHaveAttribute('aria-label', 'Выбрать дату');
  });

  it('should handle empty available dates', () => {
    render(<CalendarPopover {...defaultProps} availableDates={[]} />);

    const button = screen.getByRole('button', { name: /выбрать дату/i });
    fireEvent.click(button);

    expect(screen.getByText('Дни с прогнозом клева')).toBeInTheDocument();
  });

  it('should handle null temperature in day summary', () => {
    const propsWithNullTemp = {
      ...defaultProps,
      daySummaries: {
        [today]: {
          date: today,
          temperature: null,
          weather_icon: '01d',
          wind_speed: null,
        },
      },
    };

    render(<CalendarPopover {...propsWithNullTemp} />);

    const button = screen.getByRole('button', { name: /выбрать дату/i });
    fireEvent.click(button);

    expect(screen.getByRole('button', { name: /закрыть/i })).toBeInTheDocument();
  });

  it('should show legend about forecast days', () => {
    render(<CalendarPopover {...defaultProps} />);

    const button = screen.getByRole('button', { name: /выбрать дату/i });
    fireEvent.click(button);

    expect(screen.getByText('Дни с прогнозом клева')).toBeInTheDocument();
  });
});
