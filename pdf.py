from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        # Add hotel logo (adjusted size)
        self.image('logo1.png', 10, 8, 40)  # Adjust the path and size of your logo
        self.set_font('Arial', 'B', 14)
        
        # Position for the hotel name centered
        self.cell(0, 10, 'Hotel Hype', ln=False, align='C')
        self.ln(8)
        
        # Add the subheading centered
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Official Booking Receipt', ln=True, align='C')
        
        # Add the stamp image to the right of the hotel name
        self.image('stamp.png', x=105, y=10, w=35)  # Ensure the image path is correct and adjust size
        
        self.ln(15)  # Ensure spacing after the header

    def footer(self):
        self.set_y(-17)
        # self.set_text_color(0,0,0)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Thank you for choosing Hotel Hype!', 0, 0, 'C')
        # self.cell(0, 10, 'Page %s' % self.page_no(), 0, 0, 'R')

def create_hotel_receipt(hotel_name, booking_price, total_rooms, payment_date, payment_time, output_filename):
    pdf = PDF(orientation='P', unit='mm', format=(150, 163))
    pdf.add_page()

    # Hotel details left-aligned
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Hotel Name: {hotel_name}', ln=True)

    # Receipt date
    pdf.ln(1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f'Receipt Date: {datetime.now().strftime("%Y-%m-%d")}', ln=True)
    pdf.ln(-3)
    # pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f"Booking Price: {booking_price}", ln=True)
    pdf.ln(-3)
    pdf.cell(0, 10, f"Total Rooms Booked: {total_rooms}", ln=True)
    pdf.ln(-3)
    pdf.cell(0, 10, f"Payment Date: {payment_date}", ln=True)
    pdf.ln(-3)
    pdf.cell(0, 10, f"Payment Time: {payment_time}", ln=True)
    

    # Move the description after the payment details
    pdf.ln(5)  # Space before description
    pdf.set_font('Arial', '', 9.5)  # Reduced font size for the description
    pdf.multi_cell(0, 6, "Note! Please save this booking receipt and show it at the hotel check-in time for a smooth check-in process.")
    pdf.ln(10)  # Space after the description

    # Signature area left-aligned
    pdf.set_font('Arial', '', 12)
    # pdf.set_text_color(184, 28, 28)
    pdf.cell(0, 10, 'Authorized Signature:', ln=True)
    signature_y = pdf.get_y()  # Get the y-coordinate for the signature line
    
    # Adjust the image to fit within the signature area
    pdf.image('sign.png', x=pdf.get_x() + 40, y=signature_y - 24, w=50, h=30)  # Adjust x and y as needed

    # Save the PDF
    pdf.output(output_filename)

# Define hotel details
hotel_name = "Hotel Hype"
booking_price = "$200"
total_rooms = 5
payment_date = datetime.now().strftime("%Y-%m-%d")
payment_time = datetime.now().strftime("%H:%M:%S")
output_filename = "hotel_hype_receipt_final.pdf"

# Create the PDF receipt
create_hotel_receipt(hotel_name, booking_price, total_rooms, payment_date, payment_time, output_filename)
