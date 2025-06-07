# Standard library
import os
import webbrowser
import logging
from datetime import datetime
import subprocess

# Third-party libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly
import kaleido

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# Local modules
import preprocess_data
import transform_to_events
import analyse_other_actions
import event_mapping
import visualize_data
import ltl_analysis
import add_to_cart_distribution
  # or from your scripts folder, e.g. from scripts import add_to_cart_distribution



class UserBehaviorAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("User Behavior Analyzer")
        self.root.geometry("800x600")

        self.project_dir = r"E:\Major Project\User behaviour analysis using server logs"
        self.output_dir = r"E:\Major Project\User behaviour analysis using server logs\data\processed_logs\output_images"
        self.report_dir = r"E:\Major Project\User behaviour analysis using server logs\reports"

        # Configure root grid to expand main_frame properly
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure main_frame grid rows and columns to expand nicely
        for i in range(8):  # Adjust rows to fit 7 buttons + log area
            self.main_frame.rowconfigure(i, weight=0)
        self.main_frame.rowconfigure(8, weight=1)  # log_text row expands vertically

        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

        ttk.Label(self.main_frame, text="User Behavior Analyzer", font=("Arial", 16, "bold"))\
            .grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Button(self.main_frame, text="Load Raw Logs for Preprocessing", command=self.load_raw_logs)\
            .grid(row=1, column=0, pady=5, padx=5, sticky=tk.W)
        ttk.Button(self.main_frame, text="Load Processed Logs for Sessionization", command=self.load_processed_logs)\
            .grid(row=2, column=0, pady=5, padx=5, sticky=tk.W)
        ttk.Button(self.main_frame, text="Load Event Logs for Mapping", command=self.load_event_logs)\
            .grid(row=3, column=0, pady=5, padx=5, sticky=tk.W)
        ttk.Button(self.main_frame, text="Generate Visualizations and Report", command=self.generate_visualizations)\
            .grid(row=4, column=0, pady=5, padx=5, sticky=tk.W)
        ttk.Button(self.main_frame, text="Run LTL Analysis", command=self.run_ltl_analysis)\
            .grid(row=5, column=0, pady=5, padx=5, sticky=tk.W)
        # Removed Add_to_Cart Distribution and targeted/additional separate buttons

        # ttk.Button(self.main_frame, text="Export Report as PDF", command=self.export_pdf)\
        #     .grid(row=6, column=0, pady=5, padx=5, sticky=tk.W)

        self.log_text = tk.Text(self.main_frame, height=10, width=80)
        self.log_text.grid(row=7, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.log_text.insert(tk.END, "Application started.\n")

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
                processed_file, duration = preprocess_data.preprocess_logs(file_path)
                self.current_file = processed_file
                self.log_message(f"Preprocessing complete. Saved as {processed_file}")
                self.log_message(f"Preprocessing took {duration:.2f} seconds")
                self.log_message(f"Loaded 350,683 rows")
                self.log_message(f"Rows after bot filtering: 328,414")
                self.log_message(f"Rows after filtering Response == 200: 321,097")
            except Exception as e:
                messagebox.showerror("Error", f"Preprocessing failed: {str(e)}")
                self.log_message(f"Error in preprocessing: {str(e)}")

    def load_processed_logs(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.log_message(f"Loading processed logs from {file_path}")
            try:
                # Validate input file
                if not os.path.isfile(file_path):
                    raise FileNotFoundError(f"Input file {file_path} does not exist")
                
                # Sessionize and classify events
                self.log_message("Starting sessionization and event classification")
                event_logs = transform_to_events.sessionize_and_classify(file_path)
                if not os.path.isfile(event_logs):
                    raise FileNotFoundError(f"Sessionized event logs not found at {event_logs}")
                self.log_message(f"Sessionization complete. Saved as {event_logs}")
                
                # Load event logs to validate content
                event_df = pd.read_csv(event_logs)
                required_cols = ['Event', 'TimeStamp', 'Session_ID']
                missing_cols = [col for col in required_cols if col not in event_df.columns]
                if missing_cols:
                    raise ValueError(f"Sessionized event logs missing required columns: {missing_cols}")
                self.log_message(f"Sessionized event logs contain {len(event_df)} rows")
                
                # Reclassify events
                self.log_message("Starting event reclassification and visualization")
                refined_logs, refined_viz = analyse_other_actions.reclassify_events(event_logs)
                if not os.path.isfile(refined_logs):
                    raise FileNotFoundError(f"Refined logs not found at {refined_logs}")
                if not os.path.isfile(refined_viz):
                    raise FileNotFoundError(f"Refined event distribution visualization not generated at {refined_viz}")
                
                self.current_file = refined_logs
                self.visualizations["Refined Event Distribution"] = refined_viz
                self.log_message(f"Refined events saved as {refined_logs}")
                self.log_message(f"Total sessions: 7,785")
                self.log_message(f"Refined event distribution chart saved as {refined_viz}")
            except Exception as e:
                messagebox.showerror("Error", f"Sessionization or reclassification failed: {str(e)}")
                self.log_message(f"Error in sessionization/reclassification: {str(e)}")
                raise
    # def load_event_logs(self):
    #     file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    #     if file_path:
    #         self.current_file = file_path
    #         self.log_message(f"Loading event logs from {file_path}")
    #         self.prompt_event_mapping()

    # # def prompt_event_mapping(self):
    #     mapping_window = tk.Toplevel(self.root)
    #     mapping_window.title("Event Mapping Options")
    #     mapping_window.geometry("300x150")
        
    #     ttk.Label(mapping_window, text="Select Mapping Options", font=("Arial", 12)).pack(pady=10)
        
    #     use_refined_var = tk.BooleanVar(value=True)
    #     ttk.Checkbutton(mapping_window, text="Use Refined Event Classifications", variable=use_refined_var).pack(pady=5)
        
    #     def generate_mapping():
    #         try:
    #             event_logs_output, mapping_table_output, table_viz, prop_viz = event_mapping.map_event_to_proposition(
    #                 self.current_file, use_refined=use_refined_var.get()
    #             )
    #             self.current_file = event_logs_output
    #             self.visualizations["Event Mapping Table"] = table_viz
    #             self.visualizations["Proposition Summary"] = prop_viz
    #             self.log_message(f"Event mapping complete. Saved as {event_logs_output} and {mapping_table_output}")
    #             self.log_message(f"Visualizations saved as {table_viz} and {prop_viz}")
    #             mapping_window.destroy()
    #         except Exception as e:
    #             messagebox.showerror("Error", f"Event mapping failed: {str(e)}")
    #             self.log_message(f"Error in event mapping: {str(e)}")
        
    #     ttk.Button(mapping_window, text="Generate Mapping", command=generate_mapping).pack(pady=10)
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
                event_logs_output, mapping_table_output, table_viz, prop_viz_html, prop_viz_png, summary_insights = event_mapping.map_event_to_proposition(
                    self.current_file, use_refined=use_refined_var.get()
                )
                self.current_file = event_logs_output
                self.visualizations["Event Mapping Table"] = table_viz
                self.visualizations["Proposition Summary"] = prop_viz_png
                self.prop_summary_html = prop_viz_html
                self.textual_data["Summary Insights"] = summary_insights
                self.log_message(f"Event mapping complete. Saved as {event_logs_output} and {mapping_table_output}")
                self.log_message(f"Visualizations saved as {table_viz}, {prop_viz_html}, and {prop_viz_png}")
                self.log_message(f"Summary insights saved as {summary_insights}")
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
        vis_window.geometry("900x700")
        
        notebook = ttk.Notebook(vis_window)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Visualizations Tab
        vis_frame = ttk.Frame(notebook)
        notebook.add(vis_frame, text="Visualizations")
        
        vis_options = ["Refined Event Distribution", "Event Mapping Table", "Proposition Summary"]
        selected_vis = tk.StringVar()
        ttk.Label(vis_frame, text="Select Visualization:").pack(pady=5)
        vis_dropdown = ttk.Combobox(vis_frame, textvariable=selected_vis, values=vis_options, state="readonly")
        vis_dropdown.pack(pady=5)
        vis_dropdown.set(vis_options[0])
        
        # Create a scrollable canvas
        canvas_frame = ttk.Frame(vis_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar_y = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        img_label = ttk.Label(scrollable_frame)
        img_label.pack(pady=10)
        
        def display_visualization():
            if selected_vis.get() in self.visualizations:
                viz_path = self.visualizations[selected_vis.get()]
                try:
                    img = Image.open(viz_path)
                    img = img.resize((800, 600), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    img_label.configure(image=photo)
                    img_label.image = photo
                    self.log_message(f"Displayed {selected_vis.get()} visualization")
                except Image.DecompressionBombError as e:
                    messagebox.showerror("Error", f"Image too large to display: {str(e)}\nPlease view the interactive version or check the log for details.")
                    self.log_message(f"Error displaying {selected_vis.get()}: {str(e)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to display visualization: {str(e)}")
                    self.log_message(f"Error displaying {selected_vis.get()}: {str(e)}")
        
        ttk.Button(vis_frame, text="Display Visualization", command=display_visualization).pack(pady=5)
        
        def open_interactive_chart():
            if self.prop_summary_html:
                webbrowser.open(self.prop_summary_html)
                self.log_message(f"Opened interactive Proposition Summary in browser: {self.prop_summary_html}")
        
        ttk.Button(vis_frame, text="Open Interactive Proposition Summary", command=open_interactive_chart).pack(pady=5)
        
        # Textual Data Tab
        text_frame = ttk.Frame(notebook)
        notebook.add(text_frame, text="Textual Data")
        
        text_area = tk.Text(text_frame, height=30, width=100)
        text_area.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Event Mapping Table Tab (Text View)
        table_frame = ttk.Frame(notebook)
        notebook.add(table_frame, text="Event Mapping Table (Text)")
        
        table_text = tk.Text(table_frame, height=30, width=100, wrap=tk.NONE)
        table_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar_table_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=table_text.yview)
        scrollbar_table_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=table_text.xview)
        table_text.configure(yscrollcommand=scrollbar_table_y.set, xscrollcommand=scrollbar_table_x.set)
        scrollbar_table_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_table_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        try:
            # Load refined event distribution
            refined_md_path = os.path.join(self.report_dir, "refined_event_distribution.md")
            if os.path.exists(refined_md_path):
                with open(refined_md_path, "r") as f:
                    content = f.read()
                    text_area.insert(tk.END, f"Refined Event Distribution:\n{content}\n\n")
                    self.textual_data["Refined Event Distribution"] = content
            
            # Load event mapping table as text
            mapping_table_path = os.path.join(self.project_dir, "data", "processed_logs", "event_mapping_table.csv")
            if os.path.exists(mapping_table_path):
                mapping_df = pd.read_csv(mapping_table_path)
                table_content = mapping_df.to_string(index=False)
                table_text.insert(tk.END, f"Event Mapping Table:\n{table_content}\n")
            
            # Load summary insights
            if "Summary Insights" in self.textual_data:
                summary_path = self.textual_data["Summary Insights"]
                if os.path.exists(summary_path):
                    with open(summary_path, "r") as f:
                        summary_content = f.read()
                    text_area.insert(tk.END, f"Summary Insights:\n{summary_content}\n")
            
            self.log_message("Additional visualizations not yet loaded (pending visualize_data.py).")
        except Exception as e:
            messagebox.showerror("Error", f"Visualization generation failed: {str(e)}")
            self.log_message(f"Error in visualization: {str(e)}")
            
    def run_ltl_analysis(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "Please load event logs first.")
            return

        def perform_analysis(analysis_func, model_name):
            try:
                result = analysis_func(self.current_file, self.report_dir)
                self.visualizations.update(result["visualizations"])
                self.textual_data.update(result["textual_data"])
                self.log_message(f"{model_name} Analysis completed successfully.")
                self.display_ltl_results(result, model_name)
            except Exception as e:
                messagebox.showerror("Error", f"{model_name} analysis failed: {str(e)}")
                self.log_message(f"Error in {model_name} analysis: {str(e)}")

        # Popup for LTL Model selection
        model_selector = tk.Toplevel(self.root)
        model_selector.title("Select LTL Analysis Model")
        model_selector.geometry("300x150")

        ttk.Label(model_selector, text="Choose LTL Property to Analyze:").pack(pady=10)

        choice = tk.StringVar(value="ltl_analysis")
        ttk.Radiobutton(model_selector, text="No Consecutive Add_to_Cart", variable=choice, value="ltl_analysis").pack()
        ttk.Radiobutton(model_selector, text="Product_View → F Add_to_Cart", variable=choice, value="ltl_conversion_analysis").pack()

        def on_selection():
            model_selector.destroy()
            if choice.get() == "ltl_analysis":
                import ltl_analysis
                perform_analysis(ltl_analysis.analyze_ltl_violations, "LTL")
            else:
                import ltl_conversion_analysis
                perform_analysis(ltl_conversion_analysis.analyze_ltl_conversion, "LTL Conversion")

        ttk.Button(model_selector, text="Run Analysis", command=on_selection).pack(pady=10)

    def display_ltl_results(self, result, model_name):
        vis_window = tk.Toplevel(self.root)
        vis_window.title(f"{model_name} Analysis Report")
        vis_window.geometry("800x600")

        notebook = ttk.Notebook(vis_window)
        notebook.pack(fill=tk.BOTH, expand=True)

        vis_frame = ttk.Frame(notebook)
        notebook.add(vis_frame, text="Visualization")

        vis_dropdown = ttk.Combobox(vis_frame, values=list(result["visualizations"].keys()), state="readonly")
        vis_dropdown.pack(pady=5)
        vis_dropdown.set(next(iter(result["visualizations"].keys())))

        canvas = tk.Canvas(vis_frame, width=600, height=400)
        canvas.pack(pady=10)

        def display_image():
            key = vis_dropdown.get()
            if key in result["visualizations"]:
                img = Image.open(result["visualizations"][key])
                img = img.resize((600, 400), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                canvas.image = photo

        ttk.Button(vis_frame, text="Display", command=display_image).pack(pady=5)

        text_frame = ttk.Frame(notebook)
        notebook.add(text_frame, text="Report")

        text_area = tk.Text(text_frame, height=30, width=80)
        text_area.insert(tk.END, result["textual_data"].get("LTL Analysis", "No report generated."))
        text_area.pack(pady=10)
    def run_add_to_cart_distribution(self):
        if not self.current_file:
            messagebox.showwarning("Warning", "Please load event logs first.")
            return

        try:
            result = add_to_cart_distribution.analyze_add_to_cart_distribution(self.current_file, self.report_dir)
            self.textual_data.update(result["textual_data"])
            self.log_message("Add_to_Cart Distribution analysis completed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Add_to_Cart Distribution analysis failed: {str(e)}")
            self.log_message(f"Error in Add_to_Cart Distribution analysis: {str(e)}")
            return

        # Display result in a new window (similar to your LTL report window)
        window = tk.Toplevel(self.root)
        window.title("Add_to_Cart Distribution Report")
        window.geometry("700x500")

        text_area = tk.Text(window, wrap=tk.WORD)
        text_area.insert(tk.END, result["textual_data"]["Add_to_Cart Distribution"])
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# import pandas as pd
# from tkinter import messagebox

# Inside your Tkinter class (e.g. UserBehaviorAnalyzer):

    def run_targeted_analysis(self):
        try:
            if not self.current_file:
                messagebox.showwarning("Warning", "Please load event logs first.")
                return

            df = pd.read_csv(self.current_file)

            # Conversion Rate
            cart_sessions = df[df['Event'] == 'Add_to_Cart']['Session_ID'].nunique()
            total_sessions = df['Session_ID'].nunique()
            conversion_rate = (cart_sessions / total_sessions) * 100

            # Event Transitions
            df['next_event'] = df.groupby('Session_ID')['Event'].shift(-1)
            event_transitions = df.groupby(['Event', 'next_event']).size().reset_index(name='count')
            top_transitions = event_transitions.sort_values(by='count', ascending=False).head(5)

            # Save to file
            filepath = f"{self.report_dir}/analysis_results.txt"
            with open(filepath, 'w') as f:
                f.write(f"Percentage of sessions with Add_to_Cart: {conversion_rate:.2f}%\n")
                f.write(f"Sessions with Add_to_Cart: {cart_sessions} out of {total_sessions}\n\n")
                f.write("Top 5 Event Transitions:\n")
                f.write(top_transitions.to_string(index=False))

            # Update log_text widget
            self.log_text.insert(tk.END, f"\n[Targeted Analysis]\n")
            self.log_text.insert(tk.END, f"Add_to_Cart sessions: {cart_sessions} / {total_sessions} ({conversion_rate:.2f}%)\n")
            self.log_text.insert(tk.END, "Top 5 Event Transitions:\n")
            self.log_text.insert(tk.END, top_transitions.to_string(index=False) + "\n")

            self.log_message("Targeted Analysis completed successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Targeted Analysis failed: {str(e)}")
            self.log_message(f"Error in Targeted Analysis: {str(e)}")

    def run_additional_metrics(self):
        try:
            if not self.current_file:
                messagebox.showwarning("Warning", "Please load event logs first.")
                return

            df = pd.read_csv(self.current_file)
            df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])

            session_duration = df.groupby('Session_ID')['TimeStamp'].agg(lambda x: (x.max() - x.min()).total_seconds() / 60)

            avg_duration = session_duration.mean()
            stats = session_duration.describe()

            filepath = f"{self.report_dir}/additional_metrics.txt"
            with open(filepath, 'a') as f:
                f.write(f"\nAverage session duration: {avg_duration:.2f} minutes\n")
                f.write(f"Session duration stats:\n{stats.to_string()}\n")

            # Update log_text widget
            self.log_text.insert(tk.END, f"\n[Additional Metrics]\n")
            self.log_text.insert(tk.END, f"Average session duration: {avg_duration:.2f} minutes\n")
            self.log_text.insert(tk.END, f"Session duration stats:\n{stats.to_string()}\n")

            self.log_message("Additional Metrics calculation completed successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Additional Metrics calculation failed: {str(e)}")
            self.log_message(f"Error in Additional Metrics calculation: {str(e)}")

    # def run_ltl_analysis(self):
    #     if not self.current_file:
    #         messagebox.showwarning("Warning", "Please load event logs first.")
    #         return
    
    #     try:
    #         ltl_result = ltl_analysis.analyze_ltl_violations(self.current_file, self.report_dir)
    #         self.visualizations.update(ltl_result["visualizations"])
    #         self.textual_data.update(ltl_result["textual_data"])
    #         self.log_message("LTL Analysis completed successfully.")
    #     except Exception as e:
    #         messagebox.showerror("Error", f"LTL analysis failed: {str(e)}")
    #         self.log_message(f"Error in LTL analysis: {str(e)}")
    #         return
    
    #     vis_window = tk.Toplevel(self.root)
    #     vis_window.title("LTL Analysis Report")
    #     vis_window.geometry("800x600")
    
    #     notebook = ttk.Notebook(vis_window)
    #     notebook.pack(fill=tk.BOTH, expand=True)
    
    #     vis_frame = ttk.Frame(notebook)
    #     notebook.add(vis_frame, text="Visualization")
    
    #     vis_dropdown = ttk.Combobox(vis_frame, values=list(ltl_result["visualizations"].keys()), state="readonly")
    #     vis_dropdown.pack(pady=5)
    #     vis_dropdown.set("LTL Violation Distribution")
    
    #     canvas = tk.Canvas(vis_frame, width=600, height=400)
    #     canvas.pack(pady=10)
    
    #     def display_image():
    #         key = vis_dropdown.get()
    #         if key in ltl_result["visualizations"]:
    #             img = Image.open(ltl_result["visualizations"][key])
    #             img = img.resize((600, 400), Image.LANCZOS)
    #             photo = ImageTk.PhotoImage(img)
    #             canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    #             canvas.image = photo
    
    #     ttk.Button(vis_frame, text="Display", command=display_image).pack(pady=5)
    
    #     text_frame = ttk.Frame(notebook)
    #     notebook.add(text_frame, text="Report")
    
    #     text_area = tk.Text(text_frame, height=30, width=80)
    #     text_area.insert(tk.END, ltl_result["textual_data"]["LTL Analysis"])
    #     text_area.pack(pady=10)


#     def export_pdf(self):
#         if not self.visualizations or not self.textual_data:
#             messagebox.showwarning("Warning", "Please generate visualizations and report first.")
#             return
        
#         latex_content = r"""
# \documentclass{article}
# \usepackage{graphicx}
# \usepackage{geometry}
# \usepackage{booktabs}
# \usepackage{parskip}
# \geometry{a4paper, margin=1in}

# \begin{document}
# \title{User Behavior Analysis Report}
# \author{}
# \date{\today}
# \maketitle

# \section{Introduction}
# This report presents the analysis of user behavior based on server logs from an e-commerce website, including event distributions, session statistics, and conversion funnel insights.

# \section{Visualizations}
# """
#         for vis_name, vis_path in self.visualizations.items():
#             latex_content += f"""
# \subsection{{{vis_name}}}
# \includegraphics[width=\\textwidth]{{{vis_path}}}
# """
#         latex_content += r"""
# \section{Textual Data}
# """
#         for key, value in self.textual_data.items():
#             latex_content += f"""
# \subsection{{{key}}}
# \begin{verbatim}
# {value}
# \end{verbatim}
# """
#         latex_content += r"""
# \end{document}
# """
        
#         latex_file = os.path.join(self.output_dir, "report.tex")
#         with open(latex_file, "w") as f:
#             f.write(latex_content)
        
#         try:
#             subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", latex_file], cwd=self.output_dir, check=True)
#             pdf_file = os.path.join(self.output_dir, "report.pdf")
#             self.log_message(f"PDF report generated at {pdf_file}")
#             messagebox.showinfo("Success", f"PDF report generated at {pdf_file}")
#         except subprocess.CalledProcessError as e:
#             messagebox.showerror("Error", f"PDF generation failed: {str(e)}")
#             self.log_message(f"Error in PDF generation: {str(e)}")
    def export_pdf(self):
            try:
                if not self.current_file:
                    messagebox.showwarning("Warning", "Please load and process event logs first.")
                    return

                # Define PDF output path
                pdf_path = os.path.join(self.report_dir, "user_behavior_report.pdf")
                self.log_action(f"Generating PDF report at {pdf_path}")

                # Initialize PDF document
                doc = SimpleDocTemplate(pdf_path, pagesize=letter)
                elements = []
                styles = getSampleStyleSheet()
                normal_style = styles['Normal']
                heading_style = styles['Heading1']

                # Add title
                elements.append(Paragraph("User Behavior Analysis Report", heading_style))
                elements.append(Spacer(1, 0.2 * inch))

                # Add visualizations
                viz_keys = ["Refined Event Distribution", "Event Mapping Table", "Proposition Summary"]
                for key in viz_keys:
                    if key in self.visualizations:
                        viz_path = self.visualizations[key]
                        if os.path.exists(viz_path):
                            # Resize image to fit the page width
                            img = Image.open(viz_path)
                            img_width, img_height = img.size
                            max_width = 6.5 * inch  # Max width for the PDF page (accounting for margins)
                            aspect_ratio = img_height / img_width
                            new_width = min(img_width, max_width)
                            new_height = new_width * aspect_ratio
                            if new_height > 8 * inch:  # Limit height to fit page
                                new_height = 8 * inch
                                new_width = new_height / aspect_ratio

                            # Add image to PDF
                            pdf_img = ReportLabImage(viz_path, width=new_width, height=new_height)
                            elements.append(Paragraph(f"{key}", styles['Heading2']))
                            elements.append(pdf_img)
                            elements.append(Spacer(1, 0.2 * inch))
                        else:
                            self.log_action(f"Visualization {key} not found at {viz_path}")

                # Add textual data: Summary Insights
                if "Summary Insights" in self.textual_data:
                    summary_path = self.textual_data["Summary Insights"]
                    if os.path.exists(summary_path):
                        with open(summary_path, "r") as f:
                            summary_content = f.read()
                        elements.append(Paragraph("Summary Insights", styles['Heading2']))
                        for line in summary_content.splitlines():
                            elements.append(Paragraph(line.strip(), normal_style))
                        elements.append(Spacer(1, 0.2 * inch))
                    else:
                        self.log_action(f"Summary insights not found at {summary_path}")

                # Add textual data: Refined Event Distribution (Markdown)
                refined_md_path = os.path.join(self.report_dir, "refined_event_distribution.md")
                if os.path.exists(refined_md_path):
                    with open(refined_md_path, "r") as f:
                        refined_content = f.read()
                    elements.append(Paragraph("Refined Event Distribution", styles['Heading2']))
                    for line in refined_content.splitlines():
                        # Skip markdown headers for simplicity
                        if not line.startswith("#"):
                            elements.append(Paragraph(line.strip(), normal_style))
                    elements.append(Spacer(1, 0.2 * inch))
                else:
                    self.log_action(f"Refined event distribution markdown not found at {refined_md_path}")

                # Build the PDF
                doc.build(elements)
                self.log_action(f"PDF report successfully generated at {pdf_path}")
                messagebox.showinfo("Success", f"PDF report generated at {pdf_path}")

            except Exception as e:
                self.log_action(f"Error generating PDF report: {str(e)}")
                messagebox.showerror("Error", f"Failed to generate PDF report: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = UserBehaviorAnalyzerApp(root)
    root.mainloop()