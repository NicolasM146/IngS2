from datetime import datetime, timedelta, date
from src.core.database import db
from src.core.Reserva.reservation import Reservation
from src.core.Alquiler.Rental import Rental
import stripe
import os
from dotenv import load_dotenv

# Configuración de Stripe
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def procesar_pagos_pendientes():
    """Cobra el pago faltante 1 día antes del check-in"""
    hoy = date.today()
    fecha_mañana = hoy + timedelta(days=1)
    
    # Buscar reservas que comienzan mañana y están pendientes
    reservas_pendientes = Reservation.query.filter(
        Reservation.start_date == fecha_mañana,
        Reservation.status == 'pending'  # Solo reservas en estado inicial
    ).all()
    
    for reserva in reservas_pendientes:
        try:
            alquiler = Rental.query.get(reserva.rental_id)
            usuario = reserva.user
            
            if not usuario.stripe_payment_method_id:
                print(f"Usuario {usuario.id} sin método de pago. Reserva {reserva.id} no procesada.")
                continue
                
            # Cálculo de estadía (consistente con /alquilar)
            noches = (reserva.end_date - reserva.start_date).days + 1
            monto_total = reserva.price_per_night * noches
            
            # Lógica de pagos (adaptada a tu flujo actual)
            if reserva.advance_payment:
                # Asume que el 20% YA se pagó al crear la reserva (según tu código)
                monto_a_cobrar = monto_total * 0.8  # Cobrar 80% restante
                descripcion = "Pago restante (80%) de reserva"
            else:
                # advance_payment=False → cobrar 100%
                monto_a_cobrar = monto_total
                descripcion = "Pago completo de reserva"
            
            # Conversión a USD (ajusta la cotización según necesites)
            cotizacion_usd = 1000
            monto_usd = int((monto_a_cobrar / cotizacion_usd) * 100)
            
            # Procesar pago
            intento_pago = stripe.PaymentIntent.create(
                amount=monto_usd,
                currency="usd",
                payment_method=usuario.stripe_payment_method_id,
                confirm=True,
                off_session=True,
                description=f"{descripcion} {reserva.id}"
            )
            
            if intento_pago.status == 'succeeded':
                reserva.status = 'confirmed'
                db.session.commit()
                print(f"✅ Pago exitoso | Reserva: {reserva.id} | Monto: ${monto_a_cobrar:.2f}")
            else:
                print(f"❌ Error en pago | Reserva: {reserva.id} | Estado: {intento_pago.status}")
                
        except stripe.error.CardError as e:
            print(f"💳 Error de tarjeta | Reserva: {reserva.id} | Error: {e.user_message}")
            db.session.rollback()
        except Exception as e:
            print(f"⚠️ Error inesperado | Reserva: {reserva.id} | Error: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    print("🚀 Iniciando procesamiento de pagos pendientes...")
    procesar_pagos_pendientes()
    print("🏁 Procesamiento completado.")