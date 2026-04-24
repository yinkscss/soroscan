import { render, screen, fireEvent } from "@testing-library/react"
import { Alert } from "@/components/ui/alert"

describe("Alert Component", () => {
  it("renders all 4 variants correctly", () => {
    const variants = ["info", "success", "warning", "error"] as const
    variants.forEach((v) => {
      const { unmount } = render(<Alert variant={v} title={`${v} alert`} />)
      expect(screen.getByText(`${v} alert`)).toBeInTheDocument()
      unmount()
    })
  })

  it("handles the dismissible toggle", () => {
    const onDismiss = jest.fn()
    render(<Alert title="Dismissible" onDismiss={onDismiss} />)
    const button = screen.getByLabelText("Dismiss alert")
    fireEvent.click(button)
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it("displays title and description in the correct layout", () => {
    render(<Alert title="Alert Title" description="Detailed info here" />)
    expect(screen.getByText("Alert Title")).toBeInTheDocument()
    expect(screen.getByText("Detailed info here")).toBeInTheDocument()
  })
})