/**
 * Button Component Tests
 * Author: Sowad Al-Mughni
 * 
 * Tests for the Button component variants and interactions
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './button'

describe('Button Component', () => {
  describe('Rendering', () => {
    it('renders with default props', () => {
      render(<Button>Click me</Button>)
      
      const button = screen.getByRole('button', { name: /click me/i })
      expect(button).toBeInTheDocument()
    })

    it('renders children correctly', () => {
      render(<Button>Test Content</Button>)
      
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('renders with data-slot attribute', () => {
      render(<Button>Test</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('data-slot', 'button')
    })
  })

  describe('Variants', () => {
    it('renders default variant', () => {
      render(<Button variant="default">Default</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-primary')
    })

    it('renders destructive variant', () => {
      render(<Button variant="destructive">Delete</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-destructive')
    })

    it('renders outline variant', () => {
      render(<Button variant="outline">Outline</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('border')
    })

    it('renders secondary variant', () => {
      render(<Button variant="secondary">Secondary</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-secondary')
    })

    it('renders ghost variant', () => {
      render(<Button variant="ghost">Ghost</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('hover:bg-accent')
    })

    it('renders link variant', () => {
      render(<Button variant="link">Link</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('text-primary')
    })
  })

  describe('Sizes', () => {
    it('renders default size', () => {
      render(<Button size="default">Default Size</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-9')
    })

    it('renders small size', () => {
      render(<Button size="sm">Small</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-8')
    })

    it('renders large size', () => {
      render(<Button size="lg">Large</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-10')
    })

    it('renders icon size', () => {
      render(<Button size="icon">🔍</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('size-9')
    })
  })

  describe('States', () => {
    it('handles disabled state', () => {
      render(<Button disabled>Disabled</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('applies disabled styles', () => {
      render(<Button disabled>Disabled</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('disabled:opacity-50')
    })
  })

  describe('Interactions', () => {
    it('handles click events', () => {
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Click me</Button>)
      
      fireEvent.click(screen.getByRole('button'))
      
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('does not fire click when disabled', () => {
      const handleClick = vi.fn()
      render(<Button disabled onClick={handleClick}>Click me</Button>)
      
      fireEvent.click(screen.getByRole('button'))
      
      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('Custom className', () => {
    it('merges custom className with base classes', () => {
      render(<Button className="custom-class">Custom</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
      expect(button).toHaveClass('inline-flex')
    })
  })

  describe('AsChild prop', () => {
    it('renders as child component when asChild is true', () => {
      render(
        <Button asChild>
          <a href="/test">Link Button</a>
        </Button>
      )
      
      const link = screen.getByRole('link', { name: /link button/i })
      expect(link).toBeInTheDocument()
      expect(link).toHaveAttribute('href', '/test')
    })
  })
})
