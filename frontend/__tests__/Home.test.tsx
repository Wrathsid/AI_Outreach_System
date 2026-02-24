import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Home from '@/app/page'

// Mock the API client and Dashboard component to avoid real network requests
jest.mock('@/lib/api', () => ({
  api: {
    getActivity: jest.fn().mockResolvedValue([]),
    getStats: jest.fn().mockResolvedValue({
      weekly_goal_percent: 0,
      people_found: 0,
      emails_sent: 0,
      account_health: 100,
      is_safe: true,
      recent_leads: [],
      top_industries: []
    }),
    getCandidates: jest.fn().mockResolvedValue([]),
  }
}))

// We can just spy on the dashboard rendering
jest.mock('@/components/Dashboard', () => {
  return function MockDashboard() {
    return <div data-testid="mock-dashboard">Dashboard Component</div>
  }
})

describe('Home Page', () => {
  it('renders without crashing', () => {
    render(<Home />)
    expect(screen.getByTestId('mock-dashboard')).toBeInTheDocument()
  })
})
