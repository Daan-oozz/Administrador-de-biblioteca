#Implementación de historias de usuario - Alejandro

import sqlite3
import datetime
from collections import defaultdict


# Conexión a la base de datos SQLite
def conectar_db():
    conn = sqlite3.connect('biblioteca.db')
    c = conn.cursor()
    # Crear tablas si no existen
    c.execute('''CREATE TABLE IF NOT EXISTS libros (
                 isbn TEXT, titulo TEXT PRIMARY KEY, autor TEXT,
                 editorial TEXT, año INTEGER, cantidad INTEGER,
                 cantidad_inicial INTEGER, categoria TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                 id_usuario TEXT PRIMARY KEY, nombre TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS prestamos (
                 id_usuario TEXT, titulo TEXT, fecha TEXT,
                 FOREIGN KEY(id_usuario) REFERENCES usuarios(id_usuario),
                 FOREIGN KEY(titulo) REFERENCES libros(titulo))''')
    c.execute('''CREATE TABLE IF NOT EXISTS editoriales (
                 nombre TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS categorias (
                 nombre TEXT PRIMARY KEY)''')
    conn.commit()
    return conn

# Clase para nodos del árbol binario de búsqueda
class NodoArbol:
    def __init__(self, clave, **datos):
        self.clave = clave
        self.datos = datos
        self.izquierda = None
        self.derecha = None

# Clase para el árbol binario de búsqueda
class ArbolBST:
    def __init__(self):
        self.raiz = None

    def insertar(self, clave, **datos):
        if not self.raiz:
            self.raiz = NodoArbol(clave, **datos)
        else:
            self._insertar_recursivo(self.raiz, clave, **datos)

    def _insertar_recursivo(self, nodo, clave, **datos):
        if clave < nodo.clave:
            if nodo.izquierda is None:
                nodo.izquierda = NodoArbol(clave, **datos)
            else:
                self._insertar_recursivo(nodo.izquierda, clave, **datos)
        else:
            if nodo.derecha is None:
                nodo.derecha = NodoArbol(clave, **datos)
            else:
                self._insertar_recursivo(nodo.derecha, clave, **datos)

    def buscar(self, clave):
        return self._buscar_recursivo(self.raiz, clave)

    def _buscar_recursivo(self, nodo, clave):
        if nodo is None or nodo.clave == clave:
            return nodo
        if clave < nodo.clave:
            return self._buscar_recursivo(nodo.izquierda, clave)
        return self._buscar_recursivo(nodo.derecha, clave)

    def eliminar(self, clave):
        self.raiz = self._eliminar_recursivo(self.raiz, clave)

    def _eliminar_recursivo(self, nodo, clave):
        if nodo is None:
            return nodo
        if clave < nodo.clave:
            nodo.izquierda = self._eliminar_recursivo(nodo.izquierda, clave)
        elif clave > nodo.clave:
            nodo.derecha = self._eliminar_recursivo(nodo.derecha, clave)
        else:
            if nodo.izquierda is None:
                return nodo.derecha
            elif nodo.derecha is None:
                return nodo.izquierda
            temp = self._minimo_nodo(nodo.derecha)
            nodo.clave = temp.clave
            nodo.datos = temp.datos
            nodo.derecha = self._eliminar_recursivo(nodo.derecha, temp.clave)
        return nodo

    def _minimo_nodo(self, nodo):
        actual = nodo
        while actual.izquierda:
            actual = actual.izquierda
        return actual

# Clase para el grafo
class Grafo:
    def __init__(self):
        self.grafo = defaultdict(list)

    def agregar_nodo(self, nodo):
        if nodo not in self.grafo:
            self.grafo[nodo] = []

    def agregar_arista(self, origen, destino):
        self.grafo[origen].append(destino)

    def eliminar_arista(self, origen, destino):
        if destino in self.grafo[origen]:
            self.grafo[origen].remove(destino)

    def recomendar_libros(self, id_usuario):
        recomendaciones = set()
        # Encontrar usuarios con préstamos similares
        for usuario in self.grafo:
            if usuario != id_usuario and usuario.startswith("U"):
                libros_comunes = set(self.grafo[usuario]) & set(self.grafo[id_usuario])
                if libros_comunes:
                    recomendaciones.update(set(self.grafo[usuario]) - set(self.grafo[id_usuario]))
        return list(recomendaciones)

