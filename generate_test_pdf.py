from reportlab.pdfgen import canvas

def create_pdf(filename):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "Hello World")
    c.drawString(100, 700, "This is a test PDF.")
    c.showPage()
    c.drawString(100, 750, "Page 2")
    c.save()

if __name__ == "__main__":
    create_pdf("test.pdf")
    print("test.pdf created")
