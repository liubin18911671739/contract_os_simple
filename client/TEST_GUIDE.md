# Frontend Testing Guide

This guide covers the testing setup and practices for the Contract OS Simple React frontend.

## Table of Contents

- [Testing Stack](#testing-stack)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Structure](#test-structure)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)

## Testing Stack

- **Test Runner**: Vitest (Fast, native ESM support)
- **Testing Library**: React Testing Library (Component testing)
- **Test Environment**: jsdom (Browser-like environment)
- **Coverage**: v8 (Built-in Vitest coverage)
- **UI**: Vitest UI (Optional visual test runner)

## Setup

### Installation

Dependencies are already included in `package.json`:

```json
{
  "devDependencies": {
    "@testing-library/jest-dom": "^6.1.5",
    "@testing-library/react": "^14.1.2",
    "@testing-library/user-event": "^14.5.1",
    "@vitest/ui": "^1.1.0",
    "jsdom": "^23.0.1",
    "vitest": "^1.1.0"
  }
}
```

Install them:

```bash
cd client
npm install
```

### Configuration

The test setup is configured in:

1. **`vitest.config.ts`** - Main Vitest configuration
2. **`src/test/setup.ts`** - Test setup and mocks
3. **`src/test/test-utils.tsx`** - Custom render functions
4. **`src/test/mockData.ts`** - Mock data fixtures
5. **`src/test/api-mocks.ts`** - API mocking utilities

## Running Tests

### Watch Mode (Interactive)

```bash
npm test
```

### Single Run

```bash
npm run test:run
```

### UI Mode (Visual Interface)

```bash
npm run test:ui
```

Opens a browser-based test interface at http://localhost:51204/__vitest__/

### Coverage Report

```bash
npm run test:coverage
```

Generates coverage in `client/coverage/` directory.

### Run Specific Tests

```bash
# Run a specific test file
npm test -- Button.test

# Run tests matching a pattern
npm test -- --grep "Button"

# Run tests in a specific directory
npm test -- src/components/ui/__tests__/
```

## Writing Tests

### Basic Component Test

```tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Button from '../Button'

describe('Button Component', () => {
  it('renders children correctly', () => {
    render(<button>Click me</button>)
    expect(screen.getByRole('button')).toHaveTextContent('Click me')
  })

  it('handles click events', () => {
    let clicked = false
    const handleClick = () => { clicked = true }

    render(<button onClick={handleClick}>Click me</button>)
    screen.getByRole('button').click()
    expect(clicked).toBe(true)
  })
})
```

### Test with Props

```tsx
describe('Badge Component', () => {
  it('applies color classes correctly', () => {
    render(
      <span className="bg-green-100 text-green-800">Success</span>
    )
    expect(screen.getByText('Success')).toHaveClass('bg-green-100')
  })
})
```

### Test User Interactions

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

describe('Form Component', () => {
  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    const handleSubmit = vi.fn()

    render(
      <form onSubmit={handleSubmit}>
        <input data-testid="name" name="name" />
        <button type="submit">Submit</button>
      </form>
    )

    await user.type(screen.getByTestId('name'), 'Test User')
    await user.click(screen.getByRole('button', { name: /submit/i }))

    expect(handleSubmit).toHaveBeenCalledTimes(1)
  })
})
```

### Test Async Operations

```tsx
import { render, screen, waitFor } from '@testing-library/react'

describe('Async Component', () => {
  it('displays loading state then data', async () => {
    render(<DataList />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText(/data loaded/i)).toBeInTheDocument()
    })
  })
})
```

## Test Structure

```
client/src/
├── components/
│   ├── ui/
│   │   ├── __tests__/
│   │   │   ├── Button.test.tsx
│   │   │   ├── Badge.test.tsx
│   │   │   └── Modal.test.tsx
│   └── ...
├── pages/
│   ├── __tests__/
│   │   ├── Dashboard.test.tsx
│   │   ├── Processing.test.tsx
│   │   └── Results.test.tsx
├── utils/
│   ├── __tests__/
│   │   └── localStorage.test.ts
├── __tests__/
│   └── integration/
│       └── api.test.tsx
└── test/
    ├── setup.ts           # Test setup
    ├── test-utils.tsx     # Custom render functions
    ├── mockData.ts        # Mock data fixtures
    └── api-mocks.ts       # API mocking utilities
```

## Best Practices

### 1. Test User Behavior, Not Implementation

❌ Bad:
```tsx
it('sets state to true', () => {
  // Testing internal state
})
```

✅ Good:
```tsx
it('shows success message after form submission', () => {
  // Testing user-visible behavior
})
```

### 2. Use Descriptive Test Names

```tsx
it('renders correctly')  // ❌ Too vague

