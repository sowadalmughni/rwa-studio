/**
 * Card Component Tests
 * Author: Sowad Al-Mughni
 * 
 * Tests for Card components (Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter)
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter 
} from './card'

describe('Card Components', () => {
  describe('Card', () => {
    it('renders with default props', () => {
      render(<Card>Card content</Card>)
      
      const card = screen.getByText('Card content')
      expect(card).toBeInTheDocument()
    })

    it('has correct data-slot attribute', () => {
      render(<Card data-testid="card">Content</Card>)
      
      const card = screen.getByTestId('card')
      expect(card).toHaveAttribute('data-slot', 'card')
    })

    it('applies base styles', () => {
      render(<Card data-testid="card">Content</Card>)
      
      const card = screen.getByTestId('card')
      expect(card).toHaveClass('bg-card')
      expect(card).toHaveClass('rounded-xl')
      expect(card).toHaveClass('border')
    })

    it('merges custom className', () => {
      render(<Card className="custom-class" data-testid="card">Content</Card>)
      
      const card = screen.getByTestId('card')
      expect(card).toHaveClass('custom-class')
      expect(card).toHaveClass('bg-card')
    })
  })

  describe('CardHeader', () => {
    it('renders children', () => {
      render(<CardHeader>Header content</CardHeader>)
      
      expect(screen.getByText('Header content')).toBeInTheDocument()
    })

    it('has correct data-slot attribute', () => {
      render(<CardHeader data-testid="header">Header</CardHeader>)
      
      const header = screen.getByTestId('header')
      expect(header).toHaveAttribute('data-slot', 'card-header')
    })
  })

  describe('CardTitle', () => {
    it('renders title text', () => {
      render(<CardTitle>Test Title</CardTitle>)
      
      expect(screen.getByText('Test Title')).toBeInTheDocument()
    })

    it('has correct data-slot attribute', () => {
      render(<CardTitle data-testid="title">Title</CardTitle>)
      
      const title = screen.getByTestId('title')
      expect(title).toHaveAttribute('data-slot', 'card-title')
    })

    it('applies font-semibold style', () => {
      render(<CardTitle data-testid="title">Title</CardTitle>)
      
      const title = screen.getByTestId('title')
      expect(title).toHaveClass('font-semibold')
    })
  })

  describe('CardDescription', () => {
    it('renders description text', () => {
      render(<CardDescription>Description text</CardDescription>)
      
      expect(screen.getByText('Description text')).toBeInTheDocument()
    })

    it('has correct data-slot attribute', () => {
      render(<CardDescription data-testid="desc">Description</CardDescription>)
      
      const desc = screen.getByTestId('desc')
      expect(desc).toHaveAttribute('data-slot', 'card-description')
    })

    it('applies muted text style', () => {
      render(<CardDescription data-testid="desc">Description</CardDescription>)
      
      const desc = screen.getByTestId('desc')
      expect(desc).toHaveClass('text-muted-foreground')
    })
  })

  describe('CardContent', () => {
    it('renders content', () => {
      render(<CardContent>Main content</CardContent>)
      
      expect(screen.getByText('Main content')).toBeInTheDocument()
    })

    it('has correct data-slot attribute', () => {
      render(<CardContent data-testid="content">Content</CardContent>)
      
      const content = screen.getByTestId('content')
      expect(content).toHaveAttribute('data-slot', 'card-content')
    })

    it('applies padding styles', () => {
      render(<CardContent data-testid="content">Content</CardContent>)
      
      const content = screen.getByTestId('content')
      expect(content).toHaveClass('px-6')
    })
  })

  describe('CardFooter', () => {
    it('renders footer content', () => {
      render(<CardFooter>Footer content</CardFooter>)
      
      expect(screen.getByText('Footer content')).toBeInTheDocument()
    })

    it('has correct data-slot attribute', () => {
      render(<CardFooter data-testid="footer">Footer</CardFooter>)
      
      const footer = screen.getByTestId('footer')
      expect(footer).toHaveAttribute('data-slot', 'card-footer')
    })
  })

  describe('Full Card Composition', () => {
    it('renders complete card with all parts', () => {
      render(
        <Card data-testid="full-card">
          <CardHeader>
            <CardTitle>Card Title</CardTitle>
            <CardDescription>Card description</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Main card content goes here</p>
          </CardContent>
          <CardFooter>
            <button>Action</button>
          </CardFooter>
        </Card>
      )

      expect(screen.getByText('Card Title')).toBeInTheDocument()
      expect(screen.getByText('Card description')).toBeInTheDocument()
      expect(screen.getByText('Main card content goes here')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument()
    })
  })
})