class Biblioteca:
    def __init__(self):
        self.conn = conectar_db()
        self.pila_libros = []
        self.arbol_libros = ArbolBST()
        self.arbol_usuarios = ArbolBST()
        self.prestamos = []
        self.grafo = Grafo()
        self.cargar_datos()

    def cargar_datos(self):
        c = self.conn.cursor()
        # Cargar libros
        c.execute("SELECT isbn, titulo, autor, editorial, año, cantidad, cantidad_inicial, categoria FROM libros")
        for row in c.fetchall():
            isbn, titulo, autor, editorial, año, cantidad, cantidad_inicial, categoria = row
            self.pila_libros.append({
                'isbn': isbn, 'titulo': titulo, 'autor': autor, 'editorial': editorial,
                'año': año, 'cantidad': cantidad, 'cantidad_inicial': cantidad_inicial,
                'categoria': categoria
            })
            self.arbol_libros.insertar(titulo, isbn=isbn, autor=autor, editorial=editorial,
                                      año=año, cantidad=cantidad, categoria=categoria)
            self.grafo.agregar_nodo(titulo)

        # Cargar usuarios
        c.execute("SELECT id_usuario, nombre FROM usuarios")
        for row in c.fetchall():
            id_usuario, nombre = row
            self.arbol_usuarios.insertar(id_usuario, nombre=nombre)
            self.grafo.agregar_nodo(id_usuario)

        # Cargar préstamos y actualizar grafo
        c.execute("SELECT id_usuario, titulo, fecha FROM prestamos")
        for row in c.fetchall():
            id_usuario, titulo, fecha = row
            self.prestamos.append({'id_usuario': id_usuario, 'titulo': titulo, 'fecha': fecha})
            self.grafo.agregar_arista(id_usuario, titulo)

        # Cargar editoriales y categorías
        c.execute("INSERT OR IGNORE INTO editoriales (nombre) VALUES (?)", ("Desconocida",))
        c.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", ("Sin categoría",))
        self.conn.commit()

    def guardar_datos(self):
        c = self.conn.cursor()
        # Guardar libros
        c.execute("DELETE FROM libros")
        for libro in self.pila_libros:
            c.execute("INSERT INTO libros (isbn, titulo, autor, editorial, año, cantidad, cantidad_inicial, categoria) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (libro['isbn'], libro['titulo'], libro['autor'], libro['editorial'],
                       libro['año'], libro['cantidad'], libro['cantidad_inicial'], libro['categoria']))

        # Guardar usuarios
        c.execute("DELETE FROM usuarios")
        def recorrer_usuarios(nodo):
            if nodo:
                c.execute("INSERT INTO usuarios (id_usuario, nombre) VALUES (?, ?)",
                          (nodo.clave, nodo.datos['nombre']))
                recorrer_usuarios(nodo.izquierda)
                recorrer_usuarios(nodo.derecha)
        recorrer_usuarios(self.arbol_usuarios.raiz)

        # Guardar préstamos
        c.execute("DELETE FROM prestamos")
        for prestamo in self.prestamos:
            c.execute("INSERT INTO prestamos (id_usuario, titulo, fecha) VALUES (?, ?, ?)",
                      (prestamo['id_usuario'], prestamo['titulo'], prestamo['fecha']))

        self.conn.commit()

    def registrar_libro(self, isbn, titulo, autor, editorial, año, cantidad, categoria):
        for l in self.pila_libros:
            if l['titulo'].lower() == titulo.lower():
                print(f"El libro '{titulo}' ya está registrado.")
                return    
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO editoriales (nombre) VALUES (?)", (editorial,))
        c.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (categoria,))
        self.conn.commit()

        libro = {
            'isbn': isbn, 'titulo': titulo, 'autor': autor, 'editorial': editorial,
            'año': año, 'cantidad': cantidad, 'cantidad_inicial': cantidad, 'categoria': categoria
        }
        self.pila_libros.append(libro)
        self.arbol_libros.insertar(titulo, isbn=isbn, autor=autor, editorial=editorial,
                                  año=año, cantidad=cantidad, categoria=categoria)
        self.grafo.agregar_nodo(titulo)
        self.guardar_datos()
        print(f"Libro '{titulo}' registrado con {cantidad} ejemplares.")

    def registrar_usuario(self, id_usuario, nombre):
        if self.arbol_usuarios.buscar(id_usuario):
            print(f"El usuario con ID '{id_usuario}' ya existe.")
            return
        self.arbol_usuarios.insertar(id_usuario, nombre=nombre)
        self.grafo.agregar_nodo(id_usuario)
        self.guardar_datos()
        print(f"Usuario '{nombre}' con ID '{id_usuario}' registrado.")

    def prestar_libro(self, id_usuario, titulo):
        usuario = self.arbol_usuarios.buscar(id_usuario)
        if not usuario:
            print(f"Usuario con ID '{id_usuario}' no existe.")
            return
        for libro in self.pila_libros:
            if libro['titulo'].lower() == titulo.lower():
                if libro['cantidad'] > 0:
                    libro['cantidad'] -= 1
                    self.prestamos.append({
                        'id_usuario': id_usuario,
                        'titulo': titulo,
                        'fecha': str(datetime.datetime.now())
                    })
                    self.grafo.agregar_arista(id_usuario, titulo)
                    self.guardar_datos()
                    print(f"Libro '{titulo}' prestado a usuario {id_usuario}. Quedan {libro['cantidad']}/{libro['cantidad_inicial']}.")
                    return
                else:
                    print(f"No hay ejemplares disponibles de '{titulo}'.")
                    return
        print(f"El libro '{titulo}' no está en la biblioteca.")

    def devolver_libro(self, id_usuario, titulo):
        usuario = self.arbol_usuarios.buscar(id_usuario)
        if not usuario:
            print(f"Usuario con ID '{id_usuario}' no existe.")
            return
        for prestamo in self.prestamos:
            if prestamo['id_usuario'] == id_usuario and prestamo['titulo'].lower() == titulo.lower():
                for libro in self.pila_libros:
                    if libro['titulo'].lower() == titulo.lower():
                        if libro['cantidad'] < libro['cantidad_inicial']:
                            libro['cantidad'] += 1
                            self.prestamos.remove(prestamo)
                            self.grafo.eliminar_arista(id_usuario, titulo)
                            self.guardar_datos()
                            print(f"Libro '{titulo}' devuelto por usuario {id_usuario}. Ahora hay {libro['cantidad']}/{libro['cantidad_inicial']}.")
                            return
                        else:
                            print(f"Ya hay todos los ejemplares de '{titulo}' disponibles.")
                            return
        print(f"No se encontró un préstamo de '{titulo}' para el usuario {id_usuario}.")

    def mostrar_inventario(self):
        if not self.pila_libros:
            print("No hay libros registrados.")
        else:
            print("Inventario de la biblioteca:")
            for libro in reversed(self.pila_libros):
                print(f"- {libro['titulo']} ({libro['isbn']}) por {libro['autor']}, {libro['editorial']}, {libro['año']}, Categoría: {libro['categoria']}: {libro['cantidad']}/{libro['cantidad_inicial']}.")

    def buscar_libro_arbol(self, titulo):
        nodo = self.arbol_libros.buscar(titulo)
        if nodo:
            print(f"Libro encontrado: '{nodo.clave}' ({nodo.datos['isbn']}) por {nodo.datos['autor']}, {nodo.datos['editorial']}, {nodo.datos['año']}, Categoría: {nodo.datos['categoria']}. Disponibles: {nodo.datos['cantidad']}.")
        else:
            print(f"El libro '{titulo}' no está en la biblioteca.")

    def eliminar_libro(self, titulo):
        for libro in self.pila_libros:
            if libro['titulo'].lower() == titulo.lower():
                self.pila_libros.remove(libro)
                self.arbol_libros.eliminar(titulo)
                # Eliminar aristas asociadas al libro
                for usuario in self.grafo.grafo:
                    if usuario.startswith("U") and titulo in self.grafo.grafo[usuario]:
                        self.grafo.eliminar_arista(usuario, titulo)
                self.guardar_datos()
                print(f"Libro '{titulo}' eliminado de la biblioteca.")
                return
        print(f"El libro '{titulo}' no está en la biblioteca.")

    def recomendar_libros(self, id_usuario):
        recomendaciones = self.grafo.recomendar_libros(id_usuario)
        if recomendaciones:
            print(f"Libros recomendados para el usuario {id_usuario}:")
            for libro in recomendaciones:
                print(f"- {libro}")
        else:
            print(f"No hay recomendaciones disponibles para el usuario {id_usuario}.")

