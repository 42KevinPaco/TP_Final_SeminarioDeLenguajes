// Datos hardcodeados - Listo para reemplazar con modelos/servicios
const productosHardcode = [
    {
        idProducto: 1,
        nombre: "Leche Entera",
        descripcion: "Leche entera pasteurizada 1L",
        precio: 150.00,
        marca: "La Serenísima"
    },
    {
        idProducto: 2,
        nombre: "Pan Lactal",
        descripcion: "Pan lactal blanco 500g",
        precio: 200.00,
        marca: "Bimbo"
    },
    {
        idProducto: 3,
        nombre: "Arroz",
        descripcion: "Arroz largo fino 1kg",
        precio: 120.00,
        marca: "Gallo"
    }
];

const sucursalesHardcode = [
    {
        idSucursal: 1,
        nombre: "Sucursal Centro",
        direccion: "Av. Principal 123",
        latitud: -34.6037,
        longitud: -58.3816
    },
    {
        idSucursal: 2,
        nombre: "Sucursal Norte",
        direccion: "Calle Norte 456",
        latitud: -34.5950,
        longitud: -58.3800
    },
    {
        idSucursal: 3,
        nombre: "Sucursal Sur",
        direccion: "Av. Sur 789",
        latitud: -34.6200,
        longitud: -58.4000
    }
];

const stockPorSucursalHardcode = [
    { idStock: 1, idProducto: 1, idSucursal: 1, cantidadDisponible: 50 },
    { idStock: 2, idProducto: 2, idSucursal: 1, cantidadDisponible: 30 },
    { idStock: 3, idProducto: 1, idSucursal: 2, cantidadDisponible: 20 }
];
