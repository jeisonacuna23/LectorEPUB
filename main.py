from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.utils import platform
import os
import glob
import re
from ebooklib import epub

class BibliotecaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        titulo = Label(text='📚 Mi Biblioteca — Carpeta: Descargas', 
                       font_size='20sp', size_hint_y=None, height=50)
        self.layout.add_widget(titulo)
        
        btn_recargar = Button(text='🔄 Recargar Biblioteca', size_hint_y=None, height=50)
        btn_recargar.bind(on_press=self.cargar_libros)
        self.layout.add_widget(btn_recargar)
        
        scroll = ScrollView()
        self.grilla = GridLayout(cols=2, spacing=10, size_hint_y=None)
        self.grilla.bind(minimum_height=self.grilla.setter('height'))
        scroll.add_widget(self.grilla)
        self.layout.add_widget(scroll)
        
        self.add_widget(self.layout)
        self.cargar_libros()
    
    def obtener_carpeta_descargas(self):
        if platform == 'android':
            try:
                from android.storage import primary_external_storage_path
                ruta_base = primary_external_storage_path()
                return os.path.join(ruta_base, 'Descargas')
            except:
                return '/storage/emulated/0/Download'
        return os.path.expanduser('~/Downloads')
    
    def cargar_libros(self, *args):
        self.grilla.clear_widgets()
        carpeta = self.obtener_carpeta_descargas()
        
        if not os.path.exists(carpeta):
            self.grilla.add_widget(Label(text='❌ No se encontró la carpeta Descargas\nVerifica que exista',
                                         size_hint_y=None, height=150))
            return
        
        archivos = glob.glob(os.path.join(carpeta, '*.epub'))
        
        if not archivos:
            self.grilla.add_widget(Label(text='📭 No hay archivos EPUB en Descargas',
                                         size_hint_y=None, height=150))
            return
        
        for ruta in archivos:
            nombre = os.path.splitext(os.path.basename(ruta))[0]
            btn = Button(text=f'📖 {nombre}', size_hint_y=None, height=80)
            btn.bind(on_press=lambda inst, r=ruta: self.abrir_libro(r))
            self.grilla.add_widget(btn)
    
    def abrir_libro(self, ruta):
        self.manager.get_screen('lector').cargar_libro(ruta)
        self.manager.current = 'lector'

class LectorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ruta_libro = None
        self.contenido = []
        self.pagina_actual = 0
        
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        barra_sup = BoxLayout(size_hint_y=None, height=50, spacing=5)
        btn_volver = Button(text='⬅ Volver', on_press=lambda x: setattr(self.manager, 'current', 'biblioteca'))
        self.etiqueta_titulo = Label(text='', font_size='16sp')
        barra_sup.add_widget(btn_volver)
        barra_sup.add_widget(self.etiqueta_titulo)
        self.layout.add_widget(barra_sup)
        
        scroll = ScrollView()
        self.texto_label = Label(text='Selecciona un libro de la biblioteca', 
                                 font_size='18sp', text_size=(Window.width - 40, None),
                                 size_hint_y=None)
        self.texto_label.bind(texture_size=self.texto_label.setter('size'))
        scroll.add_widget(self.texto_label)
        self.layout.add_widget(scroll)
        
        barra_inf = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.btn_anterior = Button(text='◀ Anterior', on_press=self.pagina_anterior, disabled=True)
        self.etiqueta_pagina = Label(text='0 / 0')
        self.btn_siguiente = Button(text='Siguiente ▶', on_press=self.pagina_siguiente, disabled=True)
        barra_inf.add_widget(self.btn_anterior)
        barra_inf.add_widget(self.etiqueta_pagina)
        barra_inf.add_widget(self.btn_siguiente)
        self.layout.add_widget(barra_inf)
        
        self.add_widget(self.layout)
    
    def cargar_libro(self, ruta):
        self.ruta_libro = ruta
        self.pagina_actual = 0
        self.contenido = []
        
        try:
            libro = epub.read_epub(ruta)
            titulo = libro.get_metadata('DC', 'title')
            self.etiqueta_titulo.text = titulo[0][0] if titulo else "Libro sin título"
            
            for item in libro.get_items():
                if item.get_type() == 9:
                    contenido = item.get_content().decode('utf-8', errors='ignore')
                    contenido = re.sub(r'<script.*?</script>', '', contenido, flags=re.DOTALL|re.IGNORECASE)
                    contenido = re.sub(r'<style.*?</style>', '', contenido, flags=re.DOTALL|re.IGNORECASE)
                    contenido = re.sub(r'<[^>]+>', '\n', contenido)
                    contenido = re.sub(r'\n+', '\n', contenido).strip()
                    if len(contenido) > 30:
                        self.contenido.append(contenido)
            
            self.actualizar_vista()
            tiene_paginas = len(self.contenido) > 1
            self.btn_anterior.disabled = not tiene_paginas
            self.btn_siguiente.disabled = not tiene_paginas
            
        except Exception as e:
            self.texto_label.text = f'❌ Error al abrir el libro:\n{str(e)}'
    
    def actualizar_vista(self):
        if self.contenido:
            self.texto_label.text = self.contenido[self.pagina_actual]
            self.etiqueta_pagina.text = f'{self.pagina_actual + 1} / {len(self.contenido)}'
    
    def pagina_anterior(self, *args):
        if self.pagina_actual > 0:
            self.pagina_actual -= 1
            self.actualizar_vista()
    
    def pagina_siguiente(self, *args):
        if self.pagina_actual < len(self.contenido) - 1:
            self.pagina_actual += 1
            self.actualizar_vista()

class LectorEPUBApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(BibliotecaScreen(name='biblioteca'))
        sm.add_widget(LectorScreen(name='lector'))
        return sm
    
    def on_start(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.READ_EXTERNAL_STORAGE])
            except:
                pass

if __name__ == '__main__':
    LectorEPUBApp().run()