def main():
    biblioteca = Biblioteca()
    while True:
        print("\n=== Sistema de Gestión de Biblioteca ArboLib ===")
        print("1. Registrar libro")
        print("2. Registrar usuario")
        print("3. Prestar libro")
        print("4. Devolver libro")
        print("5. Mostrar inventario")
        print("6. Buscar libro (usando árbol)")
        print("7. Eliminar libro")
        print("8. Buscar recomendaciones (usando grafo)")
        print("9. Salir")
        opcion = input("Elige una opción: ")

        if opcion == "1":
            try:
                titulo = input("Ingresa el título del libro: ")
                autor = input("Ingresa el autor del libro: ")
                isbn = input("Ingresa el ISBN del libro: ")
                editorial = input("Ingresa la editorial del libro: ")
                año = int(input("Ingresa el año de publicación: "))
                cantidad = int(input("Ingresa la cantidad de ejemplares: "))
                categoria = input("Ingresa la categoría del libro: ")
                if cantidad < 0 or año < 0:
                    print("La cantidad y el año deben ser positivos.")
                else:
                    biblioteca.registrar_libro(isbn, titulo, autor, editorial, año, cantidad, categoria)
            except ValueError:
                print("Error: Ingresa números válidos para año y cantidad.")
        elif opcion == "2":
            id_usuario = input("Ingresa el ID del usuario: ")
            nombre = input("Ingresa el nombre del usuario: ")
            biblioteca.registrar_usuario(id_usuario, nombre)
        elif opcion == "3":
            id_usuario = input("Ingresa el ID del usuario: ")
            titulo = input("Ingresa el título del libro a prestar: ")
            biblioteca.prestar_libro(id_usuario, titulo)
        elif opcion == "4":
            id_usuario = input("Ingresa el ID del usuario: ")
            titulo = input("Ingresa el título del libro a devolver: ")
            biblioteca.devolver_libro(id_usuario, titulo)
        elif opcion == "5":
            biblioteca.mostrar_inventario()
        elif opcion == "6":
            titulo = input("Ingresa el título del libro a buscar: ")
            biblioteca.buscar_libro_arbol(titulo)
        elif opcion == "7":
            titulo = input("Ingresa el título del libro a eliminar: ")
            biblioteca.eliminar_libro(titulo)
        elif opcion == "8":
            id_usuario = input("Ingresa el ID del usuario para recomendaciones: ")
            biblioteca.recomendar_libros(id_usuario)
        elif opcion == "9":
            print("Saliendo del programa...")
            biblioteca.conn.close()
            break
        else:
            print("Opción no válida, intenta otra vez.")

if __name__ == "__main__":
    main()