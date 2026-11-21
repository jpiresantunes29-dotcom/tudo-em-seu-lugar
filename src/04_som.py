
# =========================================================================
# 2.5) SOM — trilha e efeitos ORIGINAIS, sintetizados pelo próprio código
#      (clima de thriller de série: piano esparso, drones graves, pulso
#      tenso, tique-taque e batimentos). Nada é baixado nem copiado:
#      os arquivos .wav são gerados na primeira execução e guardados na
#      pasta temporária. Sem som disponível, o jogo funciona em silêncio.
# =========================================================================

import array
import math
import struct
import subprocess
import tempfile
import threading
import wave

VERSAO_SOM = "v3"
SR_MUSICA = 16000
SR_SFX = 22050


def _nota(n):
    """Nome da nota -> frequência (ex.: 'D4', 'A#3')."""
    nomes = {"C": 0, "C#": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6,
             "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
    nome, oit = n[:-1], int(n[-1])
    semis = nomes[nome] + (oit + 1) * 12
    return 440.0 * 2 ** ((semis - 69) / 12.0)


class Sintetizador:
    """Mini-sintetizador em Python puro (só biblioteca padrão)."""

    def __init__(self, segundos, sr):
        self.sr = sr
        self.n = int(segundos * sr)
        self.b = [0.0] * self.n
        self.rng = random.Random(7)

    def _faixa(self, t0, dur):
        i0 = max(0, int(t0 * self.sr))
        i1 = min(self.n, int((t0 + dur) * self.sr))
        return i0, i1

    def tom(self, t0, dur, freq, amp, harm=(1.0,), ataque=0.01, decai=None,
            liberar=0.05, vibrato=0.0, glide=None):
        """Oscilador com harmônicos e envelope (decai = decaimento exponencial)."""
        b, sr = self.b, self.sr
        i0, i1 = self._faixa(t0, dur)
        tw = 2 * math.pi
        fase = 0.0
        total = i1 - i0
        for k in range(total):
            t = k / sr
            f = freq if glide is None else freq + (glide - freq) * (k / max(1, total))
            if vibrato:
                f *= 1 + vibrato * math.sin(tw * 5.0 * t)
            fase += tw * f / sr
            env = min(1.0, t / ataque) if ataque > 0 else 1.0
            if decai:
                env *= math.exp(-t / decai)
            resta = (total - k) / sr
            if resta < liberar:
                env *= resta / liberar
            s = 0.0
            for h, a in enumerate(harm, 1):
                if a:
                    s += a * math.sin(fase * h)
            b[i0 + k] += amp * env * s

    def piano(self, t0, nota, amp=0.3, dur=3.0):
        f = _nota(nota) if isinstance(nota, str) else nota
        self.tom(t0, dur, f, amp, harm=(1.0, 0.45, 0.22, 0.12, 0.06), ataque=0.004,
                 decai=dur * 0.33, liberar=0.3)
        self.tom(t0, 0.03, f * 4, amp * 0.15, ataque=0.001, decai=0.01)  # martelo

    def pad(self, t0, dur, notas, amp=0.08, ataque=1.5):
        for n in notas:
            f = _nota(n) if isinstance(n, str) else n
            for det in (0.997, 1.003):
                self.tom(t0, dur, f * det, amp, harm=(1.0, 0.3, 0.12), ataque=ataque,
                         liberar=min(1.5, dur / 2), vibrato=0.002)

    def ruido(self, t0, dur, amp, corte=0.1, ataque=0.002, decai=None, liberar=0.02,
              mod=None, passa_alta=False):
        """Ruído filtrado (corte 0..1: menor = mais grave)."""
        b, sr, rnd = self.b, self.sr, self.rng.random
        i0, i1 = self._faixa(t0, dur)
        y = 0.0
        total = i1 - i0
        for k in range(total):
            t = k / sr
            x = rnd() * 2 - 1
            y += corte * (x - y)
            s = (x - y) if passa_alta else y
            env = min(1.0, t / ataque) if ataque > 0 else 1.0
            if decai:
                env *= math.exp(-t / decai)
            resta = (total - k) / sr
            if resta < liberar:
                env *= resta / liberar
            if mod:
                env *= mod(t)
            b[i0 + k] += amp * env * s

    def impacto(self, t0, amp=0.9, f0=110, f1=38, dur=1.6):
        """Batida grave cinematográfica (queda de afinação)."""
        b, sr = self.b, self.sr
        i0, i1 = self._faixa(t0, dur)
        fase = 0.0
        for k in range(i1 - i0):
            t = k / sr
            f = f1 + (f0 - f1) * math.exp(-t * 9)
            fase += 2 * math.pi * f / sr
            b[i0 + k] += amp * math.exp(-t * 2.6) * math.sin(fase)
        self.ruido(t0, 0.08, amp * 0.5, corte=0.25, decai=0.03)

    def coracao(self, t0, amp=0.8):
        self.impacto(t0, amp, 70, 40, 0.35)
        self.impacto(t0 + 0.24, amp * 0.7, 62, 38, 0.35)

    def tique(self, t0, amp=0.25, agudo=True):
        self.tom(t0, 0.03, 2600 if agudo else 1900, amp, harm=(1.0, 0.3), ataque=0.0005, decai=0.006)
        self.ruido(t0, 0.02, amp * 0.6, corte=0.9, decai=0.004, passa_alta=True)

    def reverb(self, mistura=0.3, tamanho=1.0):
        """Reverb de Schroeder simples (pentes + passa-tudo)."""
        sr, b = self.sr, self.b
        saida = [0.0] * self.n
        for atraso_ms, ganho in ((29.7, 0.78), (37.1, 0.76), (41.1, 0.74), (43.7, 0.72)):
            d = int(atraso_ms * tamanho * sr / 1000)
            buf = [0.0] * self.n
            for i in range(self.n):
                v = b[i] + (buf[i - d] * ganho if i >= d else 0.0)
                buf[i] = v
                saida[i] += v * 0.25
        d = int(5.0 * sr / 1000)
        g = 0.7
        ap = [0.0] * self.n
        for i in range(self.n):
            x = saida[i]
            xd = saida[i - d] if i >= d else 0.0
            yd = ap[i - d] if i >= d else 0.0
            ap[i] = -g * x + xd + g * yd
        self.b = [b[i] * (1 - mistura) + ap[i] * mistura for i in range(self.n)]

    def salvar(self, caminho, volume=0.8, fade=0.02):
        b = self.b
        pico = max(1e-6, max(abs(x) for x in b))
        g = volume / pico
        nf = int(fade * self.sr)
        dados = array.array("h")
        for i, x in enumerate(b):
            e = 1.0
            if i < nf:
                e = i / nf
            elif i > self.n - nf:
                e = (self.n - i) / nf
            v = int(max(-1.0, min(1.0, math.tanh(x * g * 1.1))) * 32000 * e)
            dados.append(v)
        if sys.byteorder == "big":
            dados.byteswap()
        with wave.open(caminho, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.sr)
            w.writeframes(dados.tobytes())


# ---------------- Efeitos sonoros ----------------
def _sfx_hover(s):
    s.tom(0, 0.05, 1760, 0.15, harm=(1.0,), ataque=0.002, decai=0.012)

def _sfx_clique(s):
    s.ruido(0, 0.03, 0.6, corte=0.6, decai=0.006)
    s.tom(0, 0.06, 180, 0.5, ataque=0.001, decai=0.015)

def _sfx_passos(s):
    for i, t in enumerate((0.05, 0.5, 0.95, 1.4)):
        a = 0.9 - i * 0.1
        s.ruido(t, 0.09, a, corte=0.08, ataque=0.001, decai=0.025)
        s.tom(t, 0.1, 85, a * 0.6, ataque=0.001, decai=0.03)
        s.ruido(t + 0.02, 0.18, a * 0.18, corte=0.9, decai=0.06, passa_alta=True)  # poça
    s.reverb(0.2, 0.7)

def _sfx_busca(s):
    rng = random.Random(3)
    pontos = [rng.random() for _ in range(40)]
    s.ruido(0, 0.75, 0.6, corte=0.55, ataque=0.05, liberar=0.2, passa_alta=True,
            mod=lambda t: 0.3 + 0.7 * pontos[int(t * 50) % 40])

def _sfx_pista(s):
    s.ruido(0, 0.7, 0.4, corte=0.05, ataque=0.65, liberar=0.02)  # sucção reversa
    s.tom(0, 0.7, 293.66, 0.15, harm=(1, .4, .2), ataque=0.65, liberar=0.02, glide=311.1)
    s.impacto(0.7, 0.9)
    for n in ("D3", "D#4", "A4", "D5"):
        s.piano(0.7, n, 0.22, 2.2)
    s.reverb(0.35, 1.3)

def _sfx_nada(s):
    s.tom(0, 0.5, 220, 0.3, harm=(1, .3), ataque=0.005, decai=0.15)
    s.tom(0.18, 0.6, 196, 0.3, harm=(1, .3), ataque=0.005, decai=0.2)
    s.reverb(0.25)

def _sfx_gravador(s):
    s.ruido(0, 0.04, 0.8, corte=0.5, decai=0.01)
    s.tom(0, 0.08, 120, 0.6, ataque=0.001, decai=0.02)
    s.ruido(0.05, 0.6, 0.12, corte=0.95, ataque=0.05, liberar=0.3, passa_alta=True)
    s.tom(0.12, 0.12, 1000, 0.18, ataque=0.002, liberar=0.02)

def _sfx_coracao(s):
    s.coracao(0.0, 0.9)
    s.coracao(0.85, 0.9)

def _sfx_latido(s):
    for t in (0.0, 0.32, 0.55):
        s.tom(t, 0.17, 620, 0.5, harm=(1, .8, .6, .4, .3, .2), ataque=0.005, liberar=0.06, glide=360)
        s.ruido(t, 0.14, 0.35, corte=0.5, ataque=0.003, decai=0.05)
    s.reverb(0.2, 0.6)

def _sfx_trovao(s):
    rng = random.Random(11)
    picos = [rng.random() ** 2 for _ in range(30)]
    s.ruido(0, 0.25, 0.6, corte=0.6, decai=0.08)
    s.ruido(0.05, 3.2, 1.0, corte=0.03, ataque=0.1, liberar=1.5,
            mod=lambda t: 0.4 + 0.6 * picos[int(t * 9) % 30])

def _sfx_flash(s):
    for t in (0.0, 0.35, 0.55):
        s.ruido(t, 0.04, 0.7, corte=0.7, decai=0.01)
        s.ruido(t + 0.05, 0.06, 0.4, corte=0.4, decai=0.02)
        s.tom(t + 0.04, 0.15, 3200, 0.06, ataque=0.03, glide=4200)

def _sfx_telefone(s):
    for t in (0.0, 0.6):
        s.tom(t, 0.4, 150, 0.6, harm=(1, 0, .33, 0, .2), ataque=0.01, liberar=0.03,
              vibrato=0.02)

def _sfx_cafe(s):
    s.ruido(0, 0.8, 0.25, corte=0.3, ataque=0.2, liberar=0.3)
    s.piano(0.1, "A5", 0.15, 1.0)
    s.reverb(0.3)

def _sfx_dica(s):
    for i, n in enumerate(("A5", "D6", "F6")):
        s.tom(i * 0.12, 1.4, _nota(n), 0.22, harm=(1, 0, .2), ataque=0.003, decai=0.4)
    s.reverb(0.4, 1.2)

def _sfx_erro(s):
    for n in ("D2", "D#2", "A2"):
        s.tom(0, 1.3, _nota(n), 0.3, harm=(1, .7, .5, .35, .25, .15), ataque=0.02, decai=0.6)
    s.impacto(0, 0.8, 90, 35, 1.4)
    s.reverb(0.3)

def _sfx_revelacao(s):
    s.ruido(0, 1.2, 0.35, corte=0.04, ataque=1.15, liberar=0.02)
    s.impacto(1.2, 1.0, 120, 32, 2.5)
    s.pad(1.2, 3.3, ("D3", "F3", "A3", "D4"), 0.07, ataque=0.05)
    for n in ("D2", "A2", "F3", "D4"):
        s.piano(1.2, n, 0.25, 3.0)
    s.reverb(0.4, 1.4)

def _sfx_certo(s):
    s.piano(0, "E5", 0.25, 0.8)
    s.piano(0.1, "A5", 0.25, 1.0)
    s.reverb(0.25)

def _sfx_errado(s):
    s.tom(0, 0.3, 110, 0.5, harm=(1, .6, .4, .3), ataque=0.005, liberar=0.05)

def _sfx_evento(s):
    s.ruido(0, 1.0, 0.5, corte=0.12, ataque=0.4, liberar=0.5)
    s.tom(0, 1.0, 146.8, 0.2, harm=(1, .3), ataque=0.4, liberar=0.5)
    s.reverb(0.3)

def _sfx_passo(s):
    s.ruido(0, 0.07, 0.5, corte=0.07, ataque=0.001, decai=0.02)
    s.tom(0, 0.08, 80, 0.35, ataque=0.001, decai=0.025)

def _voz(freq, harm=(1, 0, .33, 0, .2), dur=0.05, ruido=0.0):
    def f(s):
        s.tom(0, dur, freq, 0.55, harm=harm, ataque=0.002, decai=dur * 0.45, liberar=0.01)
        if ruido:
            s.ruido(0, dur, ruido, corte=0.4, ataque=0.001, decai=dur * 0.3)
    return f

def _sfx_tecla(fator):
    def f(s):
        s.ruido(0, 0.03, 0.7, corte=0.75, decai=0.004, passa_alta=True)
        s.tom(0, 0.05, 150 * fator, 0.4, ataque=0.001, decai=0.012)
        s.tom(0.004, 0.04, 2300 * fator, 0.08, ataque=0.001, decai=0.008)
    return f

def _sfx_balao(s):
    s.tom(0, 0.09, 880, 0.4, harm=(1, .2), ataque=0.003, decai=0.03, glide=330)

def _sfx_papel(s):
    s.ruido(0, 0.28, 0.5, corte=0.6, ataque=0.03, liberar=0.12, passa_alta=True,
            mod=lambda t: 0.5 + 0.5 * math.sin(t * 90))

VOZES = {"helena": (430, (1, 0, .3, 0, .15), 0.0), "sofia": (620, (1, .2, .1), 0.0),
         "olivia": (340, (1, 0, .4, 0, .25), 0.0), "rodrigo": (210, (1, .5, .3, .2), 0.0),
         "aluna": (540, (1, .3, .15), 0.0), "estudante": (470, (1, 0, .3), 0.0),
         "max": (190, (1, .8, .6, .4), 0.25), "tel": (700, (1, .6, .4), 0.15)}

SFX = {
    "passo": (0.1, _sfx_passo, 0.22),
    "balao": (0.1, _sfx_balao, 0.35), "papel": (0.3, _sfx_papel, 0.3),
    "hover": (0.06, _sfx_hover, 0.35), "clique": (0.09, _sfx_clique, 0.55),
    "passos": (1.9, _sfx_passos, 0.7), "busca": (0.8, _sfx_busca, 0.5),
    "pista": (3.2, _sfx_pista, 0.85), "nada": (1.0, _sfx_nada, 0.5),
    "gravador": (0.7, _sfx_gravador, 0.6), "coracao": (1.8, _sfx_coracao, 0.65),
    "latido": (1.0, _sfx_latido, 0.75), "trovao": (3.3, _sfx_trovao, 0.8),
    "flash": (0.8, _sfx_flash, 0.6), "telefone": (1.1, _sfx_telefone, 0.3),
    "cafe": (1.2, _sfx_cafe, 0.5), "dica": (1.8, _sfx_dica, 0.55),
    "erro": (1.8, _sfx_erro, 0.85), "revelacao": (4.6, _sfx_revelacao, 0.9),
    "certo": (1.2, _sfx_certo, 0.55), "errado": (0.4, _sfx_errado, 0.35),
    "evento": (1.2, _sfx_evento, 0.6),
}

for _i, _fat in enumerate((0.94, 1.0, 1.07)):
    for _nome, (_f, _h, _r) in VOZES.items():
        SFX[f"voz_{_nome}_{_i}"] = (0.06, _voz(_f * _fat, _h, 0.05, _r), 0.28)
    SFX[f"voz_narra_{_i}"] = (0.06, _sfx_tecla(_fat), 0.3)


# ---------------- Trilhas (loops) ----------------
def _mus_tema(s):
    """Tema principal: piano solitário sobre drone grave (Ré menor)."""
    L = 24.0
    s.pad(0, L, ("D2", "A2"), 0.07, ataque=0.5)
    s.pad(0, 12, ("F3", "A3"), 0.035)
    s.pad(12, 12, ("E3", "A3"), 0.035)
    motivo = [(0.0, "D5"), (1.5, "F5"), (3.0, "A4"), (4.5, "G4"), (6.75, "F4"), (7.5, "E4"),
              (9.0, "D4"), (12.0, "D5"), (13.5, "F5"), (15.0, "C5"), (16.5, "A#4"),
              (18.75, "A4"), (19.5, "G4"), (21.0, "A4")]
    for t, n in motivo:
        s.piano(t + 0.3, n, 0.2, 3.2)
    for t in (0.3, 6.3, 12.3, 18.3):
        s.piano(t, "D3" if t < 12 else "A2", 0.16, 5.0)
    for t in range(0, 24, 2):
        s.tique(t, 0.05, t % 4 == 0)
    s.reverb(0.4, 1.5)

def _mus_investigacao(s):
    """Investigação: pulso de sintetizador em colcheias + tique-taque."""
    L, bpm = 19.2, 100
    colch = 60 / bpm / 2
    acordes = [("D2", ("D3", "F3", "A3")), ("A#1", ("D3", "F3", "A#3")),
               ("G1", ("D3", "G3", "A#3")), ("A1", ("C#3", "E3", "A3"))]
    passo = L / 4
    for i, (baixo, ac) in enumerate(acordes):
        t0 = i * passo
        s.pad(t0, passo + 0.3, ac, 0.03, ataque=0.8)
        k = 0
        while k * colch < passo - 0.01:
            t = t0 + k * colch
            acento = 1.0 if k % 4 == 0 else 0.6
            s.tom(t, colch * 0.9, _nota(baixo), 0.22 * acento, harm=(1, .5, .25), ataque=0.004,
                  decai=0.09, liberar=0.02)
            k += 1
    for k in range(int(L / (60 / bpm))):
        s.tique(k * 60 / bpm, 0.07, k % 2 == 0)
    for t, n in ((2.4, "A5"), (7.2, "F5"), (12.0, "D6"), (16.8, "E5")):
        s.piano(t, n, 0.08, 2.5)
    s.reverb(0.3, 1.2)

def _mus_tensao(s):
    """Tensão: batimentos, cluster dissonante e agudo crescente."""
    L = 17.0
    for n in ("D3", "D#3", "A3"):
        s.tom(0, L, _nota(n), 0.05, harm=(1, .35, .15), ataque=2.0, liberar=1.0, vibrato=0.004)
    s.tom(0, L, _nota("D6"), 0.02, harm=(1,), ataque=6.0, liberar=1.0, glide=_nota("F6"))
    batida = 60 / 72
    t = 0.0
    while t < L - 0.5:
        s.coracao(t, 0.55)
        t += batida
    for t in (0, 8.5):
        s.impacto(t + 0.01, 0.35, 60, 30, 3.0)
    s.reverb(0.35, 1.4)

def _mus_final(s):
    """Final: acordes de piano em Ré menor que se resolvem em Lá."""
    L = 24.0
    ciclo = [("D3", ("D4", "F4", "A4")), ("A#2", ("D4", "F4", "A#4")),
             ("F2", ("C4", "F4", "A4")), ("A2", ("C#4", "E4", "A4"))]
    for i, (b, ac) in enumerate(ciclo):
        t0 = i * 6.0
        s.pad(t0, 6.3, ac, 0.035, ataque=1.0)
        s.piano(t0 + 0.05, b, 0.22, 5.5)
        for j, n in enumerate(ac):
            s.piano(t0 + 0.6 + j * 0.55, n, 0.16, 4.0)
        s.piano(t0 + 3.6, ac[-1][:-1] + str(int(ac[-1][-1]) + 1), 0.1, 2.5)
    s.reverb(0.45, 1.5)

def _mus_derrota(s):
    """Derrota: drone que afunda e piano distante."""
    L = 14.0
    s.tom(0, L, _nota("A2"), 0.12, harm=(1, .4, .2), ataque=1.0, liberar=2.0, glide=_nota("D2"))
    s.tom(0, L, _nota("D2"), 0.1, harm=(1, .3), ataque=1.0, liberar=2.0)
    for t, n in ((1.0, "D4"), (3.0, "C4"), (5.0, "A#3"), (7.0, "A3"), (10.0, "D3")):
        s.piano(t, n, 0.16, 4.0)
    t, gap = 0.5, 0.9
    while t < L - 1:
        s.coracao(t, 0.3)
        t += gap
        gap *= 1.18
    s.reverb(0.45, 1.5)

MUSICAS = {
    "tema": (24.0, _mus_tema, 0.38), "investigacao": (19.2, _mus_investigacao, 0.32),
    "tensao": (17.0, _mus_tensao, 0.4), "final": (24.0, _mus_final, 0.38),
    "derrota": (14.0, _mus_derrota, 0.38),
}


