import os
import tkinter as tk
from tkinter import filedialog, messagebox
from param_extraction import *

def run_analysis():
    try:
        path = path_var.get()

        channel = int(channel_var.get())
        width = float(width_var.get()) * 1e-6
        length = float(length_var.get()) * 1e-6
        thickness = float(thickness_var.get()) * 1e-9
        T_normal = float(tnormal_var.get())

        print("Running analysis...")
        print(f"Path: {path}")
        print(f"PPMS Channel: {channel}")
        print(f"Dimensions: {(width, length, thickness)}")
        print(f"T_normal: {T_normal}")

        sample_ID = path.split('/')[-1]

        df_out_SI, df_out = main(sample_ID, path, channel, (width, length, thickness),T_normal)

        results_text.delete("1.0", tk.END)

        results_text.insert(tk.END, f"=== {sample_ID} Analysis Results ===\n")
        results_text.insert(tk.END, "=== Customary Units ===\n")
        results_text.insert(
            tk.END,
            df_out.to_string(
                index=False,
                float_format=lambda x: f"{x:.5g}"
            )
        )

        results_text.insert(tk.END, "\n\n=== SI Units ===\n")
        results_text.insert(
            tk.END,
            df_out_SI.to_string(
                index=False,
                float_format=lambda x: f"{x:.5g}"
            )
        )

        messagebox.showinfo("Done", f"Analysis complete. Results saved to {path}.")

    except Exception as e:
        messagebox.showerror("Error", str(e))

def browse():
    folder = filedialog.askdirectory(initialdir=os.getcwd())
    if folder:
        path_var.set(folder)

# Make window
root = tk.Tk()
root.title("Superconducting Parameter Extraction")
root.geometry("1200x600")

instruction_frame = tk.LabelFrame(
    root,
    text="Instructions",
    padx=10,
    pady=5
)

instruction_frame.grid(
    row=0,
    column=0,
    columnspan=3,
    sticky="ew",
    padx=5,
    pady=5
)

instructions = (
    "1. Create a folder named after your sample (e.g. 'MySample').\n"
    "2. Create a subfolder called 'data' inside it.\n"
    "3. Copy all PPMS .dat files into 'MySample/data'.\n"
    "4. Select the folder 'MySample' below.\n"
    "5. Enter PPMS channel and wire geometry.\n"
    "6. Click Run Analysis."
)

tk.Label(
    instruction_frame,
    text=instructions,
    justify="left",
).pack(anchor="w")

# Directory
tk.Label(root, text="Path to Sample Folder (not 'data')").grid(row=1, column=0, sticky="w", padx=5, pady=5)
path_var = tk.StringVar()
tk.Entry(root, textvariable=path_var, width=60).grid(row=1, column=1, padx=5)
tk.Button(root, text="Browse", command=browse).grid(row=1, column=2, padx=5)

# Channel
tk.Label(root, text="PPMS Channel").grid(row=2, column=0, sticky="w", padx=5)
channel_var = tk.StringVar(value="1")
tk.Entry(root, textvariable=channel_var).grid(row=2, column=1, sticky="w")

# Geometry
width_var = tk.StringVar(value="50")
length_var = tk.StringVar(value="1000")
thickness_var = tk.StringVar(value="10")

tk.Label(root, text="Width (um)").grid(row=3, column=0, sticky="w", padx=5)
tk.Entry(root, textvariable=width_var).grid(row=3, column=1, sticky="w")

tk.Label(root, text="Length (um)").grid(row=4, column=0, sticky="w", padx=5)
tk.Entry(root, textvariable=length_var).grid(row=4, column=1, sticky="w")

tk.Label(root, text="Thickness (nm)").grid(row=5, column=0, sticky="w", padx=5)
tk.Entry(root, textvariable=thickness_var).grid(row=5, column=1, sticky="w")

# T_normal
tnormal_var = tk.StringVar(value="40")
tk.Label(root, text="Normal Temp (K)").grid(row=6, column=0, sticky="w", padx=5)
tk.Entry(root, textvariable=tnormal_var).grid(row=6, column=1, sticky="w")

# Run
tk.Button(root, text="Run Analysis", command=run_analysis, height=2).grid(row=7, column=0, columnspan=3, pady=15)
root.grid_rowconfigure(8, weight=1)
root.grid_columnconfigure(1, weight=1)

# Results display
results_frame = tk.Frame(root)
results_frame.grid(row=8, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

scrollbar = tk.Scrollbar(results_frame)
results_text = tk.Text(results_frame, height=12, width=100, wrap="none", yscrollcommand=scrollbar.set)
scrollbar.config(command=results_text.yview)

results_text.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Run main loop
root.mainloop()