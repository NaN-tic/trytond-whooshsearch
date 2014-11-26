=====================================
Whoosh. Indexación (Full Text Search)
=====================================

Whoosh es una librería de indexación y búsqueda. Nos permite generar distintos
esquemas (schemas) por cada modelo de nuestro ERP para después indexar contenidos
en él y hacer búsquedas.

Un ejemplo seria un esquema sobre productos y la indexación para la posterior
búsqueda de productos en él.

.. inheritref:: whooshsearch/whooshsearch:section:esquemas

Esquemas
--------

Un esquema está relacionado con un modelo y este contendrá varios campos que nos
permiten indexar.

Cada esquema irá relacionado con uno o varios idiomas. Por cada idioma, se genera
un esquema distinto. En el caso que no seleccione ningún idioma en esquema, se usará
el idioma por defecto el usuario.

En los esquemas disponemos del campo "Dominio" para filtrar registros que contengan
esta condición y sólo se indexen estos (filtro de que registros).

Por cada esquema le podemos añadir que grupos de usuarios tendrán acceso. Esto nos
permite en el asistente de "Buscar" sólo se nos mostrarán los esquemas según los
grupos del usuario.

Para crear o modificar un esquema deberemos accionar el botón "Crear esquema".

.. warning:: En el caso que hayamos eliminado registros (por ejemplo, eliminar o
             desactivar productos), el contenido del esquema no se han eliminado.
             En este caso, elimine el esquema, y vuelve a generar el esquema y
             posteriormente la generación de la indexación.

.. inheritref:: whooshsearch/whooshsearch:section:campos

Campos
------

En cada esquema seleccionaremos los campos que desearemos que se incluyen. Cada campo
podemos usar un nombre distinto en nuestro esquema si lo deseamos. Por ejemplo, en
comercio electrónico, el campo "name" lo podemos renombrar como "title" y el campo
"description" lo podemos renombrar como "content".

En un esquema como mínimo seleccionaremos un campo "Parser" que se usara como campo
para la búsqueda.

.. inheritref:: whooshsearch/whooshsearch:section:buscar

Buscar
------

Disponemos de un asistente para hacer búsquedas. En el asistente seleccionamos que
esquema deseamos buscar y el texto a buscar.

Podemos usar el signo "+" para unir palabras en la búsqueda (AND) y podemos
usar el signo "-" para omitir palabras (NOT).
