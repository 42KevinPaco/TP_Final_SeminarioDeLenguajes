"""Domain model tests: rules, composition and polymorphism."""

import unittest
from datetime import date

from app.models.carrito import CarritoCompra, ItemCarrito
from app.models.compra import Compra, DetalleCompra
from app.models.pago import PagoCredito, PagoDebito, PagoEfectivo
from app.models.producto import Producto
from app.models.sucursal import StockSucursal, Sucursal


def make_producto(id_producto: int = 1, precio: float = 150.0) -> Producto:
    return Producto(
        id_producto=id_producto,
        nombre="Leche Entera",
        descripcion="Leche entera 1L",
        precio=precio,
        marca="La Serenisima",
    )


class ProductoTest(unittest.TestCase):
    def test_rejects_non_positive_price(self):
        with self.assertRaises(ValueError):
            make_producto(precio=0)

    def test_rejects_blank_name(self):
        with self.assertRaises(ValueError):
            Producto(1, "   ", "desc", 10.0, "Marca")


class CarritoTest(unittest.TestCase):
    def test_adding_same_product_merges_into_one_line(self):
        carrito = CarritoCompra(1)
        producto = make_producto()

        carrito.agregar_producto(producto, 2)
        carrito.agregar_producto(producto, 3)

        self.assertEqual(len(carrito.items), 1)
        self.assertEqual(carrito.cantidad_items, 5)
        self.assertEqual(carrito.calcular_total(), 750.0)

    def test_item_subtotal_and_quantity_rules(self):
        item = ItemCarrito.desde_producto(make_producto(precio=100.0), 3)
        self.assertEqual(item.subtotal, 300.0)
        with self.assertRaises(ValueError):
            item.modificar_cantidad(0)

    def test_removing_and_clearing(self):
        carrito = CarritoCompra(1)
        carrito.agregar_producto(make_producto(1), 1)
        carrito.agregar_producto(make_producto(2), 2)

        carrito.eliminar_producto(1)
        self.assertEqual(len(carrito.items), 1)
        self.assertEqual(carrito.calcular_total(), 300.0)

        carrito.vaciar_carrito()
        self.assertEqual(carrito.items, [])
        self.assertEqual(carrito.calcular_total(), 0.0)


class StockTest(unittest.TestCase):
    def test_descontar_stock_updates_quantity(self):
        stock = StockSucursal(1, 1, 1, 5)
        stock.descontar_stock(2)
        self.assertEqual(stock.cantidad_disponible, 3)

    def test_descontar_stock_rejects_insufficient_quantity(self):
        stock = StockSucursal(1, 1, 1, 1)
        with self.assertRaises(ValueError):
            stock.descontar_stock(2)

    def test_negative_quantity_is_rejected(self):
        with self.assertRaises(ValueError):
            StockSucursal(1, 1, 1, -1)


class SucursalTest(unittest.TestCase):
    def test_distance_to_same_point_is_zero(self):
        sucursal = Sucursal(1, "Centro", "Av 1", -34.6037, -58.3816)
        self.assertAlmostEqual(sucursal.distancia_km(-34.6037, -58.3816), 0.0, places=6)

    def test_distance_is_positive_for_different_points(self):
        sucursal = Sucursal(1, "Centro", "Av 1", -34.6037, -58.3816)
        self.assertGreater(sucursal.distancia_km(-34.6200, -58.4000), 0.0)


class PagoTest(unittest.TestCase):
    def test_cash_payment_returns_change(self):
        pago = PagoEfectivo(1, 300.0, monto_recibido=500.0)
        resultado = pago.procesar_pago()
        self.assertTrue(resultado.aprobado)
        self.assertEqual(resultado.vuelto, 200.0)

    def test_cash_payment_rejected_when_not_enough_money(self):
        pago = PagoEfectivo(1, 300.0, monto_recibido=100.0)
        resultado = pago.procesar_pago()
        self.assertFalse(resultado.aprobado)
        self.assertEqual(pago.estado, "rechazado")

    def test_debit_card_requires_valid_data(self):
        valida = PagoDebito(
            1,
            300.0,
            numero_tarjeta="4111111111111111",
            titular="ANA GOMEZ",
            vencimiento="12/99",
            cvv="123",
        )
        self.assertTrue(valida.procesar_pago().aprobado)

        invalida = PagoDebito(2, 300.0, numero_tarjeta="123", titular="", vencimiento="01/20", cvv="1")
        self.assertFalse(invalida.procesar_pago().aprobado)

    def test_credit_card_keeps_installments(self):
        pago = PagoCredito(
            1,
            900.0,
            numero_tarjeta="4111111111111111",
            titular="ANA GOMEZ",
            vencimiento="12/99",
            cvv="123",
            cuotas=3,
        )
        resultado = pago.procesar_pago()
        self.assertTrue(resultado.aprobado)
        self.assertIn("3 cuota", resultado.mensaje)

    def test_credit_card_rejects_zero_installments(self):
        pago = PagoCredito(
            1,
            900.0,
            numero_tarjeta="4111111111111111",
            titular="ANA GOMEZ",
            vencimiento="12/99",
            cvv="123",
            cuotas=0,
        )
        self.assertFalse(pago.procesar_pago().aprobado)


class CompraTest(unittest.TestCase):
    def test_building_a_purchase_from_a_cart_snapshots_prices(self):
        carrito = CarritoCompra(1)
        carrito.agregar_producto(make_producto(precio=150.0), 2)

        compra = Compra.desde_carrito(1, 10, 1, carrito)

        self.assertEqual(len(compra.detalles), 1)
        self.assertEqual(compra.calcular_total(), 300.0)
        self.assertEqual(compra.detalles[0].precio_unitario, 150.0)

    def test_empty_cart_cannot_become_a_purchase(self):
        with self.assertRaises(ValueError):
            Compra.desde_carrito(1, 10, 1, CarritoCompra(1))

    def test_confirming_validates_payment(self):
        carrito = CarritoCompra(1)
        carrito.agregar_producto(make_producto(precio=100.0), 1)
        pago = PagoEfectivo(1, 100.0, monto_recibido=100.0)
        compra = Compra.desde_carrito(1, 10, 1, carrito, pago)

        compra.confirmar_compra()
        self.assertEqual(compra.estado, "confirmada")

    def test_detalle_subtotal(self):
        detalle = DetalleCompra(1, "Leche", 3, 50.0)
        self.assertEqual(detalle.subtotal, 150.0)
        self.assertEqual(detalle.calcular_subtotal(), 150.0)


if __name__ == "__main__":
    unittest.main()
