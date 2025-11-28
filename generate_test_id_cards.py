from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_id_cards():
    """Create a test PDF with 4 pages (2 fronts, 2 backs) for ID cards."""
    c = canvas.Canvas("test_id_cards.pdf", pagesize=letter)
    
    # Page 1: Card 1 Front
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, 700, "CARD 1 - FRONT")
    c.setFont("Helvetica", 14)
    c.drawString(100, 650, "Name: John Doe")
    c.drawString(100, 630, "ID: 12345")
    c.showPage()
    
    # Page 2: Card 1 Back
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, 700, "CARD 1 - BACK")
    c.setFont("Helvetica", 14)
    c.drawString(100, 650, "Emergency Contact: 555-1234")
    c.showPage()
    
    # Page 3: Card 2 Front
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, 700, "CARD 2 - FRONT")
    c.setFont("Helvetica", 14)
    c.drawString(100, 650, "Name: Jane Smith")
    c.drawString(100, 630, "ID: 67890")
    c.showPage()
    
    # Page 4: Card 2 Back
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, 700, "CARD 2 - BACK")
    c.setFont("Helvetica", 14)
    c.drawString(100, 650, "Emergency Contact: 555-5678")
    c.showPage()
    
    c.save()
    print("test_id_cards.pdf created with 4 pages")

if __name__ == "__main__":
    create_test_id_cards()
