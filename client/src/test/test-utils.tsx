import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'
import { BrowserRouter } from 'react-router-dom'

// Custom render function that includes providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string
}

export function renderWithProviders(
  ui: ReactElement,
  { route = '/', ...options }: CustomRenderOptions = {}
) {
  window.history.pushState({}, 'Test page', route)

  function Wrapper({ children }: { children: React.ReactNode }) {
    return <BrowserRouter>{children}</BrowserRouter>
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...options }),
  }
}

// Re-export everything from RTL
export * from '@testing-library/react'
export { renderWithProviders as render }
