Instalação da LogoVM
====================

LogoVM necessita, pelo menos, da versão 3.7 de Python e dos seguintes componentes:

* ply >= 3.11
* pillow >= 9.3.0

A forma recomendada de instalar a LogoVM é utilizando um _virtual environment_ do Python:

```
python -m venv /tmp/venv
. /tmp/venv/bin/activate
```

No ambiente virtual, faça uma istalação "viva" da LogoVM utilizando o `pip`, apontando para o diretório raiz do repositório da LogoVM:

```
pip install -e ~/Developer/logovm
```

Caso você deseje modificar a implementação da LogoVM, você precisará dos pacotes de desenvolvimento, então utilize, a partir do diretório raiz do repositório da LogoVM:

```
pip install -e .[dev]
```

Uma vez instalado, você poderá executar a LogoVM a partir do script `logovm`:

```
logovm examples/counter.lasm
```
