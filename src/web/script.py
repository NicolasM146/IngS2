from datetime import datetime, timedelta, date
from src.core.database import db
from src.core.Reserva.reservation import Reservation
from src.core.Alquiler.Rental import Rental
import stripe
import os
from dotenv import load_dotenv
from src.web import create_app  # Tu factory para app Flask

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def procesar_pagos_pendientes():
    """Cobra el pago faltante 1 día antes del check-in"""
    hoy = date.today()
    fecha_mañana = hoy + timedelta(days=1)

    reservas_pendientes = Reservation.query.filter(
        Reservation.start_date == fecha_mañana,
        Reservation.status == 'Pendiente'
    ).all()

    if not reservas_pendientes:
        print("No hay reservas pendientes para procesar.")
        return
    
    for reserva in reservas_pendientes:
        try:
            alquiler = db.session.get(Rental, reserva.rental_id)

            usuario = reserva.user

            if not usuario.stripe_payment_method_id:
                print(f"Usuario {usuario.id} sin método de pago. Reserva {reserva.id} no procesada.")
                continue

            # Buscar cliente Stripe por email
            clientes = stripe.Customer.list(email=usuario.email).data
            if clientes:
                cliente = clientes[0]
            else:
                print(f"⚠ Cliente Stripe no encontrado para usuario {usuario.email}. Reserva {reserva.id} no procesada.")
                continue

            noches = (reserva.end_date - reserva.start_date).days + 1
            monto_total = reserva.price_per_night * noches

            if reserva.advance_payment:
                monto_a_cobrar = monto_total * 0.8
                descripcion = f"Pago restante (80%) de reserva #{reserva.id}"
            else:
                monto_a_cobrar = monto_total
                descripcion = f"Pago completo de reserva #{reserva.id}"

            cotizacion_usd = 1000  # Ajustá según tu cotización real
            monto_usd = int((monto_a_cobrar / cotizacion_usd) * 100)  # Stripe recibe centavos

            intento_pago = stripe.PaymentIntent.create(
                amount=monto_usd,
                currency="usd",
                customer=cliente.id,
                payment_method=usuario.stripe_payment_method_id,
                confirm=True,
                off_session=True,
                description=descripcion
            )

            if intento_pago.status == 'succeeded':
                reserva.status = 'confirmada'
                db.session.commit()
                print(f"✅ Pago exitoso | Reserva {reserva.id} | Localidad y Direccion {reserva.rental.property.localidad.nombre} {reserva.rental.property.direccion} | Monto: ${monto_a_cobrar:.2f}")
            else:
                print(f"❌ Error en pago | Reserva {reserva.id} | Estado: {intento_pago.status}")

        except stripe.error.CardError as e:
            print(f"💳 Error de tarjeta | Reserva {reserva.id} | Error: {e.user_message}")
            db.session.rollback()
        except Exception as e:
            print(f"⚠️ Error inesperado | Reserva {reserva.id} | Error: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("🚀 Iniciando procesamiento de pagos pendientes...")
        procesar_pagos_pendientes()
        print("🏁 Procesamiento completado.")
