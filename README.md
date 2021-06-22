# `AyED Tools`

**Usage**:

```console
$ ayed [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `coll`: Crea las funciones newT, TToString, etc. Para un struct T.
* `files`: Crea archivos .dat con los datos de un excel.

## `ayed coll`

Crea las funciones newT, TToString, TFromString, TToDebug para un struct T.

Por default, abre un editor en el que podrán escribir/copy-paste los structs.

Si ya tienen un archivo y no quieren que se abra el editor, pueden usar
-p o --path [PATH], siendo [PATH] el nombre del archivo.

**Usage**:

```console
$ ayed coll [OPTIONS]
```

**Options**:

* `-p, --path FILE`: La dirección del archivo .cpp[,.hpp,.c,.h] que contiene a los structs
* `--help`: Show this message and exit.

## `ayed files`

Por default, abre el excel `AlgoritmosFiles.xlsx` en la carpeta en la que
estén y lee todas sus solapas.

Si el excel está en otro lugar, pueden especificar la dirección del archivo.xlsx
después del nombre del programa,
ej: 
```console
$ ayed files home/bocanada/Documents/AlgoritmosFiles.xlsx.
```
Con -s o --sheet [SHEET] pueden especificar una solapa, siendo [SHEET] la solapa.

Si utilizan --no-read, el programa no leerá los archivos para mostrarlos.

**Usage**:

```console
$ ayed files [OPTIONS] [PATH]
```

**Arguments**:

* `[PATH]`: La dirección del .xlsx  [default: AlgoritmosFiles.xlsx]

**Options**:

* `-s, --sheet TEXT`: El nombre de la solapa/sheet
* `--read / --no-read`: Lee las estructuras guardadas en el .dat  [default: True]
* `--help`: Show this message and exit.
