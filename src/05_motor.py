
# =========================================================================
# 3) MOTOR DO JOGO (pygame) — mundo em pixel art, personagens, cenas
# =========================================================================

LW, LH = 480, 270          # resolução lógica (pixel art)
T = 16                     # tamanho do tile
COLS, LINHAS = 30, 15
OY = 26                    # deslocamento vertical da sala (espaço do HUD)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


C = {k: hexrgb(v) for k, v in COR.items()}


def misturar(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def escurecer(c, f=0.75):
    return tuple(max(0, int(x * f)) for x in c)


# ---------------------------------------------------------------- sprites
_BASE_FRENTE = [
    "...hhhhhh...",
    "..hhhhhhhh..",
    "..hssssssh..",
    "..hsesseshL.",
    "..hssssssh..",
    "...hssssh...",
    "...cccccc...",
    "..ccwddccc..",
    ".sccwddcccs.",
    ".sccbddcccs.",
    "..cccddccc..",
    "..cccccccc..",
    "...pp..pp...",
    "...pp..pp...",
    "...ff..ff...",
    "............",
]
_BASE_COSTAS = [
    "...hhhhhh...",
    "..hhhhhhhh..",
    "..hhhhhhhh..",
    "..hhhhhhhhL.",
    "..hhhhhhhh..",
    "...hhhhhh...",
    "...cccccc...",
    "..cccddccc..",
    ".scccddcccs.",
    ".scccddcccs.",
    "..cccddccc..",
    "..cccccccc..",
    "...pp..pp...",
    "...pp..pp...",
    "...ff..ff...",
    "............",
]
_BASE_LADO = [
    "...hhhhhh...",
    "..hhhhhhhh..",
    "..hhhhssss..",
    "..hhhhsses..",
    "..hhhhssss..",
    "...hhhsss...",
    "....cccc....",
    "...ccccdc...",
    "...cccsdc...",
    "...cccsdc...",
    "...ccccdc...",
    "...cccccc...",
    "....pppp....",
    "....pp.p....",
    "....ff.f....",
    "............",
]
_PERNAS = {  # quadros de caminhada (linhas 12-14)
    "frente": [["...pp..pp...", "...pp..pp...", "...ff..ff..."],
               ["...pp..pp...", "...pp...pp..", "...ff...ff.."],
               ["...pp..pp...", "..pp...pp...", "..ff...ff..."]],
    "lado": [["....pppp....", "....pp.p....", "....ff.f...."],
             ["....pppp....", "...pp...p...", "...ff...ff.."],
             ["....pppp....", "....p.pp....", "....f.ff...."]],
}


def _sprite_humano(pal, longo, direcao, quadro):
    if direcao == "baixo":
        base = [list(r) for r in _BASE_FRENTE]
        pernas = _PERNAS["frente"][quadro]
    elif direcao == "cima":
        base = [list(r) for r in _BASE_COSTAS]
        pernas = _PERNAS["frente"][quadro]
    else:
        base = [list(r) for r in _BASE_LADO]
        pernas = _PERNAS["lado"][quadro]
    for i, linha in enumerate(pernas):
        base[12 + i] = list(linha)
    if longo:  # cabelo comprido caindo nos ombros
        for y in range(5, 9):
            if direcao in ("baixo", "cima"):
                for x in (2, 9):
                    base[y][x] = "h"
                if direcao == "cima":
                    for x in range(3, 9):
                        base[y][x] = "h" if y < 8 else base[y][x]
            else:
                for x in (2, 3, 4):
                    base[y][x] = "h"
    if not pal.get("distintivo"):
        for r in base:
            for i, ch in enumerate(r):
                if ch == "b":
                    r[i] = "c"
    for r in base:
        for i, ch in enumerate(r):
            if ch == "L":
                r[i] = "h" if longo else "."
            if ch == "w" and not pal.get("camisa"):
                r[i] = "c"
    cores = {
        "h": pal["cabelo"], "s": pal.get("pele", "#e0b494"), "e": "#1b1f24",
        "c": pal["roupa"], "d": pal.get("sombra", None) or "#000000",
        "p": pal.get("calca", "#1a1e21"), "f": pal.get("sapato", "#0d0f12"),
        "b": "#d8b04a", "w": pal.get("camisa", "#e9e4d8"),
    }
    if pal.get("sombra") is None:
        cores["d"] = "#%02x%02x%02x" % escurecer(hexrgb(pal["roupa"]), 0.7)
    surf = pygame.Surface((12, 16), pygame.SRCALPHA)
    for y, r in enumerate(base):
        for x, ch in enumerate(r):
            if ch != "." and ch in cores:
                surf.set_at((x, y), hexrgb(cores[ch]))
    if direcao == "esquerda":
        surf = pygame.transform.flip(surf, True, False)
    return surf


_CAO = [
    "..........kk..",
    "k........kkkk.",
    "kk.......kkekn",
    ".kkkkkkkkkkkk.",
    "..kkkkkkkkkk..",
    "..kkddddddkk..",
    "..kk.....kk...",
    "..kk.....kk...",
]


def _sprite_cao(quadro, direcao):
    surf = pygame.Surface((14, 8), pygame.SRCALPHA)
    cores = {"k": (42, 32, 26), "d": (120, 84, 50), "e": (230, 200, 120), "n": (10, 10, 10)}
    linhas = [list(r) for r in _CAO]
    if quadro == 1:
        linhas[6] = list("...kk.....kk..")
        linhas[7] = list("...kk......kk.")
    for y, r in enumerate(linhas):
        for x, ch in enumerate(r):
            if ch in cores:
                surf.set_at((x, y), cores[ch])
    if direcao == "esquerda":
        surf = pygame.transform.flip(surf, True, False)
    return surf


PALETAS = {
    "helena": {"cabelo": "#b85a30", "roupa": "#2a3a46", "pele": "#e6bc9c", "camisa": "#1b2a33", "calca": "#1a1e21"},
    "sofia": {"cabelo": "#3b2618", "roupa": "#9fb3c8", "pele": "#e8c4a6", "calca": "#9fb3c8", "sapato": "#c9c9d6"},
    "olivia": {"cabelo": "#2a1d17", "roupa": "#1f3550", "pele": "#d9a98a", "distintivo": True, "camisa": "#152538"},
    "rodrigo": {"cabelo": "#121212", "roupa": "#1f3550", "pele": "#c8946e", "distintivo": True, "camisa": "#152538"},
    "aluno1": {"cabelo": "#2b2b2b", "roupa": "#1c1c1c", "camisa": "#e9e4d8", "pele": "#d4a27e"},
    "aluno2": {"cabelo": "#6b4a2b", "roupa": "#5c2f35", "pele": "#e8c4a6", "calca": "#5c2f35"},
    "aluno3": {"cabelo": "#d8c08a", "roupa": "#2f5a5a", "pele": "#f0ccb0", "calca": "#2f5a5a"},
}
CABELO_LONGO = {"helena": True, "sofia": True, "olivia": False, "rodrigo": False,
                "aluno1": False, "aluno2": True, "aluno3": True}


class Ent:
    """Personagem no mundo (posição = centro dos pés, em pixels da sala)."""

    def __init__(self, eid, nome, x, y, pal=None, longo=False, retrato=None, cao=False):
        self.id, self.nome = eid, nome
        self.x, self.y = float(x), float(y)
        self.dir = "baixo"
        self.pal, self.longo, self.retrato, self.cao = pal, longo, retrato, cao
        self.visivel = True
        self.andando = False
        self.t_anim = 0.0
        self.alvo = None
        self._cache = {}

    def sprite(self):
        q = 0 if not self.andando else (1 if int(self.t_anim * 8) % 2 == 0 else 2)
        if self.cao:
            chave = (q % 2, "esquerda" if self.dir == "esquerda" else "direita")
            if chave not in self._cache:
                self._cache[chave] = _sprite_cao(chave[0], chave[1])
            return self._cache[chave]
        chave = (self.dir, q)
        if chave not in self._cache:
            self._cache[chave] = _sprite_humano(self.pal, self.longo, self.dir, q)
        return self._cache[chave]


# ---------------------------------------------------------------- salas
# Cada móvel: (tipo, tx, ty, tw, th, sólido, ponto)  — ponto = índice do ponto
# de investigação (0..2), "telefone", ou None.
SALAS = {
    "escritorio": {
        "piso": "madeira", "parede": "#2a2f36", "escuro": 165, "externo": False,
        "moveis": [
            ("estante", 2, 0, 5, 2, True, None), ("janela", 9, 0, 3, 1, True, None),
            ("janela", 17, 0, 3, 1, True, None), ("quadro_cortica", 13, 0, 3, 1, True, None),
            ("tapete", 10, 6, 9, 5, False, None), ("mesa_trabalho", 5, 4, 4, 2, True, "telefone"),
            ("luminaria", 4, 4, 1, 1, True, None), ("sofa", 21, 4, 5, 2, True, None),
            ("planta", 27, 1, 1, 1, True, None), ("arquivo", 1, 9, 2, 2, True, None),
            ("cafeteira", 24, 10, 2, 1, True, None),
        ],
        "luzes": [(4.5, 4.5, 70), (10.5, 1, 45), (18.5, 1, 45)],
        "saida": (14, 14), "inicio": (14, 12),
    },
    "salao": {
        "piso": "salao", "parede": "#2b2236", "escuro": 135, "externo": False,
        "moveis": [
            ("palco", 10, 0, 10, 3, False, None), ("dj", 14, 1, 2, 1, True, 1),
            ("mesa_festa", 3, 4, 3, 2, True, 0), ("mesa_festa", 23, 4, 3, 2, True, None),
            ("mesa_festa", 3, 9, 3, 2, True, None), ("mesa_festa", 23, 9, 3, 2, True, None),
            ("lixeira", 26, 12, 1, 1, True, 2), ("baloes", 1, 1, 2, 2, True, None),
            ("baloes", 27, 1, 2, 2, True, None), ("pilar", 8, 6, 1, 1, True, None),
            ("pilar", 20, 6, 1, 1, True, None), ("faixa", 11, 0, 8, 1, True, None),
        ],
        "luzes": [(15, 2, 90), (4.5, 5, 50), (24.5, 5, 50), (4.5, 10, 50), (24.5, 10, 50)],
        "saida": (14, 14), "porta_lado": ((29, 7), "banheiro_baile", (1, 7)), "inicio": (14, 12),
    },
    "banheiro_baile": {
        "piso": "azulejo", "parede": "#3a4a52", "escuro": 150, "externo": False,
        "moveis": [
            ("cabine", 3, 0, 2, 3, True, None), ("cabine_fita", 6, 0, 2, 3, True, None),
            ("corpo", 5, 4, 4, 1, True, 0),
            ("cabine", 9, 0, 2, 3, True, None), ("pia", 15, 0, 6, 2, True, 1),
            ("camera", 26, 0, 1, 1, True, 2), ("lixeira", 24, 12, 1, 1, True, None),
            ("fita_chao", 3, 6, 8, 1, False, None),
        ],
        "luzes": [(18, 1, 70), (7, 2, 45), (26, 1, 30)],
        "porta_lado": ((0, 7), "salao", (28, 7)), "inicio": (2, 7),
    },
    "tulane": {
        "piso": "tulane", "parede": "#3b3328", "escuro": 175, "externo": True,
        "moveis": [
            ("estante", 1, 0, 4, 2, True, None), ("estante", 6, 0, 4, 2, True, None),
            ("arquivo_grande", 2, 5, 3, 2, True, 0), ("mural", 11, 0, 3, 1, True, 1),
            ("mesa_leitura", 6, 8, 4, 2, True, None), ("divisoria", 13, 2, 1, 8, True, None),
            ("arvore", 17, 2, 2, 2, True, None), ("arvore", 26, 1, 2, 2, True, None),
            ("arvore", 26, 8, 2, 2, True, None), ("terra", 20, 8, 3, 2, True, 2),
            ("poste", 16, 9, 1, 1, True, None), ("banco", 21, 3, 3, 1, True, None),
        ],
        "luzes": [(3.5, 6, 55), (8, 9, 55), (16.5, 9, 75), (12.5, 1, 40)],
        "saida": (7, 14), "inicio": (7, 12),
        "ceu_aberto": [(14, 0, 16, 15)],          # só o jardim; o arquivo (à esquerda) é coberto
    },
    "banheiro_tulane": {
        "piso": "concreto", "parede": "#4a4038", "escuro": 175, "externo": True,
        "moveis": [
            ("predio_banheiro", 2, 0, 9, 3, True, None), ("camera", 4, 2, 1, 1, True, 0),
            ("arbustos", 21, 3, 5, 3, True, 1), ("porta_servico", 13, 0, 2, 2, True, None),
            ("carrinho", 15, 9, 2, 2, True, 2), ("poste", 10, 6, 1, 1, True, None),
            ("arvore", 26, 9, 2, 2, True, None), ("grama", 18, 0, 11, 8, False, None),
        ],
        "luzes": [(10.5, 6, 75), (5.5, 1, 35)],
        "saida": (14, 14), "inicio": (14, 12),
        "ceu_aberto": [(0, 3, 30, 12), (11, 0, 19, 3)],   # tudo, menos o prédio do banheiro
    },
    "interrogatorio": {
        "piso": "concreto_int", "parede": "#2d3a40", "escuro": 140, "externo": False,
        "moveis": [
            ("computador", 2, 2, 3, 2, True, 0), ("quadro", 19, 0, 5, 1, True, 1),
            ("arquivo", 26, 2, 2, 2, True, 2), ("espelho_falso", 8, 0, 7, 1, True, None),
            ("mesa_interrogatorio", 11, 5, 6, 2, True, None), ("banco_longo", 3, 11, 9, 1, True, None),
            ("bebedouro", 27, 10, 1, 1, True, None),
        ],
        "luzes": [(14, 6, 85), (3.5, 3, 40)],
        "saida": (22, 14), "inicio": (22, 12),
    },
    "casa": {
        "piso": "casa", "parede": "#33302b", "escuro": 175, "externo": False,
        "moveis": [
            ("mesa_trabalho", 3, 2, 4, 2, True, 0), ("estante", 1, 0, 6, 1, True, None),
            ("divisoria", 10, 0, 1, 7, True, None), ("divisoria", 19, 0, 1, 7, True, None),
            ("cama", 23, 1, 3, 4, True, 2), ("comoda", 27, 1, 2, 1, True, None),
            ("sofa", 12, 2, 5, 2, True, None), ("grama", 20, 8, 9, 6, False, None),
            ("casinha", 25, 10, 2, 2, True, 1), ("cerca", 20, 8, 1, 3, True, None),
            ("cerca", 20, 12, 1, 2, True, None),
            ("luminaria", 7, 2, 1, 1, True, None), ("quadro_cortica", 13, 0, 3, 1, True, None),
        ],
        "luzes": [(7.5, 2.5, 60), (14.5, 3, 50), (24, 2, 45), (24, 11, 40)],
        "saida": (5, 14), "inicio": (5, 12),
        "ceu_aberto": [(21, 8, 9, 7)],            # só o quintal do Max
    },
}


def _ruido_pixel(surf, rect, cor, densidade=0.08, var=0.12, rng=None):
    rng = rng or random.Random(rect[0] * 31 + rect[1])
    for _ in range(int(rect[2] * rect[3] * densidade)):
        x = rect[0] + rng.randrange(rect[2])
        y = rect[1] + rng.randrange(rect[3])
        f = 1 + rng.uniform(-var, var)
        surf.set_at((x, y), tuple(max(0, min(255, int(c * f))) for c in cor))


def desenhar_piso(surf, tipo, rng):
    for ty in range(LINHAS):
        for tx in range(COLS):
            x, y = tx * T, ty * T
            r = pygame.Rect(x, y, T, T)
            if tipo == "madeira" or tipo == "casa":
                base = (74, 52, 38) if tipo == "madeira" else (66, 50, 40)
                pygame.draw.rect(surf, base, r)
                for k in range(0, T, 4):
                    pygame.draw.line(surf, escurecer(base, 0.8), (x, y + k), (x + T - 1, y + k))
                off = (ty * 7) % T
                pygame.draw.line(surf, escurecer(base, 0.7), (x + off, y), (x + off, y + 3))
            elif tipo == "salao":
                cor = (40, 34, 52) if (tx + ty) % 2 == 0 else (30, 26, 40)
                pygame.draw.rect(surf, cor, r)
                if (tx * 3 + ty * 5) % 11 == 0:
                    surf.set_at((x + 7, y + 7), (120, 110, 150))
            elif tipo == "azulejo":
                cor = (150, 170, 172) if (tx + ty) % 2 == 0 else (128, 148, 152)
                pygame.draw.rect(surf, cor, r)
                pygame.draw.rect(surf, (96, 112, 116), r, 1)
            elif tipo in ("concreto", "concreto_int"):
                cor = (70, 74, 76) if tipo == "concreto" else (62, 70, 74)
                pygame.draw.rect(surf, cor, r)
                if tipo == "concreto" and tx % 4 == 0:
                    pygame.draw.line(surf, escurecer(cor, 0.8), (x, y), (x, y + T))
            elif tipo == "tulane":
                if tx <= 13:
                    cor = (88, 64, 44) if (tx + ty) % 2 == 0 else (80, 58, 40)
                else:
                    cor = (38, 62, 40) if (tx * 7 + ty * 3) % 5 else (34, 56, 36)
                pygame.draw.rect(surf, cor, r)
            _ruido_pixel(surf, r, surf.get_at((x + 1, y + 1))[:3], 0.06, 0.15, rng)
    if tipo == "tulane":  # caminho de pedra
        for ty in range(9, LINHAS):
            pygame.draw.rect(surf, (90, 88, 80), (5 * T, ty * T, 4 * T, T))
        for tx in range(14, 30):
            pygame.draw.rect(surf, (90, 88, 80), (tx * T, 6 * T, T, T))


def desenhar_movel(surf, tipo, rect, rng):
    x, y, w, h = rect
    R = pygame.draw.rect
    if tipo == "estante":
        R(surf, (60, 40, 28), rect)
        for k in range(y + 3, y + h, 6):
            R(surf, (40, 26, 18), (x + 1, k, w - 2, 1))
            cx = x + 2
            while cx < x + w - 3:
                cor = rng.choice([(120, 40, 36), (40, 70, 110), (150, 120, 60), (60, 90, 60), (90, 70, 100)])
                bw = rng.randint(2, 3)
                R(surf, cor, (cx, k - 4, bw, 4))
                cx += bw + 1
    elif tipo == "janela":
        R(surf, (30, 40, 52), rect)
        R(surf, (60, 110, 160), (x + 2, y + 2, w - 4, h - 4))
        for k in range(3):
            surf.set_at((x + 4 + k * 9, y + 5), (220, 230, 255))
        R(surf, (30, 40, 52), (x + w // 2, y, 1, h))
    elif tipo in ("quadro_cortica", "mural", "quadro"):
        R(surf, (90, 60, 36), rect)
        R(surf, (150, 112, 70) if tipo != "quadro" else (200, 200, 190), (x + 1, y + 2, w - 2, h - 3))
        for k in range(6):
            px = x + 3 + rng.randrange(max(1, w - 8))
            py = y + 3 + rng.randrange(max(1, h - 7))
            R(surf, rng.choice([(230, 220, 190), (200, 190, 150), (220, 230, 240)]), (px, py, 5, 4))
            surf.set_at((px + 2, py), (190, 40, 40))
        if tipo == "quadro":
            for k in range(3):
                pygame.draw.line(surf, (180, 30, 30), (x + 4 + k * 20, y + 5), (x + 20 + k * 18, y + 10))
    elif tipo == "tapete":
        R(surf, (90, 36, 34), rect)
        R(surf, (130, 90, 50), rect, 2)
        R(surf, (70, 28, 26), (x + 6, y + 6, w - 12, h - 12), 1)
    elif tipo in ("mesa_trabalho", "mesa_leitura"):
        R(surf, (96, 66, 44), (x, y + 4, w, h - 4))
        R(surf, (122, 86, 58), (x, y + 2, w, h - 8))
        R(surf, (60, 40, 26), (x + 2, y + h - 3, 3, 3))
        R(surf, (60, 40, 26), (x + w - 5, y + h - 3, 3, 3))
        R(surf, (230, 220, 200), (x + 6, y + 6, 8, 6))
        R(surf, (210, 200, 180), (x + 16, y + 5, 7, 7))
        if tipo == "mesa_trabalho":
            R(surf, (20, 20, 22), (x + w - 16, y + 5, 9, 6))  # telefone
            R(surf, (40, 40, 44), (x + w - 15, y + 4, 7, 2))
    elif tipo == "luminaria":
        R(surf, (40, 40, 40), (x + 7, y + 4, 2, 10))
        pygame.draw.polygon(surf, (216, 167, 107), [(x + 3, y + 6), (x + 13, y + 6), (x + 10, y), (x + 6, y)])
    elif tipo == "sofa":
        R(surf, (70, 40, 42), rect)
        R(surf, (92, 54, 56), (x + 2, y + 6, w - 4, h - 8))
        R(surf, (60, 34, 36), (x, y, 4, h))
        R(surf, (60, 34, 36), (x + w - 4, y, 4, h))
    elif tipo == "planta":
        R(surf, (100, 60, 40), (x + 4, y + 9, 8, 7))
        pygame.draw.circle(surf, (40, 90, 50), (x + 8, y + 6), 6)
        pygame.draw.circle(surf, (56, 110, 62), (x + 6, y + 5), 3)
    elif tipo in ("arquivo", "arquivo_grande"):
        R(surf, (70, 80, 86), rect)
        for k in range(y + 3, y + h - 2, 7):
            R(surf, (90, 100, 106), (x + 2, k, w - 4, 5))
            R(surf, (200, 200, 190), (x + w // 2 - 2, k + 2, 4, 1))
    elif tipo == "cafeteira":
        R(surf, (96, 66, 44), rect)
        R(surf, (30, 30, 30), (x + 6, y + 2, 6, 10))
        R(surf, (200, 60, 40), (x + 8, y + 4, 2, 1))
    elif tipo == "palco":
        R(surf, (56, 36, 48), rect)
        R(surf, (80, 50, 66), (x, y + h - 4, w, 4))
        for k in range(x + 4, x + w, 12):
            pygame.draw.circle(surf, (216, 167, 107), (k, y + 4), 1)
    elif tipo == "faixa":
        R(surf, (60, 30, 40), (x, y + 2, w, 9))
        f = pygame.font.Font(None, 11)
        txt = f.render("FORMATURA ARQUITETURA 2026", False, (216, 167, 107))
        surf.blit(txt, (x + (w - txt.get_width()) // 2, y + 4))
    elif tipo == "dj":
        R(surf, (24, 24, 30), rect)
        R(surf, (60, 60, 70), (x + 2, y + 2, w - 4, 6))
        pygame.draw.circle(surf, (120, 120, 140), (x + 9, y + 5), 3)
        pygame.draw.circle(surf, (120, 120, 140), (x + 22, y + 5), 3)
        R(surf, (88, 165, 224), (x + 14, y + 10, 4, 2))
    elif tipo == "mesa_festa":
        pygame.draw.ellipse(surf, (220, 216, 206), (x, y + 2, w, h - 4))
        pygame.draw.ellipse(surf, (190, 186, 176), (x, y + 2, w, h - 4), 1)
        for k in range(3):
            pygame.draw.circle(surf, (230, 230, 240), (x + 10 + k * 12, y + 12), 2)
        R(surf, (216, 167, 107), (x + w // 2 - 1, y + 6, 2, 6))
    elif tipo == "lixeira":
        R(surf, (60, 66, 70), (x + 3, y + 3, 10, 12))
        R(surf, (90, 96, 100), (x + 2, y + 2, 12, 3))
    elif tipo == "baloes":
        for k, cor in enumerate([(184, 90, 48), (216, 167, 107), (53, 120, 200)]):
            pygame.draw.circle(surf, cor, (x + 8 + k * 7, y + 8 + (k % 2) * 6), 6)
            pygame.draw.line(surf, (200, 200, 200), (x + 8 + k * 7, y + 14 + (k % 2) * 6), (x + 10 + k * 5, y + h - 1))
    elif tipo == "pilar":
        R(surf, (90, 80, 96), (x + 2, y, 12, 16))
        R(surf, (110, 100, 116), (x + 2, y, 3, 16))
    elif tipo in ("cabine", "cabine_fita"):
        R(surf, (88, 106, 112), rect)
        R(surf, (110, 128, 134), (x + 2, y + 4, w - 4, h - 6))
        R(surf, (60, 70, 74), (x + w - 6, y + h // 2, 2, 3))
        if tipo == "cabine_fita":
            for k in range(0, w, 6):
                R(surf, (230, 200, 40), (x + k, y + 18, 4, 3))
                R(surf, (20, 20, 20), (x + k + 4, y + 18, 2, 3))
            R(surf, (120, 30, 30), (x + 8, y + h - 3, 10, 2))
    elif tipo == "corpo":
        # o professor caído (terno escuro, cabelo grisalho) e a poça de sangue
        pygame.draw.ellipse(surf, (110, 14, 18), (x + 18, y + 3, 34, 12))
        pygame.draw.ellipse(surf, (140, 20, 24), (x + 24, y + 5, 20, 7))
        R(surf, (34, 38, 46), (x + 14, y + 4, 26, 9))       # tronco (terno)
        R(surf, (210, 214, 220), (x + 26, y + 6, 6, 5))     # camisa
        R(surf, (150, 24, 28), (x + 28, y + 7, 3, 3))       # ferimento
        R(surf, (28, 30, 36), (x + 40, y + 5, 14, 3))       # pernas
        R(surf, (28, 30, 36), (x + 40, y + 9, 14, 3))
        R(surf, (12, 12, 14), (x + 54, y + 4, 3, 4))
        R(surf, (12, 12, 14), (x + 54, y + 9, 3, 4))
        R(surf, (214, 176, 150), (x + 6, y + 5, 8, 7))      # rosto
        R(surf, (120, 120, 124), (x + 4, y + 4, 5, 9))      # cabelo grisalho
        R(surf, (34, 38, 46), (x + 16, y + 1, 10, 3))       # braço
        R(surf, (214, 176, 150), (x + 12, y + 1, 4, 3))
        for k in range(0, w, 6):                             # contorno de giz
            surf.set_at((x + k, y), (230, 230, 230))
            surf.set_at((x + k, y + h - 1), (230, 230, 230))
    elif tipo == "fita_chao":
        for k in range(0, w, 8):
            R(surf, (230, 200, 40), (x + k, y + 6, 5, 2))
    elif tipo == "pia":
        R(surf, (40, 52, 58), (x, y, w, 9))
        R(surf, (150, 190, 210), (x + 2, y + 1, w - 4, 7))
        for k in range(x + 2, x + w - 2, 16):
            surf.set_at((k + 5, y + 3), (240, 250, 255))
        R(surf, (210, 214, 210), (x, y + 10, w, 10))
        for k in range(x + 6, x + w, 16):
            pygame.draw.ellipse(surf, (170, 180, 182), (k, y + 12, 10, 6))
    elif tipo == "camera":
        R(surf, (30, 30, 34), (x + 3, y + 3, 10, 6))
        R(surf, (60, 60, 66), (x + 11, y + 4, 4, 4))
        surf.set_at((x + 4, y + 4), (220, 40, 40))
    elif tipo == "divisoria":
        R(surf, (54, 48, 42), rect)
        R(surf, (70, 62, 54), (x, y, 3, h))
    elif tipo == "arvore":
        R(surf, (70, 46, 30), (x + w // 2 - 2, y + h - 10, 5, 10))
        pygame.draw.circle(surf, (28, 60, 40), (x + w // 2, y + h // 2 - 2), w // 2 + 2)
        pygame.draw.circle(surf, (40, 78, 50), (x + w // 2 - 4, y + h // 2 - 6), w // 3)
        for _ in range(6):
            surf.set_at((x + rng.randrange(w), y + rng.randrange(h - 8)), (110, 140, 90))
    elif tipo == "terra":
        pygame.draw.ellipse(surf, (74, 52, 36), rect)
        for _ in range(30):
            surf.set_at((x + 4 + rng.randrange(w - 8), y + 3 + rng.randrange(h - 6)), (96, 70, 48))
    elif tipo == "poste":
        R(surf, (30, 30, 34), (x + 7, y - 10, 2, 26))
        R(surf, (216, 167, 107), (x + 5, y - 13, 6, 4))
    elif tipo in ("banco", "banco_longo"):
        R(surf, (90, 64, 44), (x, y + 4, w, 6))
        R(surf, (60, 42, 30), (x + 2, y + 10, 2, 5))
        R(surf, (60, 42, 30), (x + w - 4, y + 10, 2, 5))
    elif tipo == "predio_banheiro":
        R(surf, (110, 96, 80), rect)
        for k in range(x, x + w, 8):
            R(surf, (96, 84, 70), (k, y, 1, h))
        R(surf, (40, 36, 34), (x + w - 22, y + h - 20, 14, 20))
        f = pygame.font.Font(None, 11)
        surf.blit(f.render("WC", False, (230, 220, 200)), (x + w - 20, y + 6))
    elif tipo == "arbustos":
        for k in range(6):
            pygame.draw.circle(surf, rng.choice([(30, 66, 40), (38, 80, 46), (26, 58, 34)]),
                               (x + 8 + rng.randrange(w - 16), y + 8 + rng.randrange(h - 16)), 9)
    elif tipo == "porta_servico":
        R(surf, (70, 60, 50), rect)
        R(surf, (50, 42, 36), (x + 4, y + 4, w - 8, h - 4))
    elif tipo == "carrinho":
        R(surf, (60, 90, 110), (x + 2, y + 4, w - 4, h - 10))
        pygame.draw.circle(surf, (20, 20, 20), (x + 6, y + h - 4), 3)
        pygame.draw.circle(surf, (20, 20, 20), (x + w - 6, y + h - 4), 3)
    elif tipo == "grama":
        for _ in range(w * h // 30):
            px, py = x + rng.randrange(w), y + rng.randrange(h)
            pygame.draw.line(surf, (40, 74, 44), (px, py), (px, py - 2))
    elif tipo == "computador":
        R(surf, (60, 64, 70), (x, y + 10, w, h - 10))
        R(surf, (20, 22, 26), (x + 8, y, 30, 18))
        R(surf, (60, 140, 180), (x + 10, y + 2, 26, 14))
        for k in range(3):
            R(surf, (150, 220, 240), (x + 12, y + 4 + k * 4, 14 - k * 3, 1))
    elif tipo == "espelho_falso":
        R(surf, (20, 26, 30), rect)
        R(surf, (50, 70, 84), (x + 2, y + 2, w - 4, h - 4))
        pygame.draw.line(surf, (110, 140, 160), (x + 6, y + 3), (x + 14, y + 12))
    elif tipo == "mesa_interrogatorio":
        R(surf, (110, 112, 110), (x, y + 2, w, h - 4))
        R(surf, (80, 82, 80), (x, y + h - 4, w, 2))
        R(surf, (230, 225, 210), (x + 30, y + 6, 10, 8))
        R(surf, (40, 40, 44), (x + 12, y - 6, 10, 6))
        R(surf, (40, 40, 44), (x + 62, y + h, 10, 6))
    elif tipo == "bebedouro":
        R(surf, (200, 210, 214), (x + 3, y, 10, 15))
        R(surf, (120, 180, 220), (x + 5, y + 2, 6, 4))
    elif tipo == "cama":
        R(surf, (80, 56, 40), rect)
        R(surf, (200, 196, 186), (x + 2, y + 2, w - 4, 10))
        R(surf, (70, 80, 110), (x + 2, y + 14, w - 4, h - 16))
    elif tipo == "comoda":
        R(surf, (90, 62, 42), rect)
        R(surf, (120, 86, 58), (x + 2, y + 3, w - 4, 4))
    elif tipo == "casinha":
        pygame.draw.polygon(surf, (120, 40, 34), [(x, y + 10), (x + w // 2, y), (x + w, y + 10)])
        R(surf, (130, 90, 60), (x + 2, y + 10, w - 4, h - 10))
        R(surf, (20, 16, 14), (x + w // 2 - 5, y + 16, 10, h - 16))
    elif tipo == "cerca":
        for k in range(y, y + h, 5):
            R(surf, (130, 112, 90), (x + 6, k, 4, 4))


def construir_sala(sid):
    """Desenha o fundo estático da sala e devolve (surface, grade de colisão)."""
    S = SALAS[sid]
    rng = random.Random(hash(sid) & 0xffff)
    surf = pygame.Surface((COLS * T, LINHAS * T))
    desenhar_piso(surf, S["piso"], rng)
    solido = [[False] * COLS for _ in range(LINHAS)]
    parede = hexrgb(S["parede"])
    # paredes: topo (face) e bordas
    pygame.draw.rect(surf, parede, (0, 0, COLS * T, T))
    pygame.draw.rect(surf, escurecer(parede, 0.6), (0, T - 3, COLS * T, 3))
    for tx in range(COLS):
        solido[0][tx] = True
        solido[LINHAS - 1][tx] = True
    for ty in range(LINHAS):
        solido[ty][0] = True
        solido[ty][COLS - 1] = True
    pygame.draw.rect(surf, escurecer(parede, 0.5), (0, (LINHAS - 1) * T, COLS * T, T))
    pygame.draw.rect(surf, escurecer(parede, 0.5), (0, 0, 6, LINHAS * T))
    pygame.draw.rect(surf, escurecer(parede, 0.5), (COLS * T - 6, 0, 6, LINHAS * T))
    # portas
    portas = []
    if "saida" in S:
        tx, ty = S["saida"]
        portas.append((tx, ty))
        pygame.draw.rect(surf, (20, 16, 14), (tx * T - 4, ty * T, T * 2 + 8, T))
        pygame.draw.rect(surf, (216, 167, 107), (tx * T - 4, ty * T, T * 2 + 8, 2))
        solido[ty][tx] = solido[ty][tx + 1] = False
    if "porta_lado" in S:
        (tx, ty), _, _ = S["porta_lado"]
        pygame.draw.rect(surf, (20, 16, 14), (tx * T, ty * T - 8, T, T * 2))
        pygame.draw.rect(surf, (216, 167, 107), (tx * T + (0 if tx == 0 else T - 2), ty * T - 8, 2, T * 2))
        solido[ty][tx] = False
    for tipo, tx, ty, tw, th, sol, _p in S["moveis"]:
        if tipo in ("tapete", "grama", "palco", "fita_chao"):
            desenhar_movel(surf, tipo, (tx * T, ty * T, tw * T, th * T), rng)
    for tipo, tx, ty, tw, th, sol, _p in S["moveis"]:
        if tipo not in ("tapete", "grama", "palco", "fita_chao"):
            desenhar_movel(surf, tipo, (tx * T, ty * T, tw * T, th * T), rng)
        if sol:
            for yy in range(ty, ty + th):
                for xx in range(tx, tx + tw):
                    if 0 <= yy < LINHAS and 0 <= xx < COLS:
                        solido[yy][xx] = True
    return surf, solido


def mascara_luz(raio):
    """Quanto de escuridão remover em cada ponto (suave até a borda)."""
    s = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    for r in range(raio, 0, -1):
        a = int(255 * (1 - r / raio) ** 0.7)
        pygame.draw.circle(s, (0, 0, 0, a), (raio, raio), r)
    return s


def brilho_luz(raio, cor, forca=0.16):
    """Brilho quente aditivo (preto nas bordas -> não vira disco chapado)."""
    s = pygame.Surface((raio * 2, raio * 2))
    s.fill((0, 0, 0))
    for r in range(raio, 0, -2):
        k = forca * (1 - r / raio) ** 1.6
        pygame.draw.circle(s, tuple(int(c * k) for c in cor), (raio, raio), r)
    return s


class FonteMista:
    """Fonte principal (embutida) + fonte de símbolos para glifos que faltam
    (★ ♥ ▶ ∧ → ↔ ∴ …). Mesma interface usada do pygame.font.Font."""

    def __init__(self, principal, simbolos):
        self.p, self.sim = principal, simbolos
        self._ok = {}

    SIMBOLOS = set("★♥♡◆▶▼▲◀∧∨→↔∴⊢≡✓✗•♪●○←↑↓⇒")

    def _tem(self, ch):
        return ch not in self.SIMBOLOS

    def _trechos(self, texto):
        # o \u200c (separador invisível) evita ligaduras "fi"/"fl" que as fontes desenham errado
        texto = texto.replace("f", "f\u200c")
        out, atual, modo = [], "", None
        for ch in texto:
            m = self._tem(ch) or self.sim is None
            if modo is None or m == modo:
                atual += ch
            else:
                out.append((atual, modo))
                atual = ch
            modo = m
        if atual:
            out.append((atual, modo))
        return out

    def render(self, texto, aa, cor, fundo=None):
        partes = self._trechos(texto)
        if len(partes) <= 1 and (not partes or partes[0][1]):
            return self.p.render(partes[0][0] if partes else "", aa, cor)
        imgs = [(self.p if m else self.sim).render(t, aa, cor) for t, m in partes]
        h = max(self.p.get_height(), max(i.get_height() for i in imgs))
        sup = pygame.Surface((sum(i.get_width() for i in imgs), h), pygame.SRCALPHA)
        x = 0
        for i in imgs:
            sup.blit(i, (x, (h - i.get_height()) // 2))
            x += i.get_width()
        return sup

    def size(self, texto):
        return (sum((self.p if m else self.sim).size(t)[0] for t, m in self._trechos(texto)),
                self.p.get_height())

    def get_linesize(self):
        return self.p.get_linesize()

    def get_height(self):
        return self.p.get_height()


def carregar_fonte(nome, tamanho, negrito=False):
    try:
        f = pygame.font.Font(io.BytesIO(base64.b64decode(FONTES[nome])), int(tamanho))
    except Exception:
        f = pygame.font.SysFont("dejavusans,segoeui,arial", int(tamanho))
    f.set_bold(negrito)
    return f


def quebrar(texto, fonte, largura):
    linhas = []
    for par in texto.split("\n"):
        palavras = par.split(" ")
        atual = ""
        for p in palavras:
            teste = (atual + " " + p).strip()
            if fonte.size(teste)[0] <= largura:
                atual = teste
            else:
                if atual:
                    linhas.append(atual)
                atual = p
        linhas.append(atual)
    return linhas


def paginar(texto, n=170):
    """Divide falas longas em páginas de balão."""
    if len(texto) <= n:
        return [texto]
    paginas, atual = [], ""
    for frase in texto.replace("\n", " \n ").split(" "):
        if frase == "\n":
            if len(atual) > n * 0.6:
                paginas.append(atual.strip())
                atual = ""
            continue
        if len(atual) + len(frase) + 1 > n and atual:
            paginas.append(atual.strip())
            atual = ""
        atual += " " + frase
    if atual.strip():
        paginas.append(atual.strip())
    return paginas
