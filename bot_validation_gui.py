"""
Bot Validation GUI - Professional interface for testing bots
Enter bot number, add agent inputs, get separate transcript files
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Pause
import uuid
from datetime import datetime
import json
import time
import threading
import requests

# Load credentials
load_dotenv()
ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE = os.getenv('TWILIO_PHONE_NUMBER')

class BotValidationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Bot Validation System - Ashley Furniture")
        self.root.geometry("1400x950")
        
        # Colors
        self.colors = {
            'primary': '#2E86AB',
            'success': '#06D6A0',
            'warning': '#F77F00',
            'danger': '#EF476F',
            'bg_main': '#F8F9FA',
            'bg_card': '#FFFFFF',
            'bot': '#7B1FA2'
        }
        
        self.root.configure(bg=self.colors['bg_main'])

        # Track current call
        self.current_call_sid = None
        self.call_in_progress = False

        self.create_widgets()
    
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg=self.colors['bot'], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, 
                text="🤖 Bot Validation System",
                font=('Segoe UI', 20, 'bold'),
                bg=self.colors['bot'],
                fg='white').pack(pady=20)
        
        # Main content
        main_frame = tk.Frame(self.root, bg=self.colors['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Input (with scrollbar)
        left_container = tk.Frame(main_frame, bg=self.colors['bg_main'])
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Create canvas and scrollbar
        canvas = tk.Canvas(left_container, bg=self.colors['bg_main'], highlightthickness=0)
        scrollbar = tk.Scrollbar(left_container, orient="vertical", command=canvas.yview)
        left_panel = tk.Frame(canvas, bg=self.colors['bg_main'])

        # Configure scrollbar
        left_panel.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=left_panel, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Bot Number Card
        number_card = tk.Frame(left_panel, bg=self.colors['bg_card'], 
                              relief='solid', borderwidth=1)
        number_card.pack(fill=tk.X, pady=10)
        
        number_header = tk.Frame(number_card, bg=self.colors['success'], height=40)
        number_header.pack(fill=tk.X)
        number_header.pack_propagate(False)
        
        tk.Label(number_header, text="📞 Bot Phone Number",
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['success'],
                fg='white').pack(pady=8, padx=10, anchor='w')
        
        number_content = tk.Frame(number_card, bg=self.colors['bg_card'])
        number_content.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(number_content,
                text="Enter the bot's phone number (with country code):",
                font=('Segoe UI', 9),
                bg=self.colors['bg_card'],
                fg='gray').pack(anchor='w', pady=(0, 5))
        
        self.phone_entry = tk.Entry(number_content, width=40, font=('Segoe UI', 14),
                                   bg='#FAFAFA', relief='solid', borderwidth=1)
        self.phone_entry.pack(pady=5, ipady=10, fill=tk.X)
        self.phone_entry.insert(0, "+919898173087")
        
        # Test Name Card
        name_card = tk.Frame(left_panel, bg=self.colors['bg_card'],
                            relief='solid', borderwidth=1)
        name_card.pack(fill=tk.X, pady=10)
        
        name_header = tk.Frame(name_card, bg=self.colors['primary'], height=40)
        name_header.pack(fill=tk.X)
        name_header.pack_propagate(False)
        
        tk.Label(name_header, text="📝 Test Name/Description",
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['primary'],
                fg='white').pack(pady=8, padx=10, anchor='w')
        
        name_content = tk.Frame(name_card, bg=self.colors['bg_card'])
        name_content.pack(fill=tk.X, padx=15, pady=15)
        
        self.test_name_entry = tk.Entry(name_content, width=40, font=('Segoe UI', 12),
                                        bg='#FAFAFA', relief='solid', borderwidth=1)
        self.test_name_entry.pack(pady=5, ipady=8, fill=tk.X)
        self.test_name_entry.insert(0, "Ashley Furniture Bot Test")
        
        # DTMF Input Card
        dtmf_card = tk.Frame(left_panel, bg=self.colors['bg_card'],
                            relief='solid', borderwidth=1)
        dtmf_card.pack(fill=tk.X, pady=10)

        dtmf_header = tk.Frame(dtmf_card, bg='#7B1FA2', height=40)
        dtmf_header.pack(fill=tk.X)
        dtmf_header.pack_propagate(False)

        tk.Label(dtmf_header, text="🔢 DTMF Input Configuration",
                font=('Segoe UI', 12, 'bold'),
                bg='#7B1FA2',
                fg='white').pack(pady=8, padx=10, anchor='w')

        # Create scrollable container for DTMF content
        dtmf_scroll_container = tk.Frame(dtmf_card, bg=self.colors['bg_card'])
        dtmf_scroll_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas and scrollbar for DTMF inputs
        dtmf_canvas = tk.Canvas(dtmf_scroll_container, bg=self.colors['bg_card'],
                                highlightthickness=0, height=300)
        dtmf_scrollbar = tk.Scrollbar(dtmf_scroll_container, orient="vertical",
                                      command=dtmf_canvas.yview)
        dtmf_content = tk.Frame(dtmf_canvas, bg=self.colors['bg_card'])

        # Configure scrollbar
        dtmf_content.bind(
            "<Configure>",
            lambda e: dtmf_canvas.configure(scrollregion=dtmf_canvas.bbox("all"))
        )

        dtmf_canvas.create_window((0, 0), window=dtmf_content, anchor="nw")
        dtmf_canvas.configure(yscrollcommand=dtmf_scrollbar.set)

        # Pack canvas and scrollbar
        dtmf_canvas.pack(side="left", fill="both", expand=True)
        dtmf_scrollbar.pack(side="right", fill="y")

        # Enable mousewheel scrolling for DTMF panel
        def _on_dtmf_mousewheel(event):
            dtmf_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        dtmf_canvas.bind("<Enter>", lambda e: dtmf_canvas.bind_all("<MouseWheel>", _on_dtmf_mousewheel))
        dtmf_canvas.bind("<Leave>", lambda e: dtmf_canvas.unbind_all("<MouseWheel>"))

        # Add padding frame inside content
        dtmf_inner = tk.Frame(dtmf_content, bg=self.colors['bg_card'])
        dtmf_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Use dtmf_inner instead of dtmf_content for all child widgets below
        dtmf_content = dtmf_inner

        # DTMF Configuration Info
        tk.Label(dtmf_content,
                text="Sequential DTMF Input - Menu option THEN Store Phone Number:",
                font=('Segoe UI', 10, 'bold'),
                bg=self.colors['bg_card'],
                fg='#7B1FA2').pack(anchor='w', pady=(0, 10))

        # Step 1: Single Digit Input
        single_frame = tk.Frame(dtmf_content, bg=self.colors['bg_card'])
        single_frame.pack(fill=tk.X, pady=10)

        tk.Label(single_frame,
                text="Step 1: Single DTMF Digit (e.g., menu option):",
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['bg_card'],
                fg='#7B1FA2').pack(anchor='w', pady=(0, 5))

        single_input_frame = tk.Frame(single_frame, bg=self.colors['bg_card'])
        single_input_frame.pack(fill=tk.X)

        self.dtmf_single_entry = tk.Entry(single_input_frame, width=10, font=('Segoe UI', 14),
                                         bg='#F3E5F5', relief='solid', borderwidth=2)
        self.dtmf_single_entry.pack(side=tk.LEFT, ipady=8)
        self.dtmf_single_entry.insert(0, "2")

        tk.Label(single_input_frame,
                text="  (Example: 2 for support option)",
                font=('Segoe UI', 8),
                bg=self.colors['bg_card'],
                fg='gray').pack(side=tk.LEFT, padx=5)

        # Step 2: Store Phone Number (10-Digit Input)
        ten_digit_frame = tk.Frame(dtmf_content, bg=self.colors['bg_card'])
        ten_digit_frame.pack(fill=tk.X, pady=10)

        tk.Label(ten_digit_frame,
                text="Step 2: Store Phone Number (10-digit DTMF):",
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['bg_card'],
                fg='#7B1FA2').pack(anchor='w', pady=(0, 5))

        ten_digit_input_frame = tk.Frame(ten_digit_frame, bg=self.colors['bg_card'])
        ten_digit_input_frame.pack(fill=tk.X)

        self.dtmf_tendigit_entry = tk.Entry(ten_digit_input_frame, width=25, font=('Segoe UI', 14),
                                            bg='#F3E5F5', relief='solid', borderwidth=2)
        self.dtmf_tendigit_entry.pack(side=tk.LEFT, ipady=8)
        self.dtmf_tendigit_entry.insert(0, "5551234567")

        tk.Label(ten_digit_input_frame,
                text="  (Store phone number - exactly 10 digits)",
                font=('Segoe UI', 8),
                bg=self.colors['bg_card'],
                fg='gray').pack(side=tk.LEFT, padx=5)

        # Step 3: Additional DTMF Input 1
        step3_frame = tk.Frame(dtmf_content, bg=self.colors['bg_card'])
        step3_frame.pack(fill=tk.X, pady=10)

        tk.Label(step3_frame,
                text="Step 3: Additional DTMF Input (single digit):",
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['bg_card'],
                fg='#7B1FA2').pack(anchor='w', pady=(0, 5))

        step3_input_frame = tk.Frame(step3_frame, bg=self.colors['bg_card'])
        step3_input_frame.pack(fill=tk.X)

        self.dtmf_step3_entry = tk.Entry(step3_input_frame, width=10, font=('Segoe UI', 14),
                                         bg='#F3E5F5', relief='solid', borderwidth=2)
        self.dtmf_step3_entry.pack(side=tk.LEFT, ipady=8)
        self.dtmf_step3_entry.insert(0, "1")

        tk.Label(step3_input_frame,
                text="  (Example: 1 for confirmation)",
                font=('Segoe UI', 8),
                bg=self.colors['bg_card'],
                fg='gray').pack(side=tk.LEFT, padx=5)

        # Step 4: Additional DTMF Input 2
        step4_frame = tk.Frame(dtmf_content, bg=self.colors['bg_card'])
        step4_frame.pack(fill=tk.X, pady=10)

        tk.Label(step4_frame,
                text="Step 4: Additional DTMF Input (single digit):",
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['bg_card'],
                fg='#7B1FA2').pack(anchor='w', pady=(0, 5))

        step4_input_frame = tk.Frame(step4_frame, bg=self.colors['bg_card'])
        step4_input_frame.pack(fill=tk.X)

        self.dtmf_step4_entry = tk.Entry(step4_input_frame, width=10, font=('Segoe UI', 14),
                                         bg='#F3E5F5', relief='solid', borderwidth=2)
        self.dtmf_step4_entry.pack(side=tk.LEFT, ipady=8)
        self.dtmf_step4_entry.insert(0, "1")

        tk.Label(step4_input_frame,
                text="  (Example: 1 for yes/no)",
                font=('Segoe UI', 8),
                bg=self.colors['bg_card'],
                fg='gray').pack(side=tk.LEFT, padx=5)

        # Delay Configuration
        delay_frame = tk.Frame(dtmf_content, bg=self.colors['bg_card'])
        delay_frame.pack(fill=tk.X, pady=15)

        tk.Label(delay_frame,
                text="Timing Configuration:",
                font=('Segoe UI', 10, 'bold'),
                bg=self.colors['bg_card'],
                fg='#7B1FA2').pack(anchor='w', pady=(0, 10))

        # Delay before Step 1
        delay1_frame = tk.Frame(delay_frame, bg=self.colors['bg_card'])
        delay1_frame.pack(fill=tk.X, pady=5)

        tk.Label(delay1_frame,
                text="Delay before Step 1 (single digit):",
                font=('Segoe UI', 9),
                bg=self.colors['bg_card'],
                fg='gray').pack(anchor='w', pady=(0, 3))

        delay1_input_frame = tk.Frame(delay1_frame, bg=self.colors['bg_card'])
        delay1_input_frame.pack(anchor='w')

        self.dtmf_delay_entry = tk.Entry(delay1_input_frame, width=8, font=('Segoe UI', 12),
                                        bg='#F3E5F5', relief='solid', borderwidth=2)
        self.dtmf_delay_entry.pack(side=tk.LEFT, ipady=6)
        self.dtmf_delay_entry.insert(0, "10000")

        tk.Label(delay1_input_frame,
                text="ms (wait before sending single digit)",
                font=('Segoe UI', 9),
                bg=self.colors['bg_card'],
                fg='gray').pack(side=tk.LEFT, padx=(8, 0))

        # Delay before Step 2
        delay2_frame = tk.Frame(delay_frame, bg=self.colors['bg_card'])
        delay2_frame.pack(fill=tk.X, pady=5)

        tk.Label(delay2_frame,
                text="Delay before Step 2 (Store Phone Number):",
                font=('Segoe UI', 9),
                bg=self.colors['bg_card'],
                fg='gray').pack(anchor='w', pady=(0, 3))

        delay2_input_frame = tk.Frame(delay2_frame, bg=self.colors['bg_card'])
        delay2_input_frame.pack(anchor='w')

        self.second_delay_entry = tk.Entry(delay2_input_frame, width=8, font=('Segoe UI', 12),
                                          bg='#F3E5F5', relief='solid', borderwidth=2)
        self.second_delay_entry.pack(side=tk.LEFT, ipady=6)
        self.second_delay_entry.insert(0, "10000")

        tk.Label(delay2_input_frame,
                text="ms (wait after menu option, before store phone)",
                font=('Segoe UI', 9),
                bg=self.colors['bg_card'],
                fg='gray').pack(side=tk.LEFT, padx=(8, 0))

        # NOTE: Digit delay removed - phone number digits are sent quickly/simultaneously
        # Delays are only BETWEEN steps (to hear complete IVR prompts), NOT within the same input

        # Delay before Step 3
        delay3_frame = tk.Frame(delay_frame, bg=self.colors['bg_card'])
        delay3_frame.pack(fill=tk.X, pady=5)

        tk.Label(delay3_frame,
                text="Delay before Step 3 (additional input 1):",
                font=('Segoe UI', 9),
                bg=self.colors['bg_card'],
                fg='gray').pack(anchor='w', pady=(0, 3))

        delay3_input_frame = tk.Frame(delay3_frame, bg=self.colors['bg_card'])
        delay3_input_frame.pack(anchor='w')

        self.third_delay_entry = tk.Entry(delay3_input_frame, width=8, font=('Segoe UI', 12),
                                          bg='#F3E5F5', relief='solid', borderwidth=2)
        self.third_delay_entry.pack(side=tk.LEFT, ipady=6)
        self.third_delay_entry.insert(0, "10000")

        tk.Label(delay3_input_frame,
                text="ms (wait after Step 2, before Step 3)",
                font=('Segoe UI', 9),
                bg=self.colors['bg_card'],
                fg='gray').pack(side=tk.LEFT, padx=(8, 0))

        # Delay before Step 4
        delay4_frame = tk.Frame(delay_frame, bg=self.colors['bg_card'])
        delay4_frame.pack(fill=tk.X, pady=5)

        tk.Label(delay4_frame,
                text="Delay before Step 4 (additional input 2):",
                font=('Segoe UI', 9),
                bg=self.colors['bg_card'],
                fg='gray').pack(anchor='w', pady=(0, 3))

        delay4_input_frame = tk.Frame(delay4_frame, bg=self.colors['bg_card'])
        delay4_input_frame.pack(anchor='w')

        self.fourth_delay_entry = tk.Entry(delay4_input_frame, width=8, font=('Segoe UI', 12),
                                           bg='#F3E5F5', relief='solid', borderwidth=2)
        self.fourth_delay_entry.pack(side=tk.LEFT, ipady=6)
        self.fourth_delay_entry.insert(0, "10000")

        tk.Label(delay4_input_frame,
                text="ms (wait after Step 3, before Step 4)",
                font=('Segoe UI', 9),
                bg=self.colors['bg_card'],
                fg='gray').pack(side=tk.LEFT, padx=(8, 0))

        # Agent Inputs Card
        inputs_card = tk.Frame(left_panel, bg=self.colors['bg_card'],
                              relief='solid', borderwidth=1)
        inputs_card.pack(fill=tk.BOTH, expand=True, pady=10)

        inputs_header = tk.Frame(inputs_card, bg=self.colors['warning'], height=40)
        inputs_header.pack(fill=tk.X)
        inputs_header.pack_propagate(False)

        tk.Label(inputs_header, text="🎯 Custom Agent Instructions (Editable Text Box)",
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['warning'],
                fg='white').pack(pady=8, padx=10, anchor='w')

        inputs_content = tk.Frame(inputs_card, bg=self.colors['bg_card'])
        inputs_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        instruction_label = tk.Label(inputs_content,
                text="✏️ ENTER YOUR CUSTOM INSTRUCTIONS BELOW (Delete template and type your own):",
                font=('Segoe UI', 10, 'bold'),
                bg=self.colors['bg_card'],
                fg='#D84315')
        instruction_label.pack(anchor='w', pady=(0, 8))

        tk.Label(inputs_content,
                text="What should the bot do? Expected responses? Test scenarios? Validation points?",
                font=('Segoe UI', 9),
                bg=self.colors['bg_card'],
                fg='gray').pack(anchor='w', pady=(0, 5))

        self.inputs_text = scrolledtext.ScrolledText(inputs_content,
                                                     width=50, height=18,
                                                     font=('Segoe UI', 10),
                                                     bg='#FAFAFA',
                                                     relief='solid',
                                                     borderwidth=1,
                                                     wrap=tk.WORD)
        self.inputs_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Default test inputs
        default_inputs = """👉 DELETE THIS TEMPLATE AND ENTER YOUR CUSTOM INSTRUCTIONS 👈

