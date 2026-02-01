/**
 * ErrorBoundary Component Tests
 * Author: Sowad Al-Mughni
 * 
 * Tests for ErrorBoundary, SuspenseFallback, and APIErrorFallback components
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ErrorBoundary, { SuspenseFallback, APIErrorFallback } from './ErrorBoundary'

// Component that throws an error for testing
function ProblematicComponent({ shouldThrow = false }) {
  if (shouldThrow) {
    throw new Error('Test error message')
  }
  return <div>Working component</div>
}

describe('ErrorBoundary', () => {
  // Suppress console.error for expected errors during testing
  let originalError

  beforeEach(() => {
    originalError = console.error
    console.error = vi.fn()
  })

  afterEach(() => {
    console.error = originalError
  })

  describe('Normal Operation', () => {
    it('renders children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div>Child content</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('Child content')).toBeInTheDocument()
    })

    it('renders multiple children', () => {
      render(
        <ErrorBoundary>
          <div>First child</div>
          <div>Second child</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('First child')).toBeInTheDocument()
      expect(screen.getByText('Second child')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('catches errors and displays fallback UI', () => {
      render(
        <ErrorBoundary>
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('displays error description message', () => {
      render(
        <ErrorBoundary>
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText(/unexpected error occurred/i)).toBeInTheDocument()
    })

    it('shows Go Home button', () => {
      render(
        <ErrorBoundary>
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /go home/i })).toBeInTheDocument()
    })

    it('shows Try Again button', () => {
      render(
        <ErrorBoundary>
          <ProblematicComponent shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    })
  })
})

describe('SuspenseFallback', () => {
  it('renders with default message', () => {
    render(<SuspenseFallback />)

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders with custom message', () => {
    render(<SuspenseFallback message="Custom loading message" />)

    expect(screen.getByText('Custom loading message')).toBeInTheDocument()
  })

  it('displays spinner animation', () => {
    render(<SuspenseFallback />)

    // Look for the spinner element with animate-spin class
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })
})

describe('APIErrorFallback', () => {
  it('displays error title', () => {
    render(<APIErrorFallback error={{ message: 'API error' }} />)

    expect(screen.getByText('Error Loading Data')).toBeInTheDocument()
  })

  it('displays error message', () => {
    render(<APIErrorFallback error={{ message: 'Custom API error message' }} />)

    expect(screen.getByText('Custom API error message')).toBeInTheDocument()
  })

  it('displays default message when no error provided', () => {
    render(<APIErrorFallback />)

    expect(screen.getByText('Failed to load data from the server.')).toBeInTheDocument()
  })

  it('shows Retry button when onRetry provided', () => {
    const handleRetry = vi.fn()
    render(<APIErrorFallback error={{ message: 'Error' }} onRetry={handleRetry} />)

    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('calls onRetry when Retry button clicked', () => {
    const handleRetry = vi.fn()
    render(<APIErrorFallback error={{ message: 'Error' }} onRetry={handleRetry} />)

    fireEvent.click(screen.getByRole('button', { name: /retry/i }))

    expect(handleRetry).toHaveBeenCalledTimes(1)
  })

  it('does not show Retry button when onRetry not provided', () => {
    render(<APIErrorFallback error={{ message: 'Error' }} />)

    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument()
  })
})
