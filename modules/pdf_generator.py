"""
Módulo de generación de reportes PDF para diseño de mezclas de concreto
Genera un informe profesional siguiendo el formato del Informe N° 936
con 6 páginas: portada, antecedentes, materiales, dosificación, gráficos y resumen.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Line

from datetime import datetime
from typing import Dict, List, Optional, Any
import io
import os


class PDFGenerator:
    """
    Generador de reportes PDF para diseño de mezclas de concreto.
    Sigue el formato del Informe N° 936.
    """
    
    def __init__(self, output_path: str = None):
        """
        Inicializa el generador de PDF.
        
        Args:
            output_path: Ruta del archivo PDF de salida
        """
        self.output_path = output_path
        self.buffer = io.BytesIO() if output_path is None else None
        self.styles = self._crear_estilos()
        self.page_width, self.page_height = letter
        
    def _crear_estilos(self) -> Dict:
        """Crea los estilos de párrafo personalizados."""
        styles = getSampleStyleSheet()
        
        # Título principal
        styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a1a1a')
        ))
        
        # Subtítulo
        styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=styles['Heading2'],
            fontSize=14,
            alignment=TA_LEFT,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#333333')
        ))
        
        # Sección
        styles.add(ParagraphStyle(
            name='Seccion',
            parent=styles['Heading3'],
            fontSize=12,
            alignment=TA_LEFT,
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2c3e50')
        ))
        
        # Texto normal
        styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        # Texto pequeño
        styles.add(ParagraphStyle(
            name='TextoPequeno',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
        
        # Texto centrado
        styles.add(ParagraphStyle(
            name='TextoCentrado',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Nota al pie
        styles.add(ParagraphStyle(
            name='NotaPie',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT,
            fontName='Helvetica-Oblique',
            textColor=colors.gray
        ))
        
        return styles
    
    def _crear_tabla_estilo_base(self) -> TableStyle:
        """Retorna el estilo base para tablas."""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ])
    
    def _pagina_1_portada(self, datos: Dict) -> List:
        """
        Genera la página 1: Portada con antecedentes generales y específicos.
        """
        elementos = []
        
        # Encabezado
        elementos.append(Paragraph("INFORME DE DOSIFICACIÓN DE HORMIGÓN", self.styles['TituloPrincipal']))
        elementos.append(Paragraph("Método Faury-Joisel con Análisis Shilstone", self.styles['TextoCentrado']))
        elementos.append(Spacer(1, 20))
        
        # Código de documento
        codigo = datos.get('codigo_documento', 'LAC-FC-13_3')
        elementos.append(Paragraph(f"Código: {codigo}", self.styles['TextoPequeno']))
        elementos.append(Spacer(1, 20))
        
        # Antecedentes Generales
        elementos.append(Paragraph("1. ANTECEDENTES GENERALES", self.styles['Subtitulo']))
        
        datos_generales = [
            ['Campo', 'Valor'],
            ['Informe N°', datos.get('numero_informe', 'S/N')],
            ['Solicitado por', datos.get('cliente', '-')],
            ['Dirigido a', datos.get('contacto', '-')],
            ['Obra', datos.get('obra', '-')],
            ['Fecha de Emisión', datos.get('fecha', datetime.now().strftime('%d/%m/%Y'))]
        ]
        
        tabla_general = Table(datos_generales, colWidths=[2.5*inch, 4*inch])
        tabla_general.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_general)
        elementos.append(Spacer(1, 20))
        
        # Antecedentes Específicos
        elementos.append(Paragraph("2. ANTECEDENTES ESPECÍFICOS DEL DISEÑO", self.styles['Subtitulo']))
        
        datos_especificos = [
            ['Parámetro', 'Valor', 'Unidad'],
            ['Código de Dosificación', datos.get('codigo_dosis', '-'), '-'],
            ['Resistencia Especificada (fc\')', f"{datos.get('fc', 30):.1f}", 'MPa'],
            ['Resistencia de Dosificación (fd)', f"{datos.get('fd', 35):.1f}", 'MPa'],
            ['Tipo de Áridos', datos.get('tipo_aridos', 'Chancado/Rodado/Arena'), '-'],
            ['Consistencia', datos.get('consistencia', 'Blanda'), '-'],
            ['Tipo de Cemento', datos.get('tipo_cemento', 'Portland Puzolánico'), '-'],
            ['Tamaño Máximo del Árido', f"{datos.get('tmn', 25)}", 'mm'],
            ['Fracción Defectuosa', f"{datos.get('fraccion_def', 0.10)*100:.0f}", '%'],
            ['Asentamiento', datos.get('asentamiento', '6 ± 2'), 'cm'],
            ['Contenido de Aire', f"{datos.get('aire_pct', 2.0):.1f}", '%']
        ]
        
        tabla_especifica = Table(datos_especificos, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        tabla_especifica.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_especifica)
        
        elementos.append(PageBreak())
        return elementos
    
    def _pagina_2_materiales(self, datos: Dict) -> List:
        """
        Genera la página 2: Caracterización de los áridos.
        """
        elementos = []
        
        elementos.append(Paragraph("3. CARACTERIZACIÓN DE LOS MATERIALES", self.styles['Subtitulo']))
        elementos.append(Spacer(1, 10))
        
        # Tabla de propiedades de áridos
        elementos.append(Paragraph("3.1 Propiedades Físicas de los Áridos", self.styles['Seccion']))
        
        aridos = datos.get('aridos', [])
        
        # Encabezado de propiedades
        prop_header = ['Propiedad', 'Unidad']
        for i, arido in enumerate(aridos):
            prop_header.append(arido.get('nombre', f'Árido {i+1}'))
        
        prop_data = [prop_header]
        
        # Densidad Real Seca
        fila_drs = ['Densidad Real Seca (DRS)', 'kg/m³']
        for arido in aridos:
            fila_drs.append(f"{arido.get('DRS', 0):.0f}")
        prop_data.append(fila_drs)
        
        # Densidad Real SSS
        fila_drsss = ['Densidad Real SSS', 'kg/m³']
        for arido in aridos:
            fila_drsss.append(f"{arido.get('DRSSS', 0):.0f}")
        prop_data.append(fila_drsss)
        
        # Absorción
        fila_abs = ['Absorción', '%']
        for arido in aridos:
            fila_abs.append(f"{arido.get('absorcion', 0)*100:.2f}")
        prop_data.append(fila_abs)
        
        col_widths = [2*inch, 1*inch] + [1.3*inch] * len(aridos)
        tabla_prop = Table(prop_data, colWidths=col_widths[:2+len(aridos)])
        tabla_prop.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_prop)
        elementos.append(Spacer(1, 20))
        
        # Tabla de granulometría
        elementos.append(Paragraph("3.2 Análisis Granulométrico (% que pasa)", self.styles['Seccion']))
        
        tamices = ['1½"', '1"', '¾"', '½"', '⅜"', 'Nº4', 'Nº8', 'Nº16', 'Nº30', 'Nº50', 'Nº100', 'Nº200']
        
        gran_header = ['Tamiz', 'mm']
        for i, arido in enumerate(aridos):
            gran_header.append(arido.get('nombre', f'Árido {i+1}')[:15])
        
        tamices_mm = [40, 25, 20, 12.5, 10, 5, 2.36, 1.18, 0.6, 0.315, 0.16, 0.08]
        
        gran_data = [gran_header]
        for i, (tamiz, mm) in enumerate(zip(tamices, tamices_mm)):
            fila = [tamiz, f"{mm}"]
            for arido in aridos:
                gran = arido.get('granulometria', [])
                valor = gran[i] if i < len(gran) else 0
                fila.append(f"{valor:.1f}")
            gran_data.append(fila)
        
        col_widths_gran = [0.8*inch, 0.7*inch] + [1.3*inch] * len(aridos)
        tabla_gran = Table(gran_data, colWidths=col_widths_gran[:2+len(aridos)])
        tabla_gran.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_gran)
        
        # Nota sobre cemento
        elementos.append(Spacer(1, 15))
        elementos.append(Paragraph("3.3 Cemento", self.styles['Seccion']))
        
        cemento_data = [
            ['Parámetro', 'Valor'],
            ['Tipo', datos.get('tipo_cemento', 'Portland Puzolánico')],
            ['Densidad', f"{datos.get('densidad_cemento', 3140)} kg/m³"],
        ]
        tabla_cemento = Table(cemento_data, colWidths=[2*inch, 3*inch])
        tabla_cemento.setStyle(self._crear_tabla_estilo_base())
        tabla_cemento.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_cemento)

        # Aditivos 
        aditivos_list = datos.get('aditivos_config', [])
        if aditivos_list:
            elementos.append(Spacer(1, 15))
            elementos.append(Paragraph("3.4 Aditivos", self.styles['Seccion']))
            
            ad_data = [['Nombre', 'Dosis (%)', 'Densidad (kg/L)']]
            for ad in aditivos_list:
                ad_data.append([
                    ad.get('nombre', '-'),
                    f"{ad.get('dosis_pct', 0):.2f}%",
                    f"{ad.get('densidad_kg_lt', 1):.2f}"
                ])
                
            tabla_ad = Table(ad_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            tabla_ad.setStyle(self._crear_tabla_estilo_base())
            elementos.append(tabla_ad)
        
        elementos.append(PageBreak())
        return elementos
    
    def _pagina_3_memoria_calculo(self, datos: Dict) -> List:
        """
        Genera la página 3: Memoria de cálculo del método Faury-Joisel.
        """
        elementos = []
        
        elementos.append(Paragraph("4. MEMORIA DE CÁLCULO - MÉTODO FAURY-JOISEL", self.styles['Subtitulo']))
        elementos.append(Spacer(1, 10))
        
        faury = datos.get('faury_joisel', {})
        
        # Descripción del método
        texto_intro = """El método Faury-Joisel permite diseñar mezclas de hormigón 
        optimizando la distribución granulométrica de los áridos para lograr una 
        compacidad máxima y las propiedades deseadas del hormigón fresco y endurecido."""
        elementos.append(Paragraph(texto_intro, self.styles['TextoNormal']))
        elementos.append(Spacer(1, 10))
        
        # Tabla de cálculos
        calc_data = [
            ['Paso', 'Descripción', 'Fórmula/Referencia', 'Valor', 'Unidad'],
            ['a)', 'Resistencia especificada', 'fc\'', f"{datos.get('fc', 30):.1f}", 'MPa'],
            ['b)', 'Desviación estándar', 's', f"{datos.get('desviacion_std', 4):.1f}", 'MPa'],
            ['c)', 'Coeficiente t', f"Fracción def. {datos.get('fraccion_def', 0.1)*100:.0f}%", 
             f"{faury.get('resistencia', {}).get('coef_t', 1.282):.3f}", '-'],
            ['d)', 'Resistencia media (fd)', 'fd = fc\' + s×t', 
             f"{faury.get('resistencia', {}).get('fd_mpa', 35):.1f}", 'MPa'],
            ['e)', 'Resistencia media', 'fd en kg/cm²', 
             f"{faury.get('resistencia', {}).get('fd_kgcm2', 360):.0f}", 'kg/cm²'],
            ['f)', 'Cantidad de cemento', 'C = fd × η', 
             f"{faury.get('cemento', {}).get('cantidad', 360):.0f}", 'kg/m³'],
            ['g)', 'Razón agua/cemento', 'Tabla según fd', 
             f"{faury.get('agua_cemento', {}).get('razon', 0.47):.3f}", '-'],
            ['h)', 'Agua de amasado', 'A = (A/C) × C', 
             f"{faury.get('agua_cemento', {}).get('agua_amasado', 170):.1f}", 'lt/m³'],
            ['i)', 'Aire ocluido', 'Tabla según TMN', 
             f"{faury.get('aire', {}).get('volumen', 35):.1f}", 'lt/m³'],
            ['j)', 'Compacidad', 'z = 1 - ha/1000 - A/1000', 
             f"{faury.get('compacidad', 0.79):.4f}", 'm³/m³'],
        ]
        
        tabla_calc = Table(calc_data, colWidths=[0.5*inch, 2*inch, 1.8*inch, 1*inch, 0.8*inch])
        estilo_calc = self._crear_tabla_estilo_base()
        estilo_calc.add('FONTSIZE', (0, 0), (-1, -1), 8)
        tabla_calc.setStyle(estilo_calc)
        elementos.append(tabla_calc)
        
        elementos.append(Spacer(1, 15))
        
        # Proporciones volumétricas
        elementos.append(Paragraph("4.1 Proporciones Volumétricas", self.styles['Seccion']))
        
        proporciones = faury.get('proporciones_volumetricas', {})
        prop_vol_data = [['Componente', 'Proporción Volumétrica']]
        for comp, valor in proporciones.items():
            prop_vol_data.append([comp.replace('_', ' ').title(), f"{valor:.4f}"])
        
        tabla_prop_vol = Table(prop_vol_data, colWidths=[2.5*inch, 2*inch])
        tabla_prop_vol.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_prop_vol)
        
        elementos.append(PageBreak())
        return elementos
    
    def _pagina_4_dosificacion(self, datos: Dict) -> List:
        """
        Genera la página 4: Dosificación final y proporciones.
        """
        elementos = []
        
        elementos.append(Paragraph("5. DOSIFICACIÓN FINAL", self.styles['Subtitulo']))
        elementos.append(Spacer(1, 10))
        
        faury = datos.get('faury_joisel', {})
        
        # Cantidades en kg/m³
        elementos.append(Paragraph("5.1 Cantidades por m³ de Hormigón", self.styles['Seccion']))
        
        cantidades = faury.get('cantidades_kg_m3', {})
        cant_data = [['Material', 'Cantidad', 'Unidad']]
        
        for material, cantidad in cantidades.items():
            cant_data.append([material.replace('_', ' ').title(), f"{cantidad:.1f}", 'kg'])
        
        # Agregar cemento y agua
        cant_data.append(['Cemento', f"{faury.get('cemento', {}).get('cantidad', 0):.0f}", 'kg'])
        cant_data.append(['Agua de amasado', f"{faury.get('agua_cemento', {}).get('agua_amasado', 0):.1f}", 'lt'])
        cant_data.append(['Agua de absorción', f"{faury.get('agua_cemento', {}).get('agua_absorcion', 0):.1f}", 'lt'])
        cant_data.append(['Agua de absorción', f"{faury.get('agua_cemento', {}).get('agua_absorcion', 0):.1f}", 'lt'])
        cant_data.append(['Agua total', f"{faury.get('agua_cemento', {}).get('agua_total', 0):.1f}", 'lt'])
        
        # Agregar Aditivos calculado
        aditivos_res = faury.get('aditivos', [])
        for ad in aditivos_res:
            cant_data.append([
                f"Aditivo: {ad['nombre']}", 
                f"{ad['cantidad_kg']:.2f}",
                'kg'
            ])


        
        tabla_cant = Table(cant_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        tabla_cant.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_cant)
        
        elementos.append(Spacer(1, 15))
        
        # Proporciones en peso
        elementos.append(Paragraph("5.2 Proporciones en Peso de Áridos", self.styles['Seccion']))
        
        prop_peso = faury.get('proporciones_peso', {})
        peso_data = [['Árido', 'Proporción', '%']]
        for arido, prop in prop_peso.items():
            peso_data.append([arido.replace('_', ' ').title(), f"{prop:.4f}", f"{prop*100:.1f}"])
        
        tabla_peso = Table(peso_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        tabla_peso.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_peso)
        
        elementos.append(Spacer(1, 15))
        
        # Banda de trabajo
        elementos.append(Paragraph("5.3 Banda de Trabajo Granulométrica", self.styles['Seccion']))
        
        tamices = ['1½"', '1"', '¾"', '½"', '⅜"', 'Nº4', 'Nº8', 'Nº16', 'Nº30', 'Nº50', 'Nº100', 'Nº200']
        mezcla = faury.get('granulometria_mezcla', [])
        banda = faury.get('banda_trabajo', [])
        
        banda_data = [['Tamiz', 'Mezcla %', 'Límite Inf.', 'Límite Sup.']]
        for i, tamiz in enumerate(tamices):
            if i < len(mezcla) and i < len(banda):
                banda_data.append([
                    tamiz, 
                    f"{mezcla[i]:.1f}", 
                    f"{banda[i][0]:.1f}",
                    f"{banda[i][1]:.1f}"
                ])
        
        tabla_banda = Table(banda_data, colWidths=[1*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        tabla_banda.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_banda)
        
        elementos.append(PageBreak())
        return elementos
    
    def _pagina_5_shilstone(self, datos: Dict, imagen_shilstone: bytes = None) -> List:
        """
        Genera la página 5: Análisis Shilstone con gráficos.
        """
        elementos = []
        
        elementos.append(Paragraph("6. ANÁLISIS SHILSTONE", self.styles['Subtitulo']))
        elementos.append(Spacer(1, 10))
        
        shilstone = datos.get('shilstone', {})
        
        # Descripción
        texto_shilstone = """El método Shilstone evalúa la trabajabilidad y cohesión 
        de la mezcla mediante el Coarseness Factor (CF) y el Workability Factor (W). 
        La posición en el gráfico indica la calidad de la gradación."""
        elementos.append(Paragraph(texto_shilstone, self.styles['TextoNormal']))
        elementos.append(Spacer(1, 10))
        
        # Cálculos Shilstone
        elementos.append(Paragraph("6.1 Parámetros Calculados", self.styles['Seccion']))
        
        shil_data = [
            ['Parámetro', 'Fórmula', 'Valor'],
            ['% Pasa 3/8"', '-', f"{shilstone.get('pasa_3_8', 0):.1f}"],
            ['% Pasa #8', '-', f"{shilstone.get('pasa_8', 0):.1f}"],
            ['Coarseness Factor (CF)', 'Q/(Q+I)×100', f"{shilstone.get('CF', 0):.1f}"],
            ['Workability Factor (W)', '% pasa #8', f"{shilstone.get('W', 0):.1f}"],
            ['Ajuste', '0.0588×Cc - 19.647', f"{shilstone.get('adj', 0):.2f}"],
            ['Wadj', 'W + Ajuste', f"{shilstone.get('Wadj', 0):.1f}"],
            ['Factor de Mortero (FM)', 'Volumen mortero', f"{shilstone.get('FM', 0):.1f} lt/m³"],
        ]
        
        tabla_shil = Table(shil_data, colWidths=[2*inch, 2*inch, 1.5*inch])
        tabla_shil.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_shil)
        
        elementos.append(Spacer(1, 15))
        
        # Evaluación
        elementos.append(Paragraph("6.2 Evaluación de la Mezcla", self.styles['Seccion']))
        
        evaluacion = shilstone.get('evaluacion', {})
        eval_data = [
            ['Aspecto', 'Resultado'],
            ['Zona', evaluacion.get('zona', '-')],
            ['Calidad', evaluacion.get('calidad', '-')],
            ['Descripción', evaluacion.get('descripcion', '-')[:80]],
        ]
        
        tabla_eval = Table(eval_data, colWidths=[1.5*inch, 4*inch])
        tabla_eval.setStyle(self._crear_tabla_estilo_base())
        elementos.append(tabla_eval)
        
        # Gráfico Shilstone si está disponible
        if imagen_shilstone:
            elementos.append(Spacer(1, 15))
            elementos.append(Paragraph("6.3 Gráfico Shilstone", self.styles['Seccion']))
            
            img_buffer = io.BytesIO(imagen_shilstone)
            img = Image(img_buffer, width=5*inch, height=4*inch)
            elementos.append(img)
        
        elementos.append(PageBreak())
        return elementos
    
    def _pagina_6_resumen(self, datos: Dict) -> List:
        """
        Genera la página 6: Resumen y conclusiones.
        """
        elementos = []
        
        elementos.append(Paragraph("7. RESUMEN DE DOSIFICACIÓN", self.styles['Subtitulo']))
        elementos.append(Spacer(1, 10))
        
        elementos.append(Paragraph(
            "Para 1 m³ de hormigón fresco a elaborar se requiere:",
            self.styles['TextoNormal']
        ))
        elementos.append(Spacer(1, 10))
        
        faury = datos.get('faury_joisel', {})
        cantidades = faury.get('cantidades_kg_m3', {})
        
        # Tabla resumen
        resumen_data = [['Material', 'Cantidad', 'Unidad']]
        
        for material, cantidad in cantidades.items():
            resumen_data.append([material.replace('_', ' ').title(), f"{cantidad:.1f}", 'kg'])
        
        resumen_data.append(['Cemento', f"{faury.get('cemento', {}).get('cantidad', 0):.0f}", 'kg'])
        resumen_data.append(['Cemento', f"{faury.get('cemento', {}).get('cantidad', 0):.0f}", 'kg'])
        resumen_data.append(['Agua Total', f"{faury.get('agua_cemento', {}).get('agua_total', 0):.1f}", 'lt'])
        
        aditivos_res = faury.get('aditivos', [])
        for ad in aditivos_res:
            resumen_data.append([ad['nombre'], f"{ad['cantidad_kg']:.2f}", 'kg'])

        
        tabla_resumen = Table(resumen_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
        estilo_resumen = self._crear_tabla_estilo_base()
        estilo_resumen.add('FONTSIZE', (0, 0), (-1, -1), 10)
        tabla_resumen.setStyle(estilo_resumen)
        elementos.append(tabla_resumen)
        
        elementos.append(Spacer(1, 20))
        
        # Conclusiones
        elementos.append(Paragraph("8. CONCLUSIONES Y RECOMENDACIONES", self.styles['Subtitulo']))
        elementos.append(Spacer(1, 10))
        
        shilstone = datos.get('shilstone', {})
        evaluacion = shilstone.get('evaluacion', {})
        
        # Generar conclusiones basadas en los resultados
        conclusiones = []
        
        calidad = evaluacion.get('calidad', 'Aceptable')
        if calidad == 'Óptima':
            conclusiones.append("• La mezcla diseñada presenta una gradación óptima según el análisis Shilstone.")
            conclusiones.append("• Se recomienda realizar mezclas de prueba para verificar las propiedades especificadas.")
        elif calidad == 'Aceptable':
            conclusiones.append("• La mezcla se encuentra en una zona aceptable del gráfico Shilstone.")
            conclusiones.append("• Se pueden realizar ajustes menores para mejorar el desempeño.")
        else:
            conclusiones.append("• La mezcla requiere ajustes en las proporciones de agregados.")
            for rec in evaluacion.get('recomendaciones', []):
                conclusiones.append(f"• {rec}")
        
        conclusiones.append("• Verificar las propiedades en estado fresco mediante ensayos de asentamiento.")
        conclusiones.append("• Monitorear la resistencia a compresión a 7 y 28 días.")
        
        for concl in conclusiones:
            elementos.append(Paragraph(concl, self.styles['TextoNormal']))
        
        elementos.append(Spacer(1, 30))
        
        # Pie de página
        elementos.append(Paragraph("_" * 80, self.styles['TextoCentrado']))
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph(
            f"Informe generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
            self.styles['NotaPie']
        ))
        elementos.append(Paragraph(
            "Aplicación de Diseño de Mezclas de Concreto - Método Faury-Joisel",
            self.styles['NotaPie']
        ))
        
        return elementos
    
    def generar_pdf(self, datos: Dict, imagen_shilstone: bytes = None) -> bytes:
        """
        Genera el PDF completo con todas las páginas.
        
        Args:
            datos: Diccionario con todos los datos del diseño
            imagen_shilstone: Imagen del gráfico Shilstone en bytes (opcional)
        
        Returns:
            PDF como bytes
        """
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Construir contenido
        elementos = []
        
        # Página 1: Portada
        elementos.extend(self._pagina_1_portada(datos))
        
        # Página 2: Materiales
        elementos.extend(self._pagina_2_materiales(datos))
        
        # Página 3: Memoria de cálculo
        elementos.extend(self._pagina_3_memoria_calculo(datos))
        
        # Página 4: Dosificación
        elementos.extend(self._pagina_4_dosificacion(datos))
        
        # Página 5: Shilstone
        elementos.extend(self._pagina_5_shilstone(datos, imagen_shilstone))
        
        # Página 6: Resumen
        elementos.extend(self._pagina_6_resumen(datos))
        
        # Generar PDF
        doc.build(elementos)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def guardar_pdf(self, datos: Dict, ruta: str, imagen_shilstone: bytes = None) -> bool:
        """
        Genera y guarda el PDF en un archivo.
        
        Args:
            datos: Diccionario con todos los datos del diseño
            ruta: Ruta donde guardar el PDF
            imagen_shilstone: Imagen del gráfico Shilstone (opcional)
        
        Returns:
            True si se guardó exitosamente
        """
        try:
            pdf_bytes = self.generar_pdf(datos, imagen_shilstone)
            with open(ruta, 'wb') as f:
                f.write(pdf_bytes)
            return True
        except Exception as e:
            print(f"Error al guardar PDF: {e}")
            return False


def generar_reporte_pdf(datos: Dict, imagen_shilstone: bytes = None) -> bytes:
    """
    Función de conveniencia para generar el reporte PDF.
    
    Args:
        datos: Diccionario con todos los datos del diseño
        imagen_shilstone: Imagen del gráfico Shilstone (opcional)
    
    Returns:
        PDF como bytes
    """
    generador = PDFGenerator()
    return generador.generar_pdf(datos, imagen_shilstone)
