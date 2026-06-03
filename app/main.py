import time

from app.extract_pdf import (
    extract_text_from_pdf,
    extract_emails
)

from app.ai_generator import generate_email
from app.email_sender import send_email


# Production PDF
pdf_path = "data/hr_contacts.pdf"

# Extract text from PDF
text = extract_text_from_pdf(pdf_path)

# Extract HR emails
emails = extract_emails(text)

print(f"\nTotal Emails Found: {len(emails)}\n")


count = 0

for email in emails:

    # Stop after 10 emails
    if count >= 10:
        print("\nDaily limit reached.")
        break

    print("\n==============================")
    print(f"Sending Email To: {email}")
    print("==============================\n")

    try:

        # Generate AI email
        ai_email = generate_email()

        # Send email
        send_email(
            receiver_email=email,
            subject="Internship Opportunity Inquiry",
            body=ai_email
        )

        print(f"\nSuccessfully sent to: {email}\n")

        count += 1

    except Exception as e:

        print(f"\nFailed to send email to {email}")
        print(f"Error: {e}\n")

    # Wait 10 minutes
    print("Waiting 10 minutes before next email...\n")

    time.sleep(600)


print("\nAutomation Completed.\n")