import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Sidebar from '@/components/Sidebar'

jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/'),
  useRouter: jest.fn(() => ({
    push: jest.fn(),
  })),
}))

describe('Sidebar', () => {
  it('renders navigation links', () => {
    render(<Sidebar />)
    
    // Each label renders twice (mobile text + desktop tooltip), so use getAllByText
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Pipeline').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Search').length).toBeGreaterThanOrEqual(1)
  })

  it('renders the settings link', () => {
    render(<Sidebar />)
    expect(screen.getAllByText('Settings').length).toBeGreaterThanOrEqual(1)
  })

  it('renders the Personal Brain link', () => {
    render(<Sidebar />)
    expect(screen.getAllByText('Personal Brain').length).toBeGreaterThanOrEqual(1)
  })
})
