"""Gera o jogo completo num único arquivo: tudo_em_seu_lugar.py.

O código fica dividido em partes em src/ (numeradas na ordem em que entram no
arquivo final) e os ativos ficam em assets/. Este script junta tudo e embute
imagens, fontes e sons em base64, para o jogo rodar com um arquivo só.

Uso:  python tools/build.py [saida.py]
"""
import base64
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")
ASSETS = os.path.join(RAIZ, "assets")


# ---------------- ativos em base64
def _dicionario(nome, itens):
    linhas = ["", "", f"{nome} = {{"]
    for chave, caminho in itens:
        b64 = base64.b64encode(open(caminho, "rb").read()).decode()
        linhas.append(f'    "{chave}": (')
        linhas += [f'        "{b64[i:i + 100]}"' for i in range(0, len(b64), 100)]
        linhas.append("    ),")
    linhas.append("}")
    return linhas


def _arquivos(pasta, extensoes):
    caminho = os.path.join(ASSETS, pasta)
    return [os.path.join(caminho, a) for a in sorted(os.listdir(caminho)) if a.lower().endswith(extensoes)]


def montar():
    # ---------------- código: partes de src/ na ordem numérica
    partes = sorted(a for a in os.listdir(SRC) if a[:2].isdigit() and a.endswith(".py"))
    codigo = "".join(open(os.path.join(SRC, p), encoding="utf-8").read() for p in partes)

    imagens = [(os.path.splitext(os.path.basename(c))[0], c) for c in _arquivos("imagens", (".jpg", ".png"))]
    fontes = [("maquina", os.path.join(ASSETS, "fontes", "SpecialElite-Regular.ttf")),
              ("pixel", os.path.join(ASSETS, "fontes", "PixelifySans[wght].ttf")),
              ("simbolos", os.path.join(ASSETS, "fontes", "Simbolos.ttf"))]
    sons = [(os.path.splitext(os.path.basename(c))[0], c) for c in _arquivos("sons", (".ogg",))]

    linhas = ["", "", "# Ilustrações da equipe (JPEG/PNG em base64)"]
    linhas += _dicionario("ASSETS", imagens)[2:]
    linhas += ["", "", "# Fontes: Special Elite (Apache 2.0), Pixelify Sans (OFL) e recorte do DejaVu Sans Bold"]
    linhas += _dicionario("FONTES", fontes)[2:]
    linhas += ["", "", "# Efeitos sonoros GRAVADOS (OGG), todos em domínio público (CC0 1.0):",
               "#  * Kenney (kenney.nl) — passos e trinco;  * wyzowl/sfx-kit — cliques, trovão, telefone,",
               "#    páginas, estática, impactos;  * coletânea CC0 lavenderdotpet/CC0-Public-Domain-Sounds —",
               "#    chuva, passos molhados, porta quebrando e latidos."]
    linhas += _dicionario("SONS_REAIS", sons)[2:]
    linhas.append('\n\nif __name__ == "__main__":\n    main()\n')
    return codigo + "\n".join(linhas)


if __name__ == "__main__":
    saida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "tudo_em_seu_lugar.py")
    with open(saida, "w", encoding="utf-8") as fh:
        fh.write(montar())
    print(f"Gerado: {saida} ({os.path.getsize(saida) / 1e6:.1f} MB)")