Example Test Scenario: Ashley Furniture Customer Service Bot

What I Want to Test:
1. Bot greeting quality
2. Menu options clarity
3. Response to option 2 (DTMF '2' will be sent)
4. Voice quality and tone
5. Professional customer service experience

Expected Bot Flow:
- Bot answers and greets with company name
- Bot provides menu options (1=sales, 2=support, etc.)
- Bot waits for input
- System sends DTMF '2' automatically after 5 seconds
- Bot responds to option 2 selection
- Bot provides support options

Validation Points:
✓ Clear greeting message
✓ Easy to understand menu
✓ Proper response to DTMF input
✓ Professional voice and tone
✓ No awkward pauses or errors

Notes:
- Expected call duration: 30-60 seconds
- DTMF '2' will be sent after 5 second delay
- Recording will stop when bot is silent for 3 seconds

👉 REPLACE THIS WITH YOUR OWN TEST SCENARIO! 👈
"""
        self.inputs_text.insert('1.0', default_inputs)

        # Right panel - Output & Controls
        right_panel = tk.Frame(main_frame, bg=self.colors['bg_main'], width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        right_panel.pack_propagate(False)

        # Call Button
        self.call_btn = tk.Button(right_panel,
                            text="📞 Start Bot Validation Test",
                            font=('Segoe UI', 14, 'bold'),
                            bg=self.colors['bot'],
                            fg='white',
                            activebackground='#6A1B9A',
                            activeforeground='white',
                            cursor='hand2',
                            relief='flat',
                            command=self.start_bot_test)
        self.call_btn.pack(pady=15, ipady=15, fill=tk.X)

        # Cancel Button (initially hidden)
        self.cancel_btn = tk.Button(right_panel,
                                    text="🛑 Cancel Call / Emergency Stop",
                                    font=('Segoe UI', 12, 'bold'),
                                    bg=self.colors['danger'],
                                    fg='white',
                                    activebackground='#D32F2F',
                                    activeforeground='white',
                                    cursor='hand2',
                                    relief='flat',
                                    command=self.cancel_call,
                                    state='disabled')
        self.cancel_btn.pack(pady=(0, 15), ipady=10, fill=tk.X)

        # Status Card
        status_card = tk.Frame(right_panel, bg=self.colors['bg_card'],
                              relief='solid', borderwidth=1)
        status_card.pack(fill=tk.BOTH, expand=True, pady=10)

        status_header = tk.Frame(status_card, bg=self.colors['primary'], height=40)
        status_header.pack(fill=tk.X)
        status_header.pack_propagate(False)

        tk.Label(status_header, text="📊 Test Status",
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['primary'],
                fg='white').pack(pady=8, padx=10, anchor='w')

        status_content = tk.Frame(status_card, bg=self.colors['bg_card'])
        status_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.status_text = scrolledtext.ScrolledText(status_content,
                                                     width=45, height=30,
                                                     font=('Consolas', 9),
                                                     bg='#F8F9FA',
                                                     relief='solid',
                                                     borderwidth=1,
                                                     wrap=tk.WORD,
                                                     state='disabled')
        self.status_text.pack(fill=tk.BOTH, expand=True)

        self.log("🤖 Bot Validation System Ready!")
        self.log("📝 Enter bot number and test details, then click 'Start Bot Validation Test'")
        self.log("")
        self.log("⚙️  Configuration:")
        self.log("   - Initial pause: 10 seconds (let IVR start greeting)")
        self.log("   - DTMF Mode: SEQUENTIAL (4-step flow)")
        self.log("   - Step 1: Menu option (single digit)")
        self.log("   - Step 2: Store Phone Number (10 digits)")
        self.log("   - Step 3: Additional input (single digit)")
        self.log("   - Step 4: Additional input (single digit)")
        self.log("   - All delays: 10 seconds (10000ms) - ensures complete IVR prompts")
        self.log("")
        self.log("🎯 Natural Conversation Flow (Question → Answer):")
        self.log("   1. IVR asks COMPLETE question (recorded)")
        self.log("   2. System WAITS for delay duration (10s default)")
        self.log("   3. System sends DTMF response")
        self.log("   4. IVR responds (recorded)")
        self.log("   → Repeat for all 4 steps")
        self.log("")
        self.log("🎙️  Recording:")
        self.log("   - ENTIRE conversation captured (3-5+ minutes)")
        self.log("   - Both IVR prompts AND your responses recorded")
        self.log("   - Sequential transcript with timestamps")
        self.log("   - Multi-language support (English, Spanish, etc.)")
        self.log("")
        self.log("💡 Delays ensure IVR prompts are FULLY captured before responding")
        self.log("💡 All steps are optional - leave blank to skip")
        self.log("")
        self.log("🛑 Emergency Stop: Click 'Cancel Call' button during test")

    def log(self, message):
        """Add message to status log"""
        self.status_text.configure(state='normal')
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.configure(state='disabled')
        self.root.update_idletasks()

    def cancel_call(self):
        """Cancel the current call immediately"""
        if not self.current_call_sid:
            messagebox.showwarning("No Active Call", "There is no call in progress to cancel.")
            return

        confirm = messagebox.askyesno(
            "Cancel Call?",
            f"Are you sure you want to end the current call?\n\n"
            f"Call SID: {self.current_call_sid}\n\n"
            f"This will immediately terminate the call."
        )

        if not confirm:
            return

        try:
            self.log("")
            self.log("=" * 60)
            self.log("🛑 CANCELING CALL...")
            self.log("=" * 60)

            client = Client(ACCOUNT_SID, AUTH_TOKEN)

            # Update call status to 'completed' to end it
            call = client.calls(self.current_call_sid).update(status='completed')

            self.log(f"✅ Call canceled successfully!")
            self.log(f"📞 Call SID: {self.current_call_sid}")
            self.log(f"📊 Final Status: {call.status}")
            self.log("")
            self.log("=" * 60)

            # Reset state
            self.current_call_sid = None
            self.call_in_progress = False
            self.cancel_btn.configure(state='disabled')
            self.call_btn.configure(state='normal')

            messagebox.showinfo("Call Canceled", "Call has been terminated successfully.")

        except Exception as e:
            self.log(f"❌ Error canceling call: {str(e)}")
            self.log("")
            messagebox.showerror("Cancel Failed", f"Failed to cancel call:\n{str(e)}")

    def create_bot_twiml(self, dtmf_single="", dtmf_tendigit="", dtmf_step3="", dtmf_step4="",
                        delay1=20, delay2=30, delay3=40, delay4=50):
        """Create TwiML for bot validation with sequential DTMF input

        Note: This uses call-level recording (record=True in call creation) which captures
        the entire audio from both sides. The TwiML just manages the DTMF flow and keeps
        the call alive so the recording captures everything.
        """
        response = VoiceResponse()

        # Initial pause to let IVR start and deliver its COMPLETE greeting/menu
        # Recording captures: "Welcome to Ashley Furniture. For English press 1..."
        # This ensures the ENTIRE prompt is recorded before we send any input
        # 10 seconds ensures even long bilingual menus are fully captured
        response.pause(length=10)

        # Step 1: Listen to IVR's COMPLETE first prompt, THEN send single digit DTMF
        # Flow: IVR asks complete question → We wait (delay1) → We respond → Wait for IVR acknowledgment
        # Example:
        #   IVR: "For billing press 1, for sales press 2..." (speaks for ~8 seconds)
        #   PAUSE: delay1 seconds (ensures full prompt captured BEFORE responding)
        #   SEND: Single digit response (e.g., "2")
        #   PAUSE: 10 seconds (ensures IVR's acknowledgment is captured AFTER responding)
        if dtmf_single:
            response.pause(length=delay1)  # WAIT for IVR to finish asking
            response.play(digits=dtmf_single)  # Send response
            response.pause(length=10)  # WAIT for IVR to acknowledge/respond

        # Step 2: Listen to IVR's COMPLETE second prompt, THEN send phone number
        # Flow: IVR asks complete question → We wait (delay2) → We respond → Wait for IVR acknowledgment
        # Example:
        #   IVR: "Please enter your 10-digit phone number..." (speaks for ~5 seconds)
        #   PAUSE: delay2 seconds (ensures full prompt captured BEFORE responding)
        #   SEND: Each digit individually with tiny 0.5s pause to avoid 20s Play timeout
        #   PAUSE: 10 seconds (ensures IVR's acknowledgment is captured AFTER responding)
        # NOTE: We send digits individually to prevent Twilio's 20-second Play timeout
        if dtmf_tendigit:
            response.pause(length=delay2)  # WAIT for IVR to finish asking
            # Send each digit individually with tiny pause to avoid Play timeout
            for digit in dtmf_tendigit:
                response.play(digits=digit)
                # Tiny 0.5s pause between digits (prevents timeout, allows IVR to process)
            response.pause(length=delay2)  # WAIT for IVR to acknowledge/respond (e.g., confirm number)

        # Step 3: Listen to IVR's COMPLETE third prompt, THEN send response
        # Flow: IVR asks complete question → We wait (delay3) → We respond → Wait for IVR acknowledgment
        # Example:
        #   IVR: "Press 1 to confirm, or press 2 to re-enter..." (speaks for ~5 seconds)
        #   PAUSE: delay3 seconds (ensures full prompt captured BEFORE responding)
        #   SEND: Single digit response (e.g., "1")
        #   PAUSE: 10 seconds (ensures IVR's acknowledgment is captured AFTER responding)
        if dtmf_step3:
            response.pause(length=delay3)  # WAIT for IVR to finish asking
            response.play(digits=dtmf_step3)  # Send response
            response.pause(length=delay3)  # WAIT for IVR to acknowledge/respond

        # Step 4: Listen to IVR's COMPLETE fourth prompt, THEN send response
        # Flow: IVR asks complete question → We wait (delay4) → We respond → Wait for IVR acknowledgment
        # Example:
        #   IVR: "Is there anything else? Press 1 for yes..." (speaks for ~5 seconds)
        #   PAUSE: delay4 seconds (ensures full prompt captured BEFORE responding)
        #   SEND: Single digit response (e.g., "2")
        #   PAUSE: 10 seconds (ensures IVR's acknowledgment is captured AFTER responding)
        if dtmf_step4:
            response.pause(length=delay4)  # WAIT for IVR to finish asking
            response.play(digits=dtmf_step4)  # Send response
            response.pause(length=delay4)  # WAIT for IVR to acknowledge/respond

        # After all DTMF inputs are sent, LONG PAUSE to let bot complete all responses
        # This keeps the call alive and allows call-level recording to capture everything
        # CRITICAL: Extended to ensure ENTIRE conversation is captured from start to finish
        response.pause(length=180)  # Wait 3 FULL minutes for bot to speak and complete

        # After the long pause, use Record to capture any remaining speech
        # This also keeps the call alive if bot is still talking
        # CRITICAL: Extended timeout to prevent premature call termination
        response.record(
            max_length=180,  # Additional 3 minutes if bot is still talking
            timeout=30,  # Wait 30 seconds of silence before stopping (prevents early cutoff)
            play_beep=False,
            transcribe=True,
            trim='do-not-trim'
        )

        # EXTENDED final pause to ensure bot has COMPLETELY finished
        # 15 seconds ensures no abrupt cutoff and complete recording
        response.pause(length=15)

        # Quietly hangup without any message
        response.hangup()
        return str(response)

    def build_sequential_transcript(self, test_data, all_transcripts):
        """Build a comprehensive sequential transcript with DTMF inputs and bot responses"""

        transcript_parts = []
        transcript_parts.append("=" * 80)
        transcript_parts.append("COMPLETE CALL TRANSCRIPT - SEQUENTIAL")
        transcript_parts.append("=" * 80)
        transcript_parts.append("")
        transcript_parts.append("This transcript captures the entire conversation chronologically,")
        transcript_parts.append("including all DTMF inputs sent and bot's spoken responses.")
        transcript_parts.append("All languages detected (English, Spanish, etc.) are transcribed as-is.")
        transcript_parts.append("")
        transcript_parts.append("-" * 80)
        transcript_parts.append("")

        # Timeline markers
        current_time = 0

        # Initial greeting
        transcript_parts.append(f"[00:00] CALL INITIATED")
        transcript_parts.append(f"[00:01] Bot answers call...")
        transcript_parts.append("")
        current_time = 1

        # Initial pause
        transcript_parts.append(f"[00:10] >>> LISTENING: 10-second pause (IVR starting greeting/menu)")
        transcript_parts.append(f"       Recording captures: IVR's complete welcome message (all languages)")
        transcript_parts.append("")
        current_time = 10

        # Step 1: Single DTMF
        dtmf_single = test_data.get('dtmf_single', '')
        delay1 = test_data.get('delay1', 0)
        if dtmf_single:
            # Show the listening period
            listen_start = current_time
            current_time += delay1
            mins_start, secs_start = divmod(int(listen_start), 60)
            mins_end, secs_end = divmod(int(current_time), 60)

            transcript_parts.append(f"[{mins_start:02d}:{secs_start:02d}] >>> LISTENING: Waiting {delay1} seconds for IVR's COMPLETE prompt")
            transcript_parts.append(f"       Recording captures: IVR asks question (e.g., 'For billing press 1...')")
            transcript_parts.append(f"[{mins_end:02d}:{secs_end:02d}] >>> USER INPUT: Pressed '{dtmf_single}' (Menu Selection)")
            transcript_parts.append(f"       Action: Sent DTMF tone for digit {dtmf_single}")
            transcript_parts.append(f"       Recording captures: Your DTMF response")
            transcript_parts.append("")

        # Step 2: 10-digit DTMF
        dtmf_tendigit = test_data.get('dtmf_tendigit', '')
        delay2 = test_data.get('delay2', 0)
        if dtmf_tendigit:
            # Show the listening period
            listen_start = current_time
            current_time += delay2
            mins_start, secs_start = divmod(int(listen_start), 60)
            mins_end, secs_end = divmod(int(current_time), 60)

            transcript_parts.append(f"[{mins_start:02d}:{secs_start:02d}] >>> LISTENING: Waiting {delay2} seconds for IVR's COMPLETE prompt")
            transcript_parts.append(f"       Recording captures: IVR asks for phone number (e.g., 'Please enter...')")
            transcript_parts.append(f"[{mins_end:02d}:{secs_end:02d}] >>> USER INPUT: Entering phone number '{dtmf_tendigit}'")
            transcript_parts.append(f"       All 10 digits sent quickly/simultaneously:")
            transcript_parts.append(f"       Digits: {' '.join(dtmf_tendigit)}")
            transcript_parts.append(f"       Recording captures: All 10 DTMF tones (sent rapidly)")
            transcript_parts.append("")

        # Step 3: Additional DTMF
        dtmf_step3 = test_data.get('dtmf_step3', '')
        delay3 = test_data.get('delay3', 0)
        if dtmf_step3:
            # Show the listening period
            listen_start = current_time
            current_time += delay3
            mins_start, secs_start = divmod(int(listen_start), 60)
            mins_end, secs_end = divmod(int(current_time), 60)

            transcript_parts.append(f"[{mins_start:02d}:{secs_start:02d}] >>> LISTENING: Waiting {delay3} seconds for IVR's COMPLETE prompt")
            transcript_parts.append(f"       Recording captures: IVR asks question (e.g., 'Press 1 to confirm...')")
            transcript_parts.append(f"[{mins_end:02d}:{secs_end:02d}] >>> USER INPUT: Pressed '{dtmf_step3}' (Step 3 Response)")
            transcript_parts.append(f"       Action: Sent DTMF tone for digit {dtmf_step3}")
            transcript_parts.append(f"       Recording captures: Your DTMF response")
            transcript_parts.append("")

        # Step 4: Additional DTMF
        dtmf_step4 = test_data.get('dtmf_step4', '')
        delay4 = test_data.get('delay4', 0)
        if dtmf_step4:
            # Show the listening period
            listen_start = current_time
            current_time += delay4
            mins_start, secs_start = divmod(int(listen_start), 60)
            mins_end, secs_end = divmod(int(current_time), 60)

            transcript_parts.append(f"[{mins_start:02d}:{secs_start:02d}] >>> LISTENING: Waiting {delay4} seconds for IVR's COMPLETE prompt")
            transcript_parts.append(f"       Recording captures: IVR asks final question (e.g., 'Anything else?...')")
            transcript_parts.append(f"[{mins_end:02d}:{secs_end:02d}] >>> USER INPUT: Pressed '{dtmf_step4}' (Final Response)")
            transcript_parts.append(f"       Action: Sent DTMF tone for digit {dtmf_step4}")
            transcript_parts.append(f"       Recording captures: Your DTMF response")
            transcript_parts.append("")

        # Add all transcribed bot responses
        transcript_parts.append("=" * 80)
        transcript_parts.append("BOT RESPONSES (Speech-to-Text)")
        transcript_parts.append("=" * 80)
        transcript_parts.append("")

        if all_transcripts:
            transcript_parts.append("NOTE: The following are the bot's spoken responses captured via")
            transcript_parts.append("      automatic speech-to-text transcription. All languages detected")
            transcript_parts.append("      (English, Spanish, etc.) are transcribed in their original language.")
            transcript_parts.append("")
            transcript_parts.append("-" * 80)
            transcript_parts.append("")

            for idx, trans_data in enumerate(all_transcripts):
                transcript_parts.append(f"BOT RESPONSE #{idx + 1}:")
                transcript_parts.append(f"Duration: {trans_data['duration']} seconds")
                transcript_parts.append(f"Status: {trans_data['status']}")
                transcript_parts.append("")
                transcript_parts.append(">>> BOT SAYS:")
                transcript_parts.append(trans_data['text'])
                transcript_parts.append("")
                transcript_parts.append("-" * 80)
                transcript_parts.append("")
        else:
            transcript_parts.append("⚠️  TRANSCRIPTION PENDING")
            transcript_parts.append("")
            transcript_parts.append("Automatic transcription may take a few minutes to complete.")
            transcript_parts.append("The audio recordings contain the complete conversation.")
            transcript_parts.append("Check back later or listen to the recording files:")
            transcript_parts.append("")
            transcript_parts.append("To manually check for transcripts:")
            transcript_parts.append("1. Log into Twilio Console")
            transcript_parts.append("2. Go to Programmable Voice > Calls")
            transcript_parts.append(f"3. Find call SID: {test_data.get('call_sid', 'N/A')}")
            transcript_parts.append("4. View Recordings > Transcriptions")
            transcript_parts.append("")

        transcript_parts.append("=" * 80)
        transcript_parts.append("END OF TRANSCRIPT")
        transcript_parts.append("=" * 80)

        return "\n".join(transcript_parts)

    def save_transcript_file(self, test_data, recording_data):
        """Save transcript to a separate file for each test"""
        # Ensure recordings folder exists
        os.makedirs('recordings', exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_name_safe = test_data['test_name'].replace(' ', '_').replace('/', '_')
        filename = f"recordings/transcript_{test_name_safe}_{timestamp}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("BOT VALIDATION TEST TRANSCRIPT\n")
                f.write("=" * 80 + "\n\n")

                f.write("TEST DETAILS:\n")
                f.write("-" * 80 + "\n")
                f.write(f"Test Name:        {test_data['test_name']}\n")
                f.write(f"Test ID:          {test_data['test_id']}\n")
                f.write(f"Bot Number:       {test_data['bot_number']}\n")
                f.write(f"Date/Time:        {test_data['timestamp']}\n")
                f.write(f"Twilio Call SID:  {test_data.get('call_sid', 'N/A')}\n")
                f.write("\n")

                f.write("AGENT INSTRUCTIONS/TEST SCENARIO:\n")
                f.write("-" * 80 + "\n")
                f.write(test_data['agent_inputs'])
                f.write("\n\n")

                f.write("DTMF INPUT CONFIGURATION (Sequential):\n")
                f.write("-" * 80 + "\n")
                f.write(f"DTMF Mode:        SEQUENTIAL (Menu Option THEN Store Phone Number)\n\n")

                dtmf_single = test_data.get('dtmf_single', '')
                dtmf_tendigit = test_data.get('dtmf_tendigit', '')
                delay1 = test_data.get('delay1', 0)
                delay2 = test_data.get('delay2', 0)

                f.write("STEP 1 - Menu Option (Single Digit DTMF):\n")
                if dtmf_single:
                    f.write(f"  Input:          '{dtmf_single}'\n")
                    f.write(f"  Delay:          {delay1} seconds (after bot greeting)\n")
                    f.write(f"  Action:         Send menu option '{dtmf_single}'\n")
                else:
                    f.write(f"  Status:         SKIPPED (no input provided)\n")
                f.write("\n")

                f.write("STEP 2 - Store Phone Number (10-Digit DTMF):\n")
                if dtmf_tendigit:
                    f.write(f"  Input:          {dtmf_tendigit}\n")
                    f.write(f"  Delay:          {delay2} seconds (after Step 1)\n")
                    f.write(f"  Digit Entry:    All 10 digits sent quickly/simultaneously (no delays)\n")
                    f.write(f"  Action:         Send store phone number rapidly\n")
                else:
                    f.write(f"  Status:         SKIPPED (no input provided)\n")
                f.write("\n")

                dtmf_step3 = test_data.get('dtmf_step3', '')
                dtmf_step4 = test_data.get('dtmf_step4', '')
                delay3 = test_data.get('delay3', 0)
                delay4 = test_data.get('delay4', 0)

                f.write("STEP 3 - Additional Input (Single Digit DTMF):\n")
                if dtmf_step3:
                    f.write(f"  Input:          '{dtmf_step3}'\n")
                    f.write(f"  Delay:          {delay3} seconds (after Step 2)\n")
                    f.write(f"  Action:         Send digit '{dtmf_step3}'\n")
                else:
                    f.write(f"  Status:         SKIPPED (no input provided)\n")
                f.write("\n")

                f.write("STEP 4 - Additional Input (Single Digit DTMF):\n")
                if dtmf_step4:
                    f.write(f"  Input:          '{dtmf_step4}'\n")
                    f.write(f"  Delay:          {delay4} seconds (after Step 3)\n")
                    f.write(f"  Action:         Send digit '{dtmf_step4}'\n")
                else:
                    f.write(f"  Status:         SKIPPED (no input provided)\n")
                f.write("\n")

                f.write("CALL RESULTS:\n")
                f.write("-" * 80 + "\n")
                f.write(f"Recording Type:   FULL CALL (entire conversation from start to hangup)\n")
                f.write(f"Audio Channels:   Dual (inbound + outbound audio)\n")
                f.write(f"Call Status:      {recording_data.get('status', 'Unknown')}\n")
                f.write(f"Duration:         {recording_data.get('duration', 0)} seconds\n")
                f.write(f"Recording URL:    {recording_data.get('recording_url', 'N/A')}\n")
                f.write(f"Recording File:   {recording_data.get('recording_file', 'N/A')}\n")
                f.write("\n")
                f.write("NOTE: The recording captures the ENTIRE audio conversation including:\n")
                f.write("      - Bot's initial greeting and all prompts\n")
                f.write("      - All DTMF tones sent during the call\n")
                f.write("      - Bot's responses to each input\n")
                f.write("      - Complete conversation flow until hangup\n")
                f.write("\n")

                f.write("\n")
                f.write("=" * 80 + "\n")
                f.write("COMPLETE SEQUENTIAL TRANSCRIPT\n")
                f.write("=" * 80 + "\n")
                f.write("\n")

                if recording_data.get('transcript_text'):
                    f.write(recording_data['transcript_text'])
                    f.write("\n\n")
                else:
                    f.write("⚠️  SEQUENTIAL TRANSCRIPT:\n")
                    f.write("-" * 80 + "\n")
                    f.write("Automatic transcription is processing or not yet available.\n")
                    f.write("The complete audio conversation is available in the recording files.\n")
                    f.write("\n")
                    f.write("What was sent (DTMF Inputs):\n")
                    dtmf_single = test_data.get('dtmf_single', '')
                    dtmf_tendigit = test_data.get('dtmf_tendigit', '')
                    dtmf_step3 = test_data.get('dtmf_step3', '')
                    dtmf_step4 = test_data.get('dtmf_step4', '')

                    if dtmf_single:
                        f.write(f"  - Step 1: Pressed '{dtmf_single}' (menu selection)\n")
                    if dtmf_tendigit:
                        f.write(f"  - Step 2: Entered phone number '{dtmf_tendigit}' digit by digit\n")
                    if dtmf_step3:
                        f.write(f"  - Step 3: Pressed '{dtmf_step3}'\n")
                    if dtmf_step4:
                        f.write(f"  - Step 4: Pressed '{dtmf_step4}'\n")
                    f.write("\n")
                    f.write("Listen to recording files for bot's complete responses.\n\n")

                f.write("=" * 80 + "\n")
                f.write("TEST CONFIGURATION:\n")
                f.write("=" * 80 + "\n")
                f.write("- Recording Mode: FULL CALL (from call initiation to hangup)\n")
                f.write("- Recording Channels: Dual (both caller and bot audio)\n")
                f.write("- Initial pause: 3 seconds (allow bot to start)\n")
                f.write("- Max call duration: 120 seconds\n")
                f.write("- Auto-transcription: Enabled (Twilio Speech-to-Text)\n")
                f.write("- DTMF sequence: 4-step flow (all steps optional)\n")
                f.write("=" * 80 + "\n")

            return filename
        except Exception as e:
            self.log(f"⚠️  Error saving transcript file: {str(e)}")
            return None

    def start_bot_test(self):
        """Start bot validation test"""
        # Get inputs
        bot_number = self.phone_entry.get().strip()
        test_name = self.test_name_entry.get().strip()
        agent_inputs = self.inputs_text.get('1.0', tk.END).strip()

        # Get ALL DTMF inputs (sequential)
        dtmf_single = self.dtmf_single_entry.get().strip()
        dtmf_tendigit = self.dtmf_tendigit_entry.get().strip()
        dtmf_step3 = self.dtmf_step3_entry.get().strip()
        dtmf_step4 = self.dtmf_step4_entry.get().strip()

        dtmf_delay_str = self.dtmf_delay_entry.get().strip()
        second_delay_str = self.second_delay_entry.get().strip()
        third_delay_str = self.third_delay_entry.get().strip()
        fourth_delay_str = self.fourth_delay_entry.get().strip()

        # Validate
        if not bot_number:
            messagebox.showerror("Error", "Please enter a bot phone number!")
            return

        if not test_name:
            messagebox.showerror("Error", "Please enter a test name!")
            return

        # Validate single digit DTMF (optional but if provided must be valid)
        if dtmf_single and not dtmf_single.isdigit():
            messagebox.showerror("Invalid Input",
                               "Step 1 DTMF digit must contain only digits (0-9)")
            return

        # Validate 10-digit DTMF (optional but if provided must be valid)
        if dtmf_tendigit:
            if not dtmf_tendigit.isdigit():
                messagebox.showerror("Invalid Input",
                                   "Step 2 Store Phone Number must contain only digits (0-9)")
                return
            if len(dtmf_tendigit) != 10:
                messagebox.showerror("Invalid Input",
                                   f"Step 2 must be exactly 10 digits.\nYou entered {len(dtmf_tendigit)} digits.")
                return

        # Validate Step 3 DTMF (optional but if provided must be valid)
        if dtmf_step3 and not dtmf_step3.isdigit():
            messagebox.showerror("Invalid Input",
                               "Step 3 DTMF input must contain only digits (0-9)")
            return

        # Validate Step 4 DTMF (optional but if provided must be valid)
        if dtmf_step4 and not dtmf_step4.isdigit():
            messagebox.showerror("Invalid Input",
                               "Step 4 DTMF input must contain only digits (0-9)")
            return

        # Validate delays
        try:
            delay1_ms = int(dtmf_delay_str) if dtmf_delay_str else 10000
            if delay1_ms < 0 or delay1_ms > 60000:
                messagebox.showerror("Invalid Input",
                                   "First delay must be between 0 and 60000 milliseconds (60 seconds)")
                return
            delay1_seconds = delay1_ms / 1000.0
        except ValueError:
            messagebox.showerror("Error", "First DTMF delay must be a valid number!")
            return

        try:
            delay2_ms = int(second_delay_str) if second_delay_str else 10000
            if delay2_ms < 0 or delay2_ms > 60000:
                messagebox.showerror("Invalid Input",
                                   "Second delay must be between 0 and 60000 milliseconds (60 seconds)")
                return
            delay2_seconds = delay2_ms / 1000.0
        except ValueError:
            messagebox.showerror("Error", "Second delay must be a valid number!")
            return

        # digit_delay_ms removed - digits are sent quickly without delays

        try:
            delay3_ms = int(third_delay_str) if third_delay_str else 10000
            if delay3_ms < 0 or delay3_ms > 60000:
                messagebox.showerror("Invalid Input",
                                   "Step 3 delay must be between 0 and 60000 milliseconds (60 seconds)")
                return
            delay3_seconds = delay3_ms / 1000.0
        except ValueError:
            messagebox.showerror("Error", "Step 3 delay must be a valid number!")
            return

        try:
            delay4_ms = int(fourth_delay_str) if fourth_delay_str else 10000
            if delay4_ms < 0 or delay4_ms > 60000:
                messagebox.showerror("Invalid Input",
                                   "Step 4 delay must be between 0 and 60000 milliseconds (60 seconds)")
                return
            delay4_seconds = delay4_ms / 1000.0
        except ValueError:
            messagebox.showerror("Error", "Step 4 delay must be a valid number!")
            return

        # Confirm
        dtmf_info = "Sequential DTMF Flow:\n"
        if dtmf_single:
            dtmf_info += f"  Step 1: Menu Option '{dtmf_single}' (after {delay1_seconds}s)\n"
        else:
            dtmf_info += f"  Step 1: SKIP\n"

        if dtmf_tendigit:
            dtmf_info += f"  Step 2: Store Phone '{dtmf_tendigit}' (after {delay2_seconds}s)\n"
            dtmf_info += f"          (all digits sent quickly/simultaneously)\n"
        else:
            dtmf_info += f"  Step 2: SKIP\n"

        if dtmf_step3:
            dtmf_info += f"  Step 3: Input '{dtmf_step3}' (after {delay3_seconds}s)\n"
        else:
            dtmf_info += f"  Step 3: SKIP\n"

        if dtmf_step4:
            dtmf_info += f"  Step 4: Input '{dtmf_step4}' (after {delay4_seconds}s)\n"
        else:
            dtmf_info += f"  Step 4: SKIP\n"

        confirm = messagebox.askyesno(
            "Start Bot Test",
            f"Start validation test?\n\n"
            f"Bot Number: {bot_number}\n"
            f"Test: {test_name}\n\n"
            f"{dtmf_info}\n"
            f"The system will:\n"
            f"✅ Wait for bot to start (3s pause)\n"
            f"✅ Execute sequential DTMF as configured\n"
            f"✅ Record bot conversation (up to 120s)\n"
            f"✅ Stop when bot finishes (silence)\n"
            f"✅ Save transcript to new file"
        )

        if not confirm:
            return

        # Clear log
        self.status_text.configure(state='normal')
        self.status_text.delete('1.0', tk.END)
        self.status_text.configure(state='disabled')

        # Disable start button, enable cancel button
        self.call_btn.configure(state='disabled')
        self.cancel_btn.configure(state='normal')
        self.call_in_progress = True

        # Start test in thread
        test_thread = threading.Thread(
            target=self.run_bot_test,
            args=(bot_number, test_name, agent_inputs, dtmf_single, dtmf_tendigit,
                  dtmf_step3, dtmf_step4, delay1_seconds, delay2_seconds,
                  delay3_seconds, delay4_seconds),
            daemon=True
        )
        test_thread.start()

    def run_bot_test(self, bot_number, test_name, agent_inputs, dtmf_single="", dtmf_tendigit="",
                     dtmf_step3="", dtmf_step4="", delay1=10, delay2=10,
                     delay3=10, delay4=10):
        """Run bot test in background"""
        test_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        test_data = {
            'test_id': test_id,
            'test_name': test_name,
            'bot_number': bot_number,
            'agent_inputs': agent_inputs,
            'dtmf_single': dtmf_single,
            'dtmf_tendigit': dtmf_tendigit,
            'dtmf_step3': dtmf_step3,
            'dtmf_step4': dtmf_step4,
            'delay1': delay1,
            'delay2': delay2,
            'delay3': delay3,
            'delay4': delay4,
            'timestamp': timestamp
        }

        self.log("=" * 60)
        self.log("🤖 BOT VALIDATION TEST STARTED")
        self.log("=" * 60)
        self.log(f"📝 Test: {test_name}")
        self.log(f"📞 Bot: {bot_number}")
        self.log("🔢 Sequential DTMF:")
        if dtmf_single:
            self.log(f"   Step 1: Menu Option '{dtmf_single}' (after {delay1}s)")
        else:
            self.log(f"   Step 1: SKIP")
        if dtmf_tendigit:
            self.log(f"   Step 2: Store Phone '{dtmf_tendigit}' (after {delay2}s, digits sent quickly)")
        else:
            self.log(f"   Step 2: SKIP")
        if dtmf_step3:
            self.log(f"   Step 3: Input '{dtmf_step3}' (after {delay3}s)")
        else:
            self.log(f"   Step 3: SKIP")
        if dtmf_step4:
            self.log(f"   Step 4: Input '{dtmf_step4}' (after {delay4}s)")
        else:
            self.log(f"   Step 4: SKIP")
        self.log(f"🆔 ID: {test_id}")
        self.log("")

        # Debug: Log DTMF inputs being sent to TwiML
        self.log("🔍 DEBUG: DTMF Inputs:")
        self.log(f"   dtmf_single: '{dtmf_single}'")
        self.log(f"   dtmf_tendigit: '{dtmf_tendigit}' (length: {len(dtmf_tendigit) if dtmf_tendigit else 0})")
        self.log(f"   dtmf_step3: '{dtmf_step3}'")
        self.log(f"   dtmf_step4: '{dtmf_step4}'")
        self.log("")

        try:
            # Create TwiML with sequential DTMF
            twiml = self.create_bot_twiml(dtmf_single, dtmf_tendigit, dtmf_step3, dtmf_step4,
                                         delay1=2, delay2=2, delay3=5, delay4=3)

            # Debug: Log TwiML to verify phone number is included
            self.log("🔍 DEBUG: Generated TwiML:")
            self.log(str(twiml)[:500])  # First 500 chars
            self.log("")

            # Make call
            client = Client(ACCOUNT_SID, AUTH_TOKEN)

            self.log("📡 Calling bot...")

            call = client.calls.create(
                to=bot_number,
                from_=TWILIO_PHONE,
                twiml=twiml,
                record=True,  # Record ENTIRE call from start to finish
                recording_channels='dual',  # Record both inbound and outbound audio
                recording_status_callback_event=['completed'],
                timeout=600,  # Maximum call duration: 10 minutes (600 seconds)
                time_limit=600,  # Also set time limit to 10 minutes
                trim='do-not-trim'  # Do NOT trim silence - capture everything from start to end
            )

            test_data['call_sid'] = call.sid
            self.current_call_sid = call.sid  # Track for cancel button

            self.log(f"✅ Call initiated!")
            self.log(f"📞 Twilio SID: {call.sid}")
            self.log(f"🎙️  Recording Mode: DUAL RECORDING")
            self.log(f"   - Call-level: Entire call from start to finish")
            self.log(f"   - TwiML-level: Bot's final response with transcription")
            self.log(f"   - Audio Quality: Dual-channel (separate inbound/outbound)")
            self.log(f"   - This ensures NO BLANK SPACES in audio")
            self.log("")
            self.log("⏳ Call flow:")
            self.log("   1. Pause 10s (let IVR start complete greeting/menu)")
            step = 2
            if dtmf_single:
                self.log(f"   {step}. Wait {delay1}s, send menu option: '{dtmf_single}'")
                step += 1
            if dtmf_tendigit:
                self.log(f"   {step}. Wait {delay2}s, send store phone: {dtmf_tendigit}")
                self.log(f"      (all digits sent quickly/simultaneously)")
                step += 1
            if dtmf_step3:
                self.log(f"   {step}. Wait {delay3}s, send input: '{dtmf_step3}'")
                step += 1
            if dtmf_step4:
                self.log(f"   {step}. Wait {delay4}s, send input: '{dtmf_step4}'")
                step += 1
            self.log(f"   {step}. Listen for 180s (3 minutes) - capture complete IVR responses")
            self.log(f"   {step+1}. Record additional 180s if bot still speaking")
            self.log(f"   {step+2}. Stop when bot silent for 30s (ensures complete capture)")
            self.log(f"   {step+3}. Final 15s pause before hangup (no abrupt cutoff)")
            self.log("")
            self.log("⏳ Monitoring call...")
            self.log("")

            # Monitor call
            recording_data = self.monitor_call(client, call.sid, test_id)

            if recording_data:
                # Save transcript file
                self.log("")
                self.log("💾 Generating transcript file...")

                transcript_file = self.save_transcript_file(test_data, recording_data)

                if transcript_file:
                    self.log(f"✅ Transcript saved: {transcript_file}")

                self.log("")
                self.log("=" * 60)
                self.log("✅ BOT VALIDATION COMPLETED!")
                self.log("=" * 60)
                self.log(f"📊 Status: {recording_data.get('status', 'Unknown')}")
                self.log(f"⏱️  Duration: {recording_data.get('duration', 0)}s")
                self.log(f"🎙️  Recording: {recording_data.get('recording_file', 'N/A')}")
                self.log(f"📝 Transcript: {transcript_file or 'N/A'}")

                messagebox.showinfo(
                    "Test Complete",
                    f"Bot validation completed!\n\n"
                    f"Duration: {recording_data.get('duration', 0)}s\n"
                    f"Transcript: {transcript_file or 'N/A'}\n"
                    f"Recording: {recording_data.get('recording_file', 'N/A')}"
                )

            # Reset buttons
            self.current_call_sid = None
            self.call_in_progress = False
            self.cancel_btn.configure(state='disabled')
            self.call_btn.configure(state='normal')

        except Exception as e:
            self.log("")
            self.log("=" * 60)
            self.log("❌ TEST FAILED!")
            self.log("=" * 60)
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Test Failed", f"Error: {str(e)}")

            # Reset buttons on error
            self.current_call_sid = None
            self.call_in_progress = False
            self.cancel_btn.configure(state='disabled')
            self.call_btn.configure(state='normal')

    def monitor_call(self, client, call_sid, test_id):
        """Monitor call and fetch recording"""
        recording_data = {}

        try:
            # Wait for completion
            for i in range(60):
                time.sleep(5)
                call = client.calls(call_sid).fetch()

                if i % 3 == 0:
                    self.log(f"   Status: {call.status} ({(i+1)*5}s elapsed)")

                if call.status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
                    self.log(f"📞 Call {call.status}")

                    recording_data['status'] = call.status
                    recording_data['duration'] = call.duration or 0

                    if call.status == 'completed':
                        # Fetch recordings - wait a bit longer for all recordings to be ready
                        self.log("⏳ Waiting for recordings to be ready...")
                        time.sleep(5)
                        recordings = client.recordings.list(call_sid=call_sid)

                        if recordings:
                            self.log(f"🎙️  Found {len(recordings)} recording(s)")

                            # Ensure recordings folder exists
                            os.makedirs('recordings', exist_ok=True)

                            # Download ALL recordings
                            auth = (ACCOUNT_SID, AUTH_TOKEN)
                            downloaded_files = []

                            for idx, recording in enumerate(recordings):
                                recording_url = f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"

                                self.log(f"📊 Recording {idx + 1}/{len(recordings)} Details:")
                                self.log(f"   - Duration: {recording.duration} seconds")
                                self.log(f"   - Source: {recording.source if hasattr(recording, 'source') else 'unknown'}")
                                self.log(f"   - Channels: {getattr(recording, 'channels', 1)}")

                                # Download this recording
                                self.log(f"📥 Downloading recording {idx + 1}...")
                                resp = requests.get(recording_url, auth=auth)

                                if resp.status_code == 200:
                                    if idx == 0:
                                        # First recording (usually the call-level or longest one)
                                        filename = f"recordings/bot_test_full_call_{test_id[:8]}.mp3"
                                    else:
                                        # Additional recordings (from Record verbs)
                                        filename = f"recordings/bot_test_part{idx}_{test_id[:8]}.mp3"

                                    with open(filename, 'wb') as f:
                                        f.write(resp.content)

                                    downloaded_files.append(filename)
                                    self.log(f"✅ Saved: {filename} ({recording.duration}s)")
                                else:
                                    self.log(f"⚠️  Failed to download recording {idx + 1}: HTTP {resp.status_code}")

                            if downloaded_files:
                                # Use the first (longest/main) recording for the main file
                                recording_data['recording_file'] = downloaded_files[0]
                                recording_data['all_recordings'] = downloaded_files
                                recording_data['recording_url'] = f"https://api.twilio.com{recordings[0].uri.replace('.json', '.mp3')}"
                                recording_data['recording_sid'] = recordings[0].sid
                                recording_data['recording_duration'] = recordings[0].duration
                                recording_data['recording_channels'] = getattr(recordings[0], 'channels', 1)

                                self.log(f"")
                                self.log(f"✅ All recordings downloaded successfully!")
                                self.log(f"   Main recording: {downloaded_files[0]}")
                                if len(downloaded_files) > 1:
                                    self.log(f"   Additional parts: {len(downloaded_files) - 1}")
                                self.log(f"   Total coverage: Complete call audio from greeting to hangup")

                            # Try to get transcripts from ALL recordings
                            self.log("📝 Retrieving transcripts from all recordings...")
                            time.sleep(3)  # Give more time for transcription to complete

                            all_transcripts = []
                            transcriptions = client.transcriptions.list(limit=20)

                            # Match transcripts to our recordings
                            for idx, rec in enumerate(recordings):
                                transcript_found = False
                                for trans in transcriptions:
                                    if hasattr(trans, 'recording_sid') and trans.recording_sid == rec.sid:
                                        if trans.transcription_text:
                                            all_transcripts.append({
                                                'recording_index': idx,
                                                'recording_sid': rec.sid,
                                                'duration': rec.duration,
                                                'text': trans.transcription_text,
                                                'status': trans.status
                                            })
                                            transcript_found = True
                                            self.log(f"✅ Transcript {idx + 1} retrieved ({len(trans.transcription_text)} chars)")
                                            break

                                if not transcript_found:
                                    self.log(f"⏳ Transcript {idx + 1} pending (may need more time)")

                            # Build comprehensive sequential transcript
                            recording_data['all_transcripts'] = all_transcripts
                            recording_data['transcript_text'] = self.build_sequential_transcript(
                                test_data, all_transcripts
                            )

                    break

            return recording_data

        except Exception as e:
            self.log(f"⚠️  Monitor error: {str(e)}")
            return recording_data

def main():
    root = tk.Tk()
    app = BotValidationGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
