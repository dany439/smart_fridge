import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import date

# --- Smart Fridge imports ---
from src.setup_db import ensure_schema
from src.smart_fridge_db import (
    add_item_simple,
    add_item_by_image,
    get_all_items,
    consume,
    clear_database
)
from src.recipe_service import get_recipe_suggestions_for_user


# ==============================
# Main Application
# ==============================

class SmartFridgeGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Smart Fridge")
        self.geometry("1000x600")

        ensure_schema()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.suggestion_tab = SuggestionTab(self.notebook)
        self.food_tab = FoodTab(self.notebook)
        self.insert_tab = InsertTab(self.notebook, self.food_tab)
        self.consume_tab = ConsumeTab(self.notebook, self.food_tab)

        self.notebook.add(self.insert_tab, text="Insert")
        self.notebook.add(self.suggestion_tab, text="Suggestions")
        self.notebook.add(self.food_tab, text="View Food")
        self.notebook.add(self.consume_tab, text="Consumption")


# ==============================
# Insert Tab
# ==============================

class InsertTab(ttk.Frame):
    def __init__(self, parent, food_tab):
        super().__init__(parent)
        self.food_tab = food_tab

        # ---------- Insert by Name ----------
        name_frame = ttk.LabelFrame(self, text="Insert by Name")
        name_frame.pack(fill="x", padx=10, pady=10)

        self.name_var = tk.StringVar()
        self.qty_var = tk.DoubleVar(value=1)
        self.unit_var = tk.StringVar(value="pcs")
        self.exp_var = tk.StringVar()
        self.storage_var = tk.StringVar(value="fridge")
        self.slot_var = tk.StringVar()

        self._row(name_frame, "Food name:", self.name_var, 0)
        self._row(name_frame, "Quantity:", self.qty_var, 1)
        self._row(name_frame, "Unit:", self.unit_var, 2)
        self._row(name_frame, "Expiration (YYYY-MM-DD, optional):", self.exp_var, 3)
        ttk.Label(name_frame, text="Storage:").grid(row=4, column=0, sticky="w", padx=5)
        ttk.Combobox(
            name_frame,
            textvariable=self.storage_var,
            values=["fridge", "freezer"],
            state="readonly",
            width=28
        ).grid(row=4, column=1, padx=5)
        self._row(name_frame, "Location slot (optional):", self.slot_var, 5)

        ttk.Button(
            name_frame,
            text="Add Item",
            command=self.add_by_name
        ).grid(row=6, column=1, pady=5)

        # ---------- Insert by Image ----------
        img_frame = ttk.LabelFrame(self, text="Insert by Image")
        img_frame.pack(fill="x", padx=10, pady=10)

        self.img_path = tk.StringVar()
        self.img_qty = tk.DoubleVar(value=1)
        self.img_unit = tk.StringVar(value="pcs")
        self.img_exp_var = tk.StringVar()
        self.img_storage_var = tk.StringVar(value="fridge")
        self.img_slot_var = tk.StringVar()


        ttk.Button(
            img_frame, text="Choose Image", command=self.pick_image
        ).grid(row=0, column=0, padx=5, pady=5)

        ttk.Label(img_frame, textvariable=self.img_path).grid(row=0, column=1, sticky="w")

        self._row(img_frame, "Quantity:", self.img_qty, 1)
        self._row(img_frame, "Unit:", self.img_unit, 2)
        self._row(img_frame, "Expiration (YYYY-MM-DD, optional):", self.img_exp_var, 3)

        ttk.Label(img_frame, text="Storage:").grid(row=4, column=0, sticky="w", padx=5)
        ttk.Combobox(
            img_frame,
            textvariable=self.img_storage_var,
            values=["fridge", "freezer"],
            state="readonly",
            width=28
        ).grid(row=4, column=1, padx=5)

        self._row(img_frame, "Location slot (optional):", self.img_slot_var, 5)


        ttk.Button(
            img_frame,
            text="Add by Image",
            command=self.add_by_image
        ).grid(row=6, column=1, pady=5)

    def _row(self, frame, label, var, row):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(frame, textvariable=var, width=30).grid(row=row, column=1, padx=5, pady=2)

    def pick_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if path:
            self.img_path.set(path)

    def add_by_name(self):
        try:
            expiration = None
            if self.storage_var.get() == "fridge":
                expiration = self.exp_var.get() or None

            add_item_simple(
                name=self.name_var.get(),
                quantity=self.qty_var.get(),
                unit=self.unit_var.get(),
                expiration_date=expiration,
                storage=self.storage_var.get(),
                location_slot=self.slot_var.get() or None
            )
            self.food_tab.refresh()


            messagebox.showinfo("Success", "Item added successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def add_by_image(self):
        try:
            expiration = None
            if self.img_storage_var.get() == "fridge":
                expiration = self.img_exp_var.get() or None

            add_item_by_image(
                image_path=self.img_path.get(),
                quantity=self.img_qty.get(),
                unit=self.img_unit.get(),
                expiration_date=expiration,
                storage=self.img_storage_var.get(),
                location_slot=self.img_slot_var.get() or None
            )
            self.food_tab.refresh()


            messagebox.showinfo("Success", "Item added by image")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ==============================
# Suggestions Tab
# ==============================

class SuggestionTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        ttk.Button(
            self,
            text="Generate Recipe Suggestions",
            command=self.generate
        ).pack(pady=10)

        self.text = tk.Text(self, wrap="word")
        self.text.pack(fill="both", expand=True, padx=10, pady=10)

    def generate(self):
        self.text.delete("1.0", tk.END)

        self.text.insert(tk.END, "Generating...\n")
        self.text.update_idletasks()   # 👈 force redraw

        recipes = get_recipe_suggestions_for_user(user_id=1, max_recipes=5)

        self.text.delete("1.0", tk.END)

        if not recipes:
            self.text.insert(tk.END, "No recipes available.\n")
            return
        
        for i, r in enumerate(recipes, start=1):
            self.text.insert(tk.END, f"Recipe {i}: {r['title']}\n")
            self.text.insert(tk.END, f"Urgency score: {r['expiry_score']}\n\n")
            self.text.insert(tk.END, "Available:\n")
            for ing in r.get("ingredients_available", []):
                self.text.insert(tk.END, f"  - {ing}\n")
            self.text.insert(tk.END, "\nMissing:\n")
            for ing in r.get("ingredients_missing", []):
                self.text.insert(tk.END, f"  - {ing}\n")
            self.text.insert(tk.END, "\nSteps:\n")
            for idx, step in enumerate(r.get("steps", []), start=1):
                self.text.insert(tk.END, f"{idx}. {step}\n")
            self.text.insert(tk.END, "\n" + "=" * 50 + "\n\n")


# ==============================
# Food Tab
# ==============================

class FoodTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        cols = (
            "item_id", "food_name", "storage",
            "quantity", "unit",
            "expiration_date", "location_slot", "date_added"
        )


        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=130)

        self.tree.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)

        ttk.Button(
            btn_frame,
            text="Refresh",
            command=self.refresh
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="Clear All",
            command=self.clear_all
        ).pack(side="left", padx=5)

        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for item in get_all_items():
            self.tree.insert("", tk.END, values=(
                item["item_id"],
                item["food_name"],
                item["storage"],
                item["quantity"],
                item["unit"],
                item["expiration_date"],
                item["location_slot"],
                item["date_added"],
            ))

    
    def clear_all(self):
        confirm = messagebox.askyesno(
            "Confirm Clear",
            "This will permanently delete ALL food items.\n\nAre you sure?"
        )

        if confirm:
            clear_database()
            self.refresh()
            messagebox.showinfo("Cleared", "All food items have been removed.")


# ==============================
# Consumption Tab
# ==============================

class ConsumeTab(ttk.Frame):
    def __init__(self, parent, food_tab):
        super().__init__(parent)
        self.food_tab = food_tab

        self.name_var = tk.StringVar()
        self.id_var = tk.IntVar()
        self.qty_var = tk.DoubleVar()

        ttk.Label(self, text="Food name:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(self, textvariable=self.name_var).grid(row=0, column=1)

        ttk.Label(self, text="Item ID (optional):").grid(row=1, column=0)
        ttk.Entry(self, textvariable=self.id_var).grid(row=1, column=1)

        ttk.Label(self, text="Consumed quantity:").grid(row=2, column=0)
        ttk.Entry(self, textvariable=self.qty_var).grid(row=2, column=1)

        ttk.Button(
            self,
            text="Consume",
            command=self.consume_item
        ).grid(row=3, column=1, pady=10)

    def consume_item(self):
        try:
            result = consume(
                name=self.name_var.get(),
                qty_used=self.qty_var.get(),
                item_id=self.id_var.get() or None
            )
            self.food_tab.refresh()
            messagebox.showinfo("Success", f"Item {result}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ==============================
# Run
# ==============================

if __name__ == "__main__":
    app = SmartFridgeGUI()
    app.mainloop()
