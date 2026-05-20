from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .base import MetodoPago


class PagoCheque(MetodoPago):
    """
    Implementación 2: pago con cheque.
    Genera y retorna un PDF descargable con los datos del cheque.
    """

    def procesar_pago(self, orden):
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Encabezado
        p.setFont('Helvetica-Bold', 22)
        p.drawCentredString(width / 2, height - 80, 'KIBO PET SHOP')
        p.setFont('Helvetica', 13)
        p.drawCentredString(width / 2, height - 108, 'COMPROBANTE DE PAGO CON CHEQUE')
        p.line(60, height - 125, width - 60, height - 125)

        # Datos del cheque
        p.setFont('Helvetica', 12)
        p.drawString(80, height - 165, f'Beneficiario:      Kibo Pet Shop S.A.')
        p.drawString(80, height - 195, f'Número de orden:   #{orden.id}')
        p.drawString(80, height - 225, f'Fecha de emisión:  {orden.created_at.strftime("%d/%m/%Y")}')
        p.drawString(80, height - 255, f'Cliente:           {orden.user.get_full_name() or orden.user.username}')

        # Caja de monto
        p.rect(80, height - 340, width - 160, 55)
        p.setFont('Helvetica-Bold', 16)
        p.drawCentredString(width / 2, height - 308, f'MONTO TOTAL: ${orden.total}')

        # Líneas de firma
        p.line(80, height - 430, width / 2 - 20, height - 430)
        p.setFont('Helvetica', 10)
        p.drawString(80, height - 450, 'Firma del cliente')

        p.line(width / 2 + 20, height - 430, width - 80, height - 430)
        p.drawString(width / 2 + 20, height - 450, 'Firma autorizada — Kibo Pet Shop')

        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer
