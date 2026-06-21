from fpdf import FPDF
from fpdf.enums import XPos, YPos


class PDFReport(FPDF):

    def header(self):
        self.set_font("Helvetica", "B", 16)
        # Обновленный синтаксис перехода на новую строку вместо deprecated ln=True
        self.cell(
            0,
            10,
            "Project Structure & Listing Report",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


# Инициализация PDF
pdf = PDFReport()
pdf.add_page()
pdf.set_font("Helvetica", size=11)

# Раздел 1
pdf.set_font("Helvetica", "B", 14)
pdf.cell(0, 10, "1. Project Overview", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_font("Helvetica", size=11)
pdf.multi_cell(
    0,
    6,
    "The 'osint_app' is a modular Open Source Intelligence application. "
    "It combines a web-based administration panel with a Telegram bot interface "
    "for data gathering and analysis.",
)
pdf.ln(5)

# Раздел 2
pdf.set_font("Helvetica", "B", 14)
pdf.cell(
    0, 10, "2. Directory & File Listing", new_x=XPos.LMARGIN, new_y=YPos.NEXT
)
pdf.set_font("Helvetica", size=11)

structure = [
    ("modules/", "Core directory containing distinct OSINT search/scraping modules."),
    ("templates/", "HTML templates for the web interface layout."),
    ("static/", "Frontend assets including CSS, JavaScript, and UI components."),
    ("reports/", "Output directory where generated search reports are stored."),
    ("main.py", "Main entry point that initializes and runs the web server."),
    ("init_tg.py", "Handles Telegram Bot integration and command processing."),
    ("database.py", "Manages SQLite database connections and core CRUD operations."),
    ("models.py", "Defines the database schema and ORM models for the system."),
    ("osint.db", "Active SQLite database storing user data, logs, and targets."),
    (".env", "Environment configuration file for sensitive API keys and tokens."),
]

# Чтобы исправить ошибку "Not enough horizontal space", теперь сначала пишется жирный текст,
# а затем справа от него выводится описание через multi_cell, смещая каретку вниз.
for item, desc in structure:
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(35, 6, item, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, f"- {desc}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# Сохранение файла
pdf.output("Project_Report.pdf")
print("PDF успешно создан под именем 'Project_Report.pdf'")