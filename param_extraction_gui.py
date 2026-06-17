import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

from param_extraction import main

def run_analysis():
    try:
        path = path_var.get().strip()
        if not path:
            raise ValueError("Please select a sample folder.")

        channel = int(channel_var.get())
        width = float(width_var.get()) * 1e-6
        length = float(length_var.get()) * 1e-6
        thickness = float(thickness_var.get()) * 1e-9
        sc_criterion = float(sc_criterion_var.get())
        T_normal = float(tnormal_var.get())

        sample_ID = os.path.basename(path)

        print("Running analysis...")
        print(f"Path: {path}")
        print(f"Sample ID: {sample_ID}")
        print(f"PPMS Channel: {channel}")
        print(f"Dimensions: {(width, length, thickness)}")
        print(f"Superconducting Criterion: {sc_criterion}")
        print(f"Normal Temperature: {T_normal}")

        df_out_SI, df_out = main(
            sample_ID,
            path,
            channel,
            (width, length, thickness),
            sc_criterion=sc_criterion,
            T_normal=T_normal,
        )

        results_text.delete("1.0", tk.END)

        results_text.insert(tk.END, f"=== {sample_ID} Analysis Results ===\n\n")
        results_text.insert(tk.END, "=== Customary Units ===\n")
        results_text.insert(tk.END, df_out.to_string(index=False, float_format=lambda x: f"{x:.5g}"))

        results_text.insert(tk.END, "\n\n=== SI Units ===\n")
        results_text.insert(tk.END, df_out_SI.to_string(index=False, float_format=lambda x: f"{x:.5g}"))

        messagebox.showinfo("Done", f"Analysis complete.\n\nResults saved to:\n{path}")

    except Exception as e:
        messagebox.showerror("Error", str(e))


def browse():
    folder = filedialog.askdirectory(initialdir=path_var.get().strip() or os.getcwd())
    if folder:
        path_var.set(folder)


root = tk.Tk()
root.title("Superconducting Parameter Extraction")
root.geometry("1200x700")
root.minsize(1000, 600)

instruction_frame = tk.LabelFrame(root, text="Instructions", padx=10, pady=5)
instruction_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

instructions = (
    "1. Create a folder named after your sample (e.g. 'MySample').\n"
    "2. Create a subfolder called 'data' inside it.\n"
    "3. Copy all PPMS .dat files into 'MySample/data'.\n"
    "4. Click Browse and select the 'MySample' folder.\n"
    "5. Enter PPMS channel, geometry, superconducting criterion, and normal-state temperature.\n"
    "6. Click Run Analysis."
)

tk.Label(instruction_frame, text=instructions, justify="left").pack(anchor="w")

path_var = tk.StringVar()
channel_var = tk.StringVar(value="1")
thickness_var = tk.StringVar(value="10")
width_var = tk.StringVar(value="20")
length_var = tk.StringVar(value="1000")
sc_criterion_var = tk.StringVar(value="0.5")
tnormal_var = tk.StringVar(value="40")

tk.Label(root, text="Path to folder").grid(row=1, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=path_var, width=70).grid(row=1, column=1, padx=5, sticky="ew")
tk.Button(root, text="Browse", command=browse).grid(row=1, column=2, padx=5)

tk.Label(root, text="PPMS Channel").grid(row=2, column=0, sticky="w", padx=5)
tk.Entry(root, textvariable=channel_var).grid(row=2, column=1, sticky="w")

tk.Label(root, text="Thickness (nm)").grid(row=3, column=0, sticky="w", padx=5)
tk.Entry(root, textvariable=thickness_var).grid(row=3, column=1, sticky="w")

ttk.Separator(root, orient="horizontal").grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=10)

underline_font = tkfont.Font(size=10, weight="bold", underline=True)
tk.Label(root, text="Extra Parameters", font=underline_font).grid(row=5, column=0, sticky="w", padx=5)

tk.Label(root, text="Width (um)").grid(row=6, column=0, sticky="w", padx=5)
tk.Entry(root, textvariable=width_var).grid(row=6, column=1, sticky="w")

tk.Label(root, text="Length (um)").grid(row=7, column=0, sticky="w", padx=5)
tk.Entry(root, textvariable=length_var).grid(row=7, column=1, sticky="w")

tk.Label(root, text="Superconducting Criterion").grid(row=8, column=0, sticky="w", padx=5)
tk.Entry(root, textvariable=sc_criterion_var).grid(row=8, column=1, sticky="w")

tk.Label(root, text="Normal Temp (K)").grid(row=9, column=0, sticky="w", padx=5)
tk.Entry(root, textvariable=tnormal_var).grid(row=9, column=1, sticky="w")

tk.Button(root, text="Run Analysis", command=run_analysis, height=2).grid(row=10, column=0, columnspan=3, pady=15)

results_frame = tk.Frame(root)
results_frame.grid(row=11, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

scrollbar_y = tk.Scrollbar(results_frame)
results_text = tk.Text(results_frame, height=12, width=120, wrap="none", font=("Consolas", 10), yscrollcommand=scrollbar_y.set)

scrollbar_y.config(command=results_text.yview)

results_text.pack(side="left", fill="both", expand=True)
scrollbar_y.pack(side="right", fill="y")

root.grid_rowconfigure(11, weight=1)
root.grid_columnconfigure(1, weight=1)

root.mainloop()