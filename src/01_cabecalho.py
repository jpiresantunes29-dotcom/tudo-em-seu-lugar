# -*- coding: utf-8 -*-
"""
==========================================================================
  TUDO EM SEU LUGAR — Jogo de investigação em MODO HISTÓRIA
  Desenvolvido por João Pedro Pires Antunes

  COMO EXECUTAR
    1) Instale o pygame (uma vez só):   pip install pygame
    2) Rode:                            python tudo_em_seu_lugar.py
       (se o pygame faltar, o próprio jogo oferece instalar)
    Android: app Pydroid 3 → menu Pip → instale "pygame" → abra este arquivo e ▶.

  CONTROLES
    WASD / setas: andar      E / Espaço / Enter: interagir e avançar falas
    C: caderno de proposições   Q: quadro de suspeitas   H: dica
    X: arriscar acusação   TAB: mapa da cidade   M: som   ESC: pausa

  REGRAS (resumo)
    * A história segue em capítulos, na ordem do caso: o baile, o chamado de
      Sofia, a cena do crime, o passado da Tulane, a quinta aluna, a casa do
      professor e a revelação. O objetivo do capítulo aparece no topo.
    * A promotoria dá 48h desde o crime. Viajar custa 45 min, examinar 30 min,
      interrogar 45 min. Acabou o prazo: acusação obrigatória.
    * ESC abre a pausa: Salvar jogo, Salvar e sair, Sair sem salvar. O jogo
      também salva sozinho no início de cada capítulo; no menu principal,
      "Continuar caso salvo" retoma de onde parou.
    * Pistas dão pontos e revelam as PROPOSIÇÕES dos slides (A … AM).
    * Decisões: liberar ou acusar cada suspeita, pedir dica, arriscar a
      acusação a qualquer momento (errar custa pontos e credibilidade).
    * Final: acertar QUEM e POR QUÊ. Tela final com estatísticas e recordes.
    * Sorteio por partida (CÓDIGO DO CASO): nomes, roupas e características
      das alunas ruivas, álibis, traços da assassina nas câmeras, lugar das
      pistas, pistas falsas e eventos aleatórios.
    * Trilhas originais geradas pelo próprio código; efeitos gravados em
      domínio público (CC0). Créditos completos no README do repositório.

  Repositório: https://github.com/jpiresantunes29-dotcom/tudo-em-seu-lugar
==========================================================================
"""

import array
import base64
import datetime
import io
import json
import math
import os
import random
import struct
import sys
import tempfile
import threading
import time
import wave

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
try:
    import pygame
except ImportError:
    print("\nEste jogo precisa do pygame (biblioteca de jogos do Python).")
    try:
        resp = input("Instalar agora automaticamente? [S/n] ").strip().lower()
    except EOFError:
        resp = "n"
    if resp in ("", "s", "sim", "y", "yes"):
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
            import pygame
        except Exception:
            print("\nNão deu para instalar sozinho. Instale com:  pip install pygame")
            print("(No Windows:  py -m pip install pygame)\n")
            input("Aperte Enter para sair...")
            sys.exit(1)
    else:
        print("\nInstale com:  pip install pygame   (no Windows:  py -m pip install pygame)\n")
        input("Aperte Enter para sair...")
        sys.exit(1)

