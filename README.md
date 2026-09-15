# Pipateka

Enciclopedia informativa en español sobre tabacos de pipa. El proyecto no vende ni facilita la compra de tabaco.

## Estado actual

- Sitio estático publicado con GitHub Pages.
- Catálogo local generado automáticamente a partir de las fuentes incorporadas al proyecto.
- Búsqueda por marca, nombre, tipo, país, fuerza, corte y aromatización cuando esos datos están disponibles.
- Fichas individuales de producto y páginas independientes por marca.
- Sección específica de Mac Baren con 131 fichas editoriales.
- Imágenes locales únicamente cuando se ha podido identificar una fuente adecuada; no se inventan asociaciones de imágenes.
- Registro, inicio de sesión y recuperación de contraseña mediante Supabase Auth.
- Newsletter mediante Supabase.
- Aviso 18+ y advertencia sanitaria.

## Datos

El catálogo local de esta versión contiene 657 mezclas cargadas de 122 marcas. TobaccoReviews se utiliza también como referencia externa de alcance; esa referencia no significa que Pipateka haya cargado automáticamente todas sus fichas.

Las valoraciones y metadatos públicos se usan como referencia. Pipateka redacta sus propias síntesis editoriales y no reproduce literalmente reseñas de terceros.

## Desarrollo

El despliegue se realiza mediante GitHub Actions y GitHub Pages. El workflow genera los catálogos, valida duplicados y fichas incompletas, persiste los datos generados y publica el artefacto final.

La autenticación y la newsletter requieren la configuración correspondiente del proyecto Supabase.
