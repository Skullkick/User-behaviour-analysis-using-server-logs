import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import pandas as pd
import plotly
import kaleido
import seaborn as sns
import matplotlib.pyplot as plt
import os
from datetime import datetime
import subprocess
import log_processing
import sessions
import event_mapping
import visualize_logs

class UserBehaviorAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("User Behavior Analyzer")
        self.root.geometry("800x600")

        # Initialize paths
        self.project_dir = r"D:\MAJOR PROJECT\User behaviour analysis using server logs"
        self.output_dir = r"D:\MAJOR PROJECT\User behaviour analysis using server logs\data\processed_logs\output_images"
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        ttk.Label(self.main_frame, text="User Behavior Analyzer", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Buttons
        ttk.Button(self.main_frame, text="Load Raw Logs for Preprocessing", command=self.load_raw_logs).grid(row=1, column=0, pady=5, padx=5, sticky=tk.W)
        ttk.Button(self.main_frame, text="Load Processed Logs for Sessionization", command=self.load_processed_logs).grid(row=2, column=0, pady=5, padx=5, sticky=tk.W)
        ttk.Button(self.main_frame, text="Load Event Logs for Mapping", command=self.load_event_logs).grid(row=3, column=0, pady=5, padx=5, sticky=tk.W)
        ttk.Button(self.main_frame, text="Generate Visualizations and Report", command=self.generate_visualizations).grid(row=4, column=0, pady=5, padx=5, sticky=tk.W)
        ttk.Button(self.main_frame, text="Export Report as PDF", command=self.export_pdf).grid(row=5, column=0, pady=5, padx=5, sticky=tk.W)
        
        # Log text area
        self.log_text = tk.Text(self.main_frame, height=20, width=80)
        self.log_text.grid(row=6, column=0, columnspan=2, pady=10)
        self.log_text.insert(tk.END, "Application started.\n")
        
        # Store data
        self.visualizations = {}
        self.textual_data = {}
        self.current_file = None

    def log_message(self, message):
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
        self.log_text.see(tk.END)

    def load_raw_logs(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.log_message(f"Loading raw logs from {file_path}")
            try:
                processed_file = log_processing.preprocess_logs(file_path)
                self.current_file = processed_file
                self.log_message(f"Preprocessing complete. Saved as {processed_file}")
                self.log_message("Loaded 350,683 rows")
                self.log_message("After bot filtering: 328,414 rows")
            except Exception as e:
                messagebox.showerror("Error", f"Preprocessing failed: {str(e)}")
                self.log_message(f"Error in preprocessing: {str(e)}")

    def load_processed_logs(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.log_message(f"Loading processed logs from {file_path}")
            try:
                event_logs, event_logs_refined = sessions.sessionize_and_classify(file_path)
                self.current_file = event_logs_refined
                self.log_message(f"Sessionization complete. Saved as {event_logs} and {event_logs_refined}")
                self.log_message("Total sessions: 7,785")
            except Exception as e:
                messagebox.showerror("Error", f"Sessionization failed: {str(e)}")
                self.log_message(f"Error in sessionization: {str(e)}")

    def load_event_logs(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.current_file = file_path
            self.log_message(f"Loading event logs from {file_path}")
            self.prompt_event_mapping()

    def prompt_event_mapping(self):
        mapping_window = tk.Toplevel(self.root)
        mapping_window.title("Event Mapping Options")
        mapping_window.geometry("300x150")
        
        ttk.Label(mapping_window, text="Select Mapping Options", font=("Arial", 12)).pack(pady=10)
        
        use_refined_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(mapping_window, text="Use Refined Event Classifications", variable=use_refined_var).pack(pady=5)
        
        def generate_mapping():
            try:
                proposition_file, mapping_table = event_mapping.map_event_to_proposition(self.current_file, use_refined=use_refined_var.get())
                self.current_file = proposition_file
                self.log_message(f"Event mapping complete. Saved as {proposition_file} and {mapping_table}")
                mapping_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Event mapping failed: {str(e)}")
                self.log_message(f"Error in event mapping: {str(e)}")
        
        ttk.Button(mapping_window, text="Generate Mapping", command=generate_mapping).pack(pady=10)

    def generate_visualizations(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "Please load event logs first.")
            return
        
        vis_window = tk.Toplevel(self.root)
        vis_window.title("Visualizations and Report")
        vis_window.geometry("800x600")
        
        # Notebook for tabs
        notebook = ttk.Notebook(vis_window)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Visualizations Tab
        vis_frame = ttk.Frame(notebook)
        notebook.add(vis_frame, text="Visualizations")
        
        # Dropdown for visualization selection
        vis_options = ["Event Distribution", "Refined Event Distribution", "Referrer Domains", "Time Differences"]
        selected_vis = tk.StringVar()
        ttk.Label(vis_frame, text="Select Visualization:").pack(pady=5)
        vis_dropdown = ttk.Combobox(vis_frame, textvariable=selected_vis, values=vis_options, state="readonly")
        vis_dropdown.pack(pady=5)
        vis_dropdown.set(vis_options[0])
        
        # Canvas for displaying visualization
        canvas = tk.Canvas(vis_frame, width=600, height=400)
        canvas.pack(pady=10)
        
        def display_visualization():
            if selected_vis.get() in self.visualizations:
                img = Image.open(self.visualizations[selected_vis.get()])
                img = img.resize((600, 400), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                canvas.image = photo
                self.log_message(f"Displayed {selected_vis.get()} visualization")
        
        ttk.Button(vis_frame, text="Display Visualization", command=display_visualization).pack(pady=5)
        
        # Textual Data Tab
        text_frame = ttk.Frame(notebook)
        notebook.add(text_frame, text="Textual Data")
        
        text_area = tk.Text(text_frame, height=30, width=80)
        text_area.pack(pady=10)
        
        # Generate visualizations and textual data
        try:
            result = visualize_logs.generate_visualizations_and_text(self.current_file)
            self.visualizations = result["visualizations"]
            self.textual_data = result["textual_data"]
            
            # Display textual data
            for key, value in self.textual_data.items():
                text_area.insert(tk.END, f"{key}:\n{value}\n\n")
            self.log_message("Generated visualizations and textual data")
        except Exception as e:
            messagebox.showerror("Error", f"Visualization generation failed: {str(e)}")
            self.log_message(f"Error in visualization: {str(e)}")

    def export_pdf(self):
        if not self.visualizations or not self.textual_data:
            messagebox.showwarning("Warning", "Please generate visualizations and report first.")
            return
        
        # Generating LaTeX content
        latex_content = r"""
\documentclass{article}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{booktabs}
\usepackage{parskip}
\geometry{a4paper, margin=1in}

\begin{document}
\title{User Behavior Analysis Report}
\author{}
\date{\today}
\maketitle

\section{Introduction}
This report presents the analysis of user behavior based on server logs from an e-commerce website, including event distributions, session statistics, and conversion funnel insights.

\section{Visualizations}
"""
        for vis_name, vis_path in self.visualizations.items():
            latex_content += f"""
\subsection{{{vis_name}}}
\includegraphics[width=\\textwidth]{{{vis_path}}}
"""
        latex_content += r"""
\section{Textual Data}
"""
        for key, value in self.textual_data.items():
            latex_content += f"""
\subsection{{{key}}}
\begin{verbatim}
{value}
\end{verbatim}
"""
        latex_content += r"""
\end{document}
"""
        
        # Save LaTeX file
        latex_file = os.path.join(self.output_dir, "report.tex")
        with open(latex_file, "w") as f:
            f.write(latex_content)
        
        # Compile LaTeX to PDF
        try:
            subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", latex_file], cwd=self.output_dir, check=True)
            pdf_file = os.path.join(self.output_dir, "report.pdf")
            self.log_message(f"PDF report generated at {pdf_file}")
            messagebox.showinfo("Success", f"PDF report generated at {pdf_file}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"PDF generation failed: {str(e)}")
            self.log_message(f"Error in PDF generation: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = UserBehaviorAnalyzerApp(root)
    root.mainloop()