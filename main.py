import tkinter as tk # for GUI
from tkinter import messagebox 
import smtplib #to send emails
import imaplib #to read/receive emails,
import email  #to read/receive emails,
import threading #to manage background tasks (like scheduled sending) 
import schedule
import time
import google.generativeai as genai #to generate AI-written emails,
from email.message import EmailMessage #to construct email objects properly.

# Setup Gemini AI
genai.configure(api_key="API_KEY")

class SmartEmailAssistant(tk.Tk):
    def __init__(self):
        super().__init__()

        # Window Settings
        self.title("Smart Email Assistant")
        self.geometry("800x600")
        self.resizable(True, True)

        # Initialize credentials
        self.email_user = ""
        self.email_pass = ""

        # Sidebar
        self.sidebar = tk.Frame(self, bg="#2C3E50", width=150)
        self.sidebar.pack(side="left", fill="y")

        # Buttons for navigation
        tk.Button(self.sidebar, text="Login", fg="white", bg="#34495E", command=self.show_login).pack(fill="x")
        tk.Button(self.sidebar, text="Compose Email", fg="white", bg="#34495E", command=self.show_compose).pack(fill="x")
        tk.Button(self.sidebar, text="AI Generator", fg="white", bg="#34495E", command=self.show_ai_generator).pack(fill="x")
        tk.Button(self.sidebar, text="Read Emails", fg="white", bg="#34495E", command=self.read_latest_email).pack(fill="x")
        tk.Button(self.sidebar, text="Schedule Email", fg="white", bg="#34495E", command=self.show_scheduler).pack(fill="x")

        # Main Area
        self.main_frame = tk.Frame(self, bg="white")
        self.main_frame.pack(side="right", fill="both", expand=True)

        # Start Scheduler Thread
        threading.Thread(target=self.run_scheduler, daemon=True).start()

        self.show_login()

    # Login Page
    def show_login(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Login", font=("Arial", 20)).pack(pady=20)

        tk.Label(self.main_frame, text="Email:").pack()
        email_entry = tk.Entry(self.main_frame, width=40)
        email_entry.pack()

        tk.Label(self.main_frame, text="App Password:").pack()
        pass_entry = tk.Entry(self.main_frame, width=40, show="*")
        pass_entry.pack()

        def login_action():
            self.email_user = email_entry.get()
            self.email_pass = pass_entry.get()

            if self.email_user and self.email_pass:
                messagebox.showinfo("Success", "Logged in Successfully!")
                self.show_compose()
            else:
                messagebox.showerror("Error", "Please enter both email and password.")

        tk.Button(self.main_frame, text="Login", command=login_action).pack(pady=10)

    #  Compose Email Page
    def show_compose(self):
        self.clear_main_frame()

        tk.Label(self.main_frame, text="Compose Email", font=("Arial", 20)).pack(pady=20)
        tk.Label(self.main_frame, text="To:").pack()
        to_entry = tk.Entry(self.main_frame, width=50)
        to_entry.pack()

        tk.Label(self.main_frame, text="Subject:").pack()
        subject_entry = tk.Entry(self.main_frame, width=50)
        subject_entry.pack()

        tk.Label(self.main_frame, text="Body:").pack()
        body_text = tk.Text(self.main_frame, width=60, height=15)
        body_text.pack()


        def send_action():
            to_email = to_entry.get()
            subject = subject_entry.get()
            body = body_text.get("1.0", tk.END)

            if to_email and subject and body.strip():
                self.send_email(to_email, subject, body)
            else:
                messagebox.showerror("Error", "All fields are required!")

        tk.Button(self.main_frame, text="Send Email", command=send_action).pack(pady=10)

    # AI Email Generator Page
    def show_ai_generator(self):
        self.clear_main_frame()

        tk.Label(self.main_frame, text="AI Email Generator", font=("Arial", 20)).pack(pady=20)

        # Input fields
        tk.Label(self.main_frame, text="Sender Name:").pack()
        sender_entry = tk.Entry(self.main_frame, width=50)
        sender_entry.pack()

        tk.Label(self.main_frame, text="Receiver Name:").pack()
        receiver_entry = tk.Entry(self.main_frame, width=50)
        receiver_entry.pack()

        tk.Label(self.main_frame, text="Receiver Email:").pack()
        to_email_entry = tk.Entry(self.main_frame, width=50)
        to_email_entry.pack()

        tk.Label(self.main_frame, text="Subject:").pack()
        subject_preview = tk.Entry(self.main_frame, width=50)
        subject_preview.pack()

        tk.Label(self.main_frame, text="Describe your email:").pack()
        prompt_entry = tk.Entry(self.main_frame, width=50)
        prompt_entry.pack()

        # Email preview text box
        email_preview = tk.Text(self.main_frame, width=60, height=15)
        email_preview.pack()

        def extract_subject_and_body(email_text):
            # Step 1: Split lines for processing
            lines = email_text.strip().split('\n')

            subject = None
            body_lines = []

            # Step 2: Find the subject line
            for index, line in enumerate(lines):
                # Normalize the case and remove extra spaces
                line_strip = line.strip()

                if line_strip.lower().startswith('subject:'):
                    # Extract subject (remove 'subject:' prefix)
                    subject = line_strip[len('subject:'):].strip()

                    # Skip adding this line to the body
                    continue

                # If subject already found, add remaining lines to body
                body_lines.append(line)

            # Step 3: Join body lines back into text
            body = '\n'.join(body_lines).strip()

            return subject, body

        def generate_action():
            sender = sender_entry.get()
            receiver = receiver_entry.get()
            prompt = prompt_entry.get()

            if not sender or not receiver or not prompt:
                messagebox.showerror("Error", "Sender, Receiver, and description are required!")
                return

            full_prompt = f"Write an email from {sender} to {receiver}: {prompt}"
            email_content = self.generate_email(full_prompt)

            subject, body =extract_subject_and_body(email_content)

            if email_content:
                subject_preview.delete(0, tk.END)
                subject_preview.insert(tk.END, subject)
                email_preview.delete("1.0", tk.END)
                email_preview.insert(tk.END, body)
            else:
                messagebox.showerror("Error", "Failed to generate email.")

        def send_ai_email():
            to_email = to_email_entry.get()
            subject = subject_preview.get()
            body = email_preview.get("1.0", tk.END)

            if not to_email or not subject or not body.strip():
                messagebox.showerror("Error", "Recipient Email, Subject, and Body are required!")
                return

            self.send_email(to_email, subject, body)

        tk.Button(self.main_frame, text="Generate Email", command=generate_action).pack(pady=5)
        tk.Button(self.main_frame, text="Send This Email", command=send_ai_email).pack(pady=5)

    # Scheduler Page
    def show_scheduler(self):
        self.clear_main_frame()

        tk.Label(self.main_frame, text="Schedule Email", font=("Arial", 20)).pack(pady=20)

        tk.Label(self.main_frame, text="To:").pack()
        to_entry = tk.Entry(self.main_frame, width=50)
        to_entry.pack()

        tk.Label(self.main_frame, text="Subject:").pack()
        subject_entry = tk.Entry(self.main_frame, width=50)
        subject_entry.pack()

        tk.Label(self.main_frame, text="Body:").pack()
        body_text = tk.Text(self.main_frame, width=60, height=15)
        body_text.pack()

        tk.Label(self.main_frame, text="Time (HH:MM, 24hr):").pack()
        time_entry = tk.Entry(self.main_frame, width=20)
        time_entry.pack()

        def schedule_action():
            to_email = to_entry.get()
            subject = subject_entry.get()
            body = body_text.get("1.0", tk.END)
            time_of_day = time_entry.get()

            if to_email and subject and body.strip() and time_of_day:
                schedule.every().day.at(time_of_day).do(self.send_email, to_email, subject, body)
                messagebox.showinfo("Scheduled", f"Email scheduled to {to_email} at {time_of_day}")
            else:
                messagebox.showerror("Error", "All fields are required!")

        tk.Button(self.main_frame, text="Schedule Email", command=schedule_action).pack(pady=10)

    # Read The Latest Email
    def read_latest_email(self):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email_user, self.email_pass)
            mail.select("inbox")

            _, data = mail.search(None, "ALL")
            email_ids = data[0].split()

            if not email_ids:
                messagebox.showinfo("Info", "No emails found!")
                return

            latest_email_id = email_ids[-1]
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                messagebox.showerror("Error", "Failed to fetch the email.")
                return


            raw_email = msg_data[0][1].decode("utf-8")
            msg = email.message_from_string(raw_email)

            sender = msg["From"]
            subject = msg["Subject"]
            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = msg.get_payload(decode=True).decode()

            self.clear_main_frame()

            tk.Label(self.main_frame, text="Latest Email", font=("Arial", 20)).pack(pady=10)
            tk.Label(self.main_frame, text=f"From: {sender}").pack()
            tk.Label(self.main_frame, text=f"Subject: {subject}").pack()

            email_body = tk.Text(self.main_frame, width=60, height=15)
            email_body.insert(tk.END, body)
            email_body.config(state="disabled")
            email_body.pack()

            mail.logout()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read email: {e}")

    #  Send Email Function
    def send_email(self, to_email, subject, body):
        try:
            msg = EmailMessage()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.set_content(body)

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.email_user, self.email_pass)
                server.send_message(msg)

            messagebox.showinfo("Success", f"Email sent to {to_email}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to send email: {e}")

    #  Generate AI Email
    @staticmethod
    def generate_email(prompt):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate email: {e}")
            return None


    #  Run Scheduler Loop
    @staticmethod
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    #  Clear the main content frame
    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    app = SmartEmailAssistant()
    app.mainloop()