it('renders task list with all columns')  // ✅ Specific
it('displays error message when task creation fails')  // ✅ Specific
```

### 3. Use Testing Library Queries

```tsx
// Priority order (most to least preferred):

// 1. By role (most accessible)
screen.getByRole('button', { name: /submit/i })

// 2. By label
screen.getByLabelText('Email')

// 3. By placeholder
screen.getByPlaceholderText('Search')

// 4. By text
screen.getByText('Submit')

// 5. By test id (last resort)
screen.getByTestId('submit-button')
```

### 4. Mock External Dependencies

```tsx
// Mock API calls
vi.mock('../api/tasks', () => ({
  getTasks: vi.fn(() => Promise.resolve({ data: mockTasks }))
}))

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})
```

### 5. Clean Up After Tests

```tsx
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
})
```

### 6. Test Error States

```tsx
it('displays error message when API fails', async () => {
  // Mock failed API call
  vi.mock('../api/tasks', () => ({
    getTasks: vi.fn(() => Promise.reject(new Error('API Error')))
  }))

  render(<TaskList />)

  await waitFor(() => {
    expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
  })
})
```

### 7. Test Loading States

```tsx
it('shows skeleton while loading', () => {
  vi.mock('../api/tasks', () => ({
    getTasks: vi.fn(() => new Promise(() => {})) // Never resolves
  }))

  render(<TaskList />)

  expect(screen.getByTestId('skeleton')).toBeInTheDocument()
})
```

## Common Patterns

### Rendering with Providers

```tsx
import { renderWithProviders } from '@/test/test-utils'

describe('My Component', () => {
  it('renders with router', () => {
    renderWithProviders(<MyComponent />)
  })

  it('renders with custom route', () => {
    renderWithProviders(<MyComponent />, { route: '/tasks/1' })
  })
})
```

### Testing Hooks

```tsx
import { renderHook, act } from '@testing-library/react'
import { useTaskData } from '../useTaskData'

describe('useTaskData Hook', () => {
  it('fetches task data on mount', async () => {
    vi.mock('../api/tasks', () => ({
      getTask: vi.fn(() => Promise.resolve({ data: mockTask }))
    }))

    const { result } = renderHook(() => useTaskData('1'))

    await waitFor(() => {
      expect(result.current.data).toEqual(mockTask)
    })
  })
})
```

### Testing Forms

```tsx
import userEvent from '@testing-library/user-event'

describe('Task Creation Form', () => {
  it('submits with all fields filled', async () => {
    const user = userEvent.setup()
    const handleSubmit = vi.fn()

    render(
      <form onSubmit={handleSubmit}>
        <input name="name" data-testid="name" required />
        <select name="type" data-testid="type">
          <option value="">Select...</option>
          <option value="contract">Contract</option>
        </select>
        <button type="submit">Submit</button>
      </form>
    )

    await user.type(screen.getByTestId('name'), 'Test Task')
    await user.selectOptions(screen.getByTestId('type'), 'contract')
    await user.click(screen.getByRole('button'))

    expect(handleSubmit).toHaveBeenCalled()
  })
})
```

### Testing Navigation

```tsx
import { renderWithProviders } from '@/test/test-utils'

describe('Navigation', () => {
  it('navigates to task details on click', async () => {
    const user = userEvent.setup()

    renderWithProviders(
      <a href="/tasks/1" data-testid="task-link">
        View Task
      </a>
    )

    await user.click(screen.getByTestId('task-link'))

    // Assert navigation happened
    expect(window.location.pathname).toBe('/tasks/1')
  })
})
```

## Coverage Goals

Aim for:

- **Statements**: > 80%
- **Branches**: > 75%
- **Functions**: > 80%
- **Lines**: > 80%

Focus coverage on:

1. ✅ Critical business logic
2. ✅ Error handling
3. ✅ Edge cases
4. ⚠️ UI styling (lower priority)
5. ⚠️ Mock data (not necessary)

## Troubleshooting

### Tests Timing Out

```tsx
// Increase timeout
it('loads data slowly', { timeout: 10000 }, async () => {
  // Test code
})
```

### Tests Failing in CI but Not Locally

```tsx
// Ensure cleanup
afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

// Use waitFor for async
await waitFor(() => {
  expect(element).toBeInTheDocument()
})
```

### React Act Warnings

```tsx
// Wrap state updates in act()
import { act } from 'react'

act(() => {
  // State update
})

// Or use waitFor
await waitFor(() => {
  expect(result).toBe(expected)
})
```

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Playground](https://testing-playground.com/)
- [Common Mistakes with React Testing Library](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
