"""Tkinter GUI for Booth's multiplication algorithm.

Run with:
    python booth_multiplier_tkinter.py
"""

import tkinter as tk
from tkinter import messagebox, ttk


def twos_complement_bits(value: int, bits: int) -> str:
    """Return the two's-complement binary representation of value."""
    mask = (1 << bits) - 1
    return format(value & mask, f"0{bits}b")


def signed_from_bits(bit_string: str) -> int:
    """Convert a two's-complement bit string to a signed integer."""
    value = int(bit_string, 2)
    if bit_string[0] == "1":
        value -= 1 << len(bit_string)
    return value


def arithmetic_shift_right(a_bits: str, q_bits: str, q_minus_one: str) -> tuple[str, str, str]:
    """Shift the combined A, Q, Q-1 register right arithmetically."""
    combined = a_bits + q_bits + q_minus_one
    shifted = combined[0] + combined[:-1]
    size = len(a_bits)
    return shifted[:size], shifted[size : size * 2], shifted[-1]


def booth_multiply(multiplicand: int, multiplier: int, bits: int) -> tuple[int, list[dict[str, str]]]:
    """Multiply two signed integers with Booth's algorithm and return trace rows."""
    if bits < 2:
        raise ValueError("Bit size must be at least 2.")

    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    if not (minimum <= multiplicand <= maximum and minimum <= multiplier <= maximum):
        raise ValueError(f"Both numbers must fit in {bits}-bit signed range ({minimum} to {maximum}).")

    a_bits = "0" * bits
    q_bits = twos_complement_bits(multiplier, bits)
    q_minus_one = "0"
    rows: list[dict[str, str]] = []

    for step in range(1, bits + 1):
        pair = q_bits[-1] + q_minus_one
        if pair == "01":
            action = "A = A + M"
            a_value = signed_from_bits(a_bits) + multiplicand
            a_bits = twos_complement_bits(a_value, bits)
        elif pair == "10":
            action = "A = A - M"
            a_value = signed_from_bits(a_bits) - multiplicand
            a_bits = twos_complement_bits(a_value, bits)
        else:
            action = "No operation"

        rows.append(
            {
                "step": str(step),
                "pair": pair,
                "action": action,
                "a_before_shift": a_bits,
                "q_before_shift": q_bits,
                "q_minus_one_before_shift": q_minus_one,
            }
        )

        a_bits, q_bits, q_minus_one = arithmetic_shift_right(a_bits, q_bits, q_minus_one)
        rows[-1].update({"a_after_shift": a_bits, "q_after_shift": q_bits, "q_minus_one_after_shift": q_minus_one})

    product_bits = a_bits + q_bits
    return signed_from_bits(product_bits), rows


class BoothMultiplierApp(tk.Tk):
    """Small Tkinter application that visualizes Booth multiplication."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Booth Multiplication")
        self.geometry("980x520")
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self) -> None:
        input_frame = ttk.LabelFrame(self, text="Inputs")
        input_frame.pack(fill="x", padx=12, pady=10)

        ttk.Label(input_frame, text="Multiplicand (M):").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.multiplicand_var = tk.StringVar(value="7")
        ttk.Entry(input_frame, textvariable=self.multiplicand_var, width=12).grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(input_frame, text="Multiplier (Q):").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.multiplier_var = tk.StringVar(value="-3")
        ttk.Entry(input_frame, textvariable=self.multiplier_var, width=12).grid(row=0, column=3, padx=8, pady=8)

        ttk.Label(input_frame, text="Bits:").grid(row=0, column=4, padx=8, pady=8, sticky="w")
        self.bits_var = tk.StringVar(value="5")
        ttk.Entry(input_frame, textvariable=self.bits_var, width=8).grid(row=0, column=5, padx=8, pady=8)

        ttk.Button(input_frame, text="Calculate", command=self.calculate).grid(row=0, column=6, padx=8, pady=8)
        ttk.Button(input_frame, text="Clear", command=self.clear).grid(row=0, column=7, padx=8, pady=8)

        self.result_var = tk.StringVar(value="Enter values and click Calculate.")
        ttk.Label(self, textvariable=self.result_var, font=("Arial", 12, "bold")).pack(anchor="w", padx=12)

        columns = (
            "step",
            "pair",
            "action",
            "a_before_shift",
            "q_before_shift",
            "q_minus_one_before_shift",
            "a_after_shift",
            "q_after_shift",
            "q_minus_one_after_shift",
        )
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        headings = {
            "step": "Step",
            "pair": "Q0Q-1",
            "action": "Action",
            "a_before_shift": "A before shift",
            "q_before_shift": "Q before shift",
            "q_minus_one_before_shift": "Q-1 before",
            "a_after_shift": "A after shift",
            "q_after_shift": "Q after shift",
            "q_minus_one_after_shift": "Q-1 after",
        }
        widths = {"step": 55, "pair": 70, "action": 110}
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths.get(column, 120), anchor="center")

        y_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=12)
        y_scroll.pack(side="right", fill="y", padx=(0, 12), pady=12)

    def calculate(self) -> None:
        try:
            multiplicand = int(self.multiplicand_var.get())
            multiplier = int(self.multiplier_var.get())
            bits = int(self.bits_var.get())
            product, rows = booth_multiply(multiplicand, multiplier, bits)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.clear_table()
        for row in rows:
            self.tree.insert("", "end", values=tuple(row[column] for column in self.tree["columns"]))

        product_bits = twos_complement_bits(product, bits * 2)
        self.result_var.set(f"Product: {multiplicand} × {multiplier} = {product}  (binary: {product_bits})")

    def clear_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def clear(self) -> None:
        self.clear_table()
        self.result_var.set("Enter values and click Calculate.")


if __name__ == "__main__":
    BoothMultiplierApp().mainloop()
