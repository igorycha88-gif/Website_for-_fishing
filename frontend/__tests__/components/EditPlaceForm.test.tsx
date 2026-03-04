import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import EditPlaceForm from '@/components/EditPlaceForm';
import { usePlaces } from '@/hooks/usePlaces';
import { Place } from '@/types/place';

jest.mock('@/hooks/usePlaces');

const mockPlace: Place = {
  id: '1',
  owner_id: 'user1',
  name: 'Test Place',
  description: 'Test description',
  latitude: 55.7558,
  longitude: 37.6173,
  address: 'Test Address',
  place_type: 'wild',
  access_type: 'car',
  water_type: 'lake',
  fish_types: [
    { id: '1', name: 'Щука', icon: '🐟', category: 'predatory' },
  ],
  seasonality: ['summer'],
  visibility: 'private',
  images: [],
  rating_avg: 0,
  reviews_count: 0,
  is_active: true,
  created_at: '2024-01-01',
  updated_at: '2024-01-01',
};

const mockFishTypes = [
  { id: '1', name: 'Щука', icon: '🐟', category: 'predatory' },
  { id: '2', name: 'Карп', icon: '🐠', category: 'peaceful' },
];

describe('EditPlaceForm', () => {
  const mockOnCancel = jest.fn();
  const mockOnSave = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (usePlaces as jest.Mock).mockReturnValue({
      getFishTypes: jest.fn().mockResolvedValue(mockFishTypes),
    });
  });

  it('should render with pre-filled data', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Place')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test description')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test Address')).toBeInTheDocument();
    });
  });

  it('should call onCancel when cancel button clicked', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Отмена')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Отмена'));

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('should call onCancel when X button clicked', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Редактирование места')).toBeInTheDocument();
    });

    const closeButton = screen.getByRole('button', { name: '' });
    fireEvent.click(closeButton);

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('should call onSave with updated data', async () => {
    mockOnSave.mockResolvedValue(undefined);

    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Place')).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue('Test Place');
    fireEvent.change(nameInput, { target: { value: 'Updated Place' } });
    fireEvent.click(screen.getByText('Сохранить'));

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Updated Place',
        })
      );
    });
  });

  it('should show error when onSave fails', async () => {
    mockOnSave.mockRejectedValue(new Error('Save failed'));

    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Place')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Сохранить'));

    await waitFor(() => {
      expect(screen.getByText('Save failed')).toBeInTheDocument();
    });
  });

  it('should display fish types from API', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Щука/)).toBeInTheDocument();
      expect(screen.getByText(/Карп/)).toBeInTheDocument();
    });
  });

  it('should toggle fish type selection', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Карп/)).toBeInTheDocument();
    });

    const carpCheckbox = screen.getByText(/Карп/).closest('label')!.querySelector('input');
    fireEvent.click(carpCheckbox!);

    expect(carpCheckbox).toBeChecked();
  });

  it('should change visibility to public', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Place')).toBeInTheDocument();
    });

    const publicRadio = screen.getByLabelText('Публичное');
    fireEvent.click(publicRadio);

    expect(publicRadio).toBeChecked();
  });

  it('should display place type options', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      const selectElement = screen.getByDisplayValue('Дикое место');
      expect(selectElement).toBeInTheDocument();
    });
  });

  it('should display water type options', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      const selectElement = screen.getByDisplayValue('Озеро');
      expect(selectElement).toBeInTheDocument();
    });
  });

  it('should display access type options', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      const selectElement = screen.getByDisplayValue('На машине');
      expect(selectElement).toBeInTheDocument();
    });
  });

  it('should show loading state when saving', async () => {
    mockOnSave.mockImplementation(() => new Promise(() => {}));

    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Place')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Сохранить'));

    await waitFor(() => {
      expect(screen.getByText('Сохранение...')).toBeInTheDocument();
    });
  });

  it('should display seasonality checkboxes', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Весна')).toBeInTheDocument();
      expect(screen.getByLabelText('Лето')).toBeInTheDocument();
      expect(screen.getByLabelText('Осень')).toBeInTheDocument();
      expect(screen.getByLabelText('Зима')).toBeInTheDocument();
    });
  });

  it('should have pre-selected seasonality', async () => {
    render(
      <EditPlaceForm
        place={mockPlace}
        onCancel={mockOnCancel}
        onSave={mockOnSave}
      />
    );

    await waitFor(() => {
      const summerCheckbox = screen.getByLabelText('Лето');
      expect(summerCheckbox).toBeChecked();
    });
  });
});
