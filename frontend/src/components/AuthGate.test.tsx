import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthGate } from "@/components/AuthGate";
import { initialData } from "@/lib/kanban";

describe("AuthGate", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows login form when unauthenticated and signs in then signs out", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ username: "user" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(initialData), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "ok" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

    render(<AuthGate />);

    expect(
      await screen.findByRole("button", { name: /sign in/i })
    ).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
    expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /sign out/i }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /sign in/i })
      ).toBeInTheDocument();
    });

    expect(fetchMock).toHaveBeenCalledTimes(4);
  });

  it("shows an error on invalid credentials", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Invalid username or password" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        })
      );

    render(<AuthGate />);

    await userEvent.type(
      await screen.findByLabelText(/username/i),
      "user"
    );
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /invalid username or password/i
    );
  });
});
