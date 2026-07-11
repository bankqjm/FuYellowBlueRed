import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext'

function ThemeTestComponent() {
  const { theme, toggleTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme-value">{theme}</span>
      <button data-testid="toggle-btn" onClick={toggleTheme}>Toggle</button>
    </div>
  )
}

describe('ThemeContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.body.classList.remove('dark-theme')
    document.documentElement.removeAttribute('data-theme')
  })

  it('should default to light theme', () => {
    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>,
    )
    expect(screen.getByTestId('theme-value').textContent).toBe('light')
  })

  it('should toggle to dark theme', () => {
    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>,
    )
    fireEvent.click(screen.getByTestId('toggle-btn'))
    expect(screen.getByTestId('theme-value').textContent).toBe('dark')
  })

  it('should toggle back to light theme', () => {
    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>,
    )
    fireEvent.click(screen.getByTestId('toggle-btn'))
    fireEvent.click(screen.getByTestId('toggle-btn'))
    expect(screen.getByTestId('theme-value').textContent).toBe('light')
  })

  it('should call localStorage.setItem when theme changes', () => {
    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>,
    )
    fireEvent.click(screen.getByTestId('toggle-btn'))
    expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'dark')
  })

  it('should call localStorage.getItem on init', () => {
    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>,
    )
    expect(localStorage.getItem).toHaveBeenCalledWith('theme')
  })

  it('should set data-theme attribute on document', () => {
    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>,
    )
    fireEvent.click(screen.getByTestId('toggle-btn'))
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('should toggle dark-theme class on body', () => {
    render(
      <ThemeProvider>
        <ThemeTestComponent />
      </ThemeProvider>,
    )
    fireEvent.click(screen.getByTestId('toggle-btn'))
    expect(document.body.classList.contains('dark-theme')).toBe(true)
    fireEvent.click(screen.getByTestId('toggle-btn'))
    expect(document.body.classList.contains('dark-theme')).toBe(false)
  })

  it('should throw error when useTheme used outside provider', () => {
    expect(() => {
      render(<ThemeTestComponent />)
    }).toThrow('useTheme must be used within ThemeProvider')
  })
})
