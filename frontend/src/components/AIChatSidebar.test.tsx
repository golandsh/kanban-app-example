import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AIChatSidebar } from "@/components/AIChatSidebar";
import { initialData } from "@/lib/kanban";

describe("AIChatSidebar", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends a message and renders AI reply without updating board when updated is false", async () => {
    const onBoardUpdate = vi.fn();
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          reply: "You have 8 cards.",
          updated: false,
          board: initialData,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    render(<AIChatSidebar onBoardUpdate={onBoardUpdate} />);

    await userEvent.type(
      screen.getByLabelText("AI chat message"),
      "How many cards?"
    );
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(await screen.findByText("You have 8 cards.")).toBeInTheDocument();
    expect(onBoardUpdate).not.toHaveBeenCalled();
  });

  it("calls onBoardUpdate when AI updates the board", async () => {
    const onBoardUpdate = vi.fn();
    const updatedBoard = {
      ...initialData,
      cards: {
        ...initialData.cards,
        "card-ai-1": {
          id: "card-ai-1",
          title: "AI Card",
          details: "Created by AI",
        },
      },
    };

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          reply: "Added AI Card.",
          updated: true,
          board: updatedBoard,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    render(<AIChatSidebar onBoardUpdate={onBoardUpdate} />);

    await userEvent.type(
      screen.getByLabelText("AI chat message"),
      "Add AI Card"
    );
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(await screen.findByText("Added AI Card.")).toBeInTheDocument();
    expect(onBoardUpdate).toHaveBeenCalledWith(updatedBoard);
  });
});
