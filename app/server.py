from fastapi import FastAPI
from fastapi import Request
from fastapi import UploadFile
from fastapi import File
from fastapi import Form
from fastapi import BackgroundTasks

from fastapi.responses import HTMLResponse, StreamingResponse

from fastapi.staticfiles import StaticFiles

from fastapi.templating import Jinja2Templates

import shutil
import time
import csv
import os
import asyncio
from typing import List

from app.extract_pdf import (
    extract_text_from_pdf,
    extract_emails
)

from app.ai_generator import generate_email

from app.email_sender import send_email


# Thread-safe LogManager to capture stdout/logs and broadcast them to UI clients
class LogManager:
    def __init__(self):
        self.logs: List[str] = []
        self.listeners: List[asyncio.Queue] = []
        self.loop = None
        self.is_running = False

    def set_loop(self, loop):
        self.loop = loop

    def clear(self):
        self.logs = []
        self.is_running = True

    def log(self, message: str):
        print(message)  # Still print to terminal
        self.logs.append(message)
        if self.loop and self.listeners:
            def broadcast():
                for queue in self.listeners:
                    queue.put_nowait(message)
            self.loop.call_soon_threadsafe(broadcast)

    def remove_listener(self, queue: asyncio.Queue):
        if queue in self.listeners:
            self.listeners.remove(queue)


log_manager = LogManager()
app = FastAPI()


# Static folder
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# Templates folder
templates = Jinja2Templates(
    directory="templates"
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


def process_emails_background(pdf_path: str, resume_path: str, daily_limit: int, delay: int):
    try:
        # Extract text
        log_manager.log("📄 Extracting text from HR contacts PDF...")
        text = extract_text_from_pdf(pdf_path)

        # Extract emails
        log_manager.log("🔎 Searching for email addresses...")
        emails = extract_emails(text)
        log_manager.log(f"📋 Found {len(emails)} email address(es) in HR contacts PDF.")

        sent_count = 0

        # Create CSV if not exists
        if not os.path.exists("sent_log.csv"):
            with open("sent_log.csv", "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["email"])

        # Read already sent emails
        sent_emails = set()
        with open("sent_log.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                sent_emails.add(row[0])

        # Start automation
        for email in emails:
            # Skip duplicates
            if email in sent_emails:
                log_manager.log(f"⚠️ Already sent before: {email}")
                continue

            # Daily limit
            if sent_count >= daily_limit:
                log_manager.log("✅ Daily limit reached.")
                break

            try:
                log_manager.log(f"🚀 Generating email for: {email}")
                # Generate AI email
                ai_email = generate_email()

                log_manager.log(f"📨 Sending email to: {email}")
                # Send Email
                send_email(
                    receiver_email=email,
                    subject="Internship Opportunity Inquiry",
                    body=ai_email,
                    resume_path=resume_path
                )

                # Save sent email
                with open("sent_log.csv", "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([email])

                sent_count += 1
                log_manager.log(f"✅ Successfully sent to: {email}")

                # Delay
                log_manager.log(f"⏳ Waiting {delay} minute(s) before next email...")
                time.sleep(delay * 60)

            except Exception as e:
                log_manager.log(f"❌ Failed for: {email}")
                log_manager.log(f"Error details: {str(e)}")
        
        log_manager.log("\n✅ Background automation completed.")
    except Exception as e:
        log_manager.log(f"❌ Fatal error in background process: {str(e)}")
    finally:
        log_manager.is_running = False


@app.post("/send-emails")
async def send_emails_route(
    request: Request,
    background_tasks: BackgroundTasks,
    pdf_file: UploadFile = File(...),
    resume_file: UploadFile = File(...),
    daily_limit: int = Form(...),
    delay: int = Form(...)
):
    # Set the event loop inside the manager
    try:
        log_manager.set_loop(asyncio.get_running_loop())
    except RuntimeError:
        pass

    # Clear previous logs and start fresh
    log_manager.clear()
    log_manager.log(f"📤 HR PDF uploaded: {pdf_file.filename}")
    log_manager.log(f"📤 Resume uploaded: {resume_file.filename}")
    log_manager.log("⚙️ Starting background automation...")

    # Create folders
    os.makedirs("data", exist_ok=True)
    os.makedirs("resume", exist_ok=True)

    # Save HR PDF
    pdf_path = f"data/{pdf_file.filename}"
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(pdf_file.file, buffer)

    # Save Resume
    resume_path = f"resume/{resume_file.filename}"
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(resume_file.file, buffer)

    # Queue the background task
    background_tasks.add_task(
        process_emails_background, 
        pdf_path, 
        resume_path, 
        daily_limit, 
        delay
    )

    return {
        "status": "success",
        "message": "Email automation started in the background! Dynamic logs are streaming below.",
        "logs": log_manager.logs
    }


@app.get("/status")
def get_status():
    return {
        "is_running": log_manager.is_running,
        "logs": log_manager.logs
    }


@app.get("/stream-logs")
async def stream_logs(skip: int = 0):
    try:
        log_manager.set_loop(asyncio.get_running_loop())
    except RuntimeError:
        pass

    queue = asyncio.Queue()
    log_manager.listeners.append(queue)

    async def log_generator():
        # First, yield any existing logs that client hasn't rendered yet
        if skip < len(log_manager.logs):
            for log_msg in log_manager.logs[skip:]:
                yield f"data: {log_msg}\n\n"

        try:
            while True:
                message = await queue.get()
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            log_manager.remove_listener(queue)
            raise

    return StreamingResponse(log_generator(), media_type="text/event-stream")