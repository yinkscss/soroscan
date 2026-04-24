import { render, screen } from "@testing-library/react"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import "@testing-library/jest-dom"

describe("Input Component with Validation States", () => {
  it("should render the label and accept text", () => {
    render(
      <div>
        <Label htmlFor="test-input">Username</Label>
        <Input id="test-input" placeholder="Enter username" />
      </div>
    )
    const input = screen.getByPlaceholderText("Enter username")
    expect(screen.getByText("Username")).toBeInTheDocument()
    expect(input).toBeInTheDocument()
  })

  it("should show required indicator when required prop is passed", () => {
    render(<Label required>Email</Label>)
    expect(screen.getByText("*")).toBeInTheDocument()
    expect(screen.getByText("*")).toHaveClass("text-destructive")
  })

  it("should apply error styles when state is error", () => {
    render(<Input state="error" data-testid="error-input" />)
    const input = screen.getByTestId("error-input")
    expect(input).toHaveClass("border-destructive")
    expect(input).toHaveAttribute("aria-invalid", "true")
  })

  it("should apply success styles when state is success", () => {
    render(<Input state="success" data-testid="success-input" />)
    const input = screen.getByTestId("success-input")
    expect(input).toHaveClass("border-green-500")
  })

  it("should be disabled when disabled prop is passed", () => {
    render(<Input disabled placeholder="Disabled input" />)
    const input = screen.getByPlaceholderText("Disabled input")
    expect(input).toBeDisabled()
  })
})