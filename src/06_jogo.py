
# =========================================================================
# 4) O JOGO — modo história
# =========================================================================

TECLAS_CIMA = (pygame.K_UP, pygame.K_w)
TECLAS_BAIXO = (pygame.K_DOWN, pygame.K_s)
TECLAS_ESQ = (pygame.K_LEFT, pygame.K_a)
TECLAS_DIR = (pygame.K_RIGHT, pygame.K_d)
TECLAS_OK = (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)

NOMES_PISTAS = {"corpo": "Corpo no banheiro trancado", "faca": "Faca do assassinato",
                "cam_baile": "Câmeras do baile", "cam_univ": "Gravações de 2020",
                "terra": "Terra revirada no campus", "livro": "Livro de registros de 2020",
                "celular": "Celular de Beatriz", "computador": "Computador do caso",
                "max": "Reação do cachorro Max"}
NOMES_FEITOS = {"telefone": "Atender a ligação de Sofia", "sofia": "Conversar com Sofia",
                "olivia": "Conversar com a policial Olívia", "interrogatorios": "Interrogar as 4 alunas ruivas",
                "entrevista": "A entrevista da quinta aluna", "comparacao": "Comparar as gravações",
                "acusacao": "Fazer a acusação"}


# Ritmo pensado para a partida completa caber em ~20 minutos de apresentação
VELOCIDADE_TEXTO = {"fala": 55, "tel": 55, "narra": 48, "cena": 48, "carta": 130, "capitulo": 24}
VELOCIDADE_ANDAR = 108   # pixels por segundo

LARG_FALA = 230    # largura (lógica) do balão de fala
LARG_NARRA = 380   # caixa de narração
LARG_TEL = 410     # caixa de ligação
LARG_CENA = 440    # legenda das ilustrações em tela cheia


class Menu:
    def __init__(self, titulo, opcoes, ao_escolher, subtitulo="", cancelavel=True, img=None):
        self.titulo, self.opcoes, self.cb = titulo, opcoes, ao_escolher
        self.subtitulo, self.cancelavel, self.img = subtitulo, cancelavel, img
        self.painel = None   # função(valor_selecionado) -> lista de blocos para o painel lateral
        self.sel = next((i for i, o in enumerate(opcoes) if o[2]), 0)
        self.rects = []


class Jogo:
    def __init__(self):
        # Windows com zoom de tela (125%/150%) "estica" janelas antigas e deixa tudo borrado.
        # Declarar o programa como DPI-aware faz o jogo usar os pixels reais do monitor.
        if sys.platform.startswith("win"):
            try:
                import ctypes
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)
                except Exception:
                    ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Tudo em seu lugar — Projeto Detetive")
        info = pygame.display.Info()
        self.android = "ANDROID_ROOT" in os.environ or "ANDROID_ARGUMENT" in os.environ
        self.tela_cheia = True   # para a apresentação; F11 alterna com janela
        self._tam_janela = None
        if info.current_w > 0:
            w = min(1600, max(800, int(info.current_w * 0.8)))
            self._tam_janela = (w, int(w * 9 / 16))
        self._aplicar_modo_tela()
        self.toque = self.android
        self.mundo = pygame.Surface((LW, LH))
        self.relogio = pygame.time.Clock()
        self.img = {}
        for nome, dados in ASSETS.items():
            try:
                bruto = base64.b64decode(dados)
                dica = "img.png" if bruto[:4] == b"\x89PNG" else "img.jpg"
                self.img[nome] = pygame.image.load(io.BytesIO(bruto), dica).convert()
            except Exception:
                pass
        self.som = SomPygame()
        self.salas_cache = {}
        self.luz_cache = {}
        self._recalcular()
        self.modo = "titulo"
        self.menu = None
        self.caso = None
        self.t = 0.0
        self.toast = None
        self.texto_codigo = ""
        self.rodando = True
        self.titulo_menu()

    def _aplicar_modo_tela(self):
        if self.tela_cheia or self.android or not self._tam_janela:
            self.tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.tela = pygame.display.set_mode(self._tam_janela, pygame.RESIZABLE)
        if hasattr(self, "f"):
            self._recalcular()

    def alternar_tela_cheia(self):
        if self.android:
            return
        self.tela_cheia = not self.tela_cheia
        self._aplicar_modo_tela()

    # ------------------------------------------------------------ escala / fontes
    def _recalcular(self):
        W, H = self.tela.get_size()
        self.s = min(W / LW, H / LH)
        self.ox = (W - LW * self.s) / 2
        self.oy = (H - LH * self.s) / 2
        px = lambda n: max(10, int(n * self.s))
        sim = lambda n: carregar_fonte("simbolos", px(n))
        maq = lambda n: FonteMista(carregar_fonte("maquina", px(n)), sim(n))     # Special Elite
        pix = lambda n, b=False: FonteMista(carregar_fonte("pixel", px(n), b), sim(n))  # Pixelify Sans
        self.f = {
            "titulo": maq(22), "h1": maq(13), "h2": maq(10),
            "narra": maq(9), "carta": maq(8.5),
            "corpo": pix(8.5), "corpo_b": pix(8.5, True), "peq": pix(7), "mini": pix(6.2),
        }
        self.retratos = {}

    def P(self, x, y):
        return (int(self.ox + x * self.s), int(self.oy + y * self.s))

    def RR(self, x, y, w, h):
        return pygame.Rect(int(self.ox + x * self.s), int(self.oy + y * self.s), int(w * self.s), int(h * self.s))

    def retrato(self, chave, lado):
        k = (chave, int(lado))
        if k not in self.retratos and chave in self.img:
            self.retratos[k] = pygame.transform.smoothscale(self.img[chave], (int(lado), int(lado)))
        return self.retratos.get(k)

    def imagem_larga(self, chave, largura):
        k = (chave, "L", int(largura))
        if k not in self.retratos and chave in self.img:
            im = self.img[chave]
            h = int(largura * im.get_height() / im.get_width())
            self.retratos[k] = pygame.transform.smoothscale(im, (int(largura), h))
        return self.retratos.get(k)

    # ------------------------------------------------------------ texto
    def texto(self, txt, fonte, cor, x, y, centro=False, sombra=True):
        f = self.f[fonte]
        img = f.render(txt, True, cor)
        if centro:
            x -= img.get_width() // 2
        if sombra:
            self.tela.blit(f.render(txt, True, (0, 0, 0)), (x + 1, y + 1))
        self.tela.blit(img, (x, y))
        return img.get_width()

    def bloco(self, txt, fonte, cor, x, y, largura, entre=1.15, centro=False):
        f = self.f[fonte]
        for linha in quebrar(txt, f, largura):
            if centro:
                self.texto(linha, fonte, cor, x + largura // 2, y, centro=True, sombra=False)
            else:
                self.tela.blit(f.render(linha, True, cor), (x, y))
            y += int(f.get_linesize() * entre)
        return y

    def painel(self, rect, cor=None, borda=None, alfa=235):
        sup = pygame.Surface(rect.size, pygame.SRCALPHA)
        sup.fill((cor or C["card"]) + (alfa,))
        self.tela.blit(sup, rect.topleft)
        pygame.draw.rect(self.tela, borda or C["linha"], rect, max(1, int(self.s * 0.6)))

    # ============================================================ TELAS FORA DO JOGO
    def titulo_menu(self):
        self.modo = "titulo"
        self.caso = None
        self.som.musica("tema")
        sv = ler_save()
        ops = []
        if sv:
            c_ = sv["caso"]
            ops.append((f"Continuar caso salvo — Capítulo {c_.get('cap', 1)} · {c_.get('pontos', 0)} pts",
                        "continuar", True))
        self.menu = Menu("", ops + [("Novo caso (modo história)", "novo", True),
                              ("Abrir caso pelo código", "codigo", True),
                              ("Como jogar", "como", True), ("Recordes", "recordes", True),
                              ("Sair", "sair", True)], self._escolha_titulo, cancelavel=False)

    def _escolha_titulo(self, v):
        if v == "continuar":
            if not self.carregar_jogo():
                self.titulo_menu()
                self.mostrar_toast("Não foi possível abrir o jogo salvo.")
        elif v == "novo":
            if ler_save():
                self.menu = Menu("Começar um caso novo?",
                                 [("Sim — começar do zero (o jogo salvo continua guardado até você salvar de novo)", "sim", True),
                                  ("Não, voltar", "nao", True)],
                                 lambda r: self.novo_jogo() if r == "sim" else self.titulo_menu(),
                                 cancelavel=False)
            else:
                self.novo_jogo()
        elif v == "codigo":
            self.modo, self.menu, self.texto_codigo = "codigo", None, ""
        elif v == "como":
            self.modo, self.menu = "como", None
            self.briefing = None
        elif v == "recordes":
            self.modo, self.menu = "recordes", None
        elif v == "sair":
            self.rodando = False

    def desenhar_titulo(self):
        W, H = self.tela.get_size()
        self.tela.fill(C["bg"])
        self._fundo_inteiro("salao", 60)
        r = self.retrato("helena", 120 * self.s)
        if r:
            self.tela.blit(r, self.P(30, 50))
            pygame.draw.rect(self.tela, C["ambar"], (*self.P(30, 50), r.get_width(), r.get_height()), 2)
        x = self.P(170, 0)[0]
        self.texto(TITULO, "titulo", C["texto"], x, self.P(0, 46)[1])
        self.texto("Quem matou o professor Augusto Nakamura?", "h2", C["ambar"], x, self.P(0, 76)[1])
        self.bloco("Nova Orleans, 2026. Um jogo de investigação em modo história.", "corpo",
                   C["fraco"], x, self.P(0, 92)[1], int(280 * self.s))
        if self.menu:
            self.desenhar_opcoes(self.menu, 170, 112, 200)
        self.texto("F11: alternar tela cheia / janela", "peq", C["ambar"], W // 2, self.P(0, 236)[1], centro=True)
        self.texto(SUBTITULO, "peq", C["fraco"], W // 2, self.P(0, 248)[1], centro=True)
        self.texto(EQUIPE, "peq", C["fraco"], W // 2, self.P(0, 258)[1], centro=True)

    def desenhar_opcoes(self, menu, x, y, w, altura=17):
        menu.rects = []
        for i, (rot, val, ok) in enumerate(menu.opcoes):
            r = self.RR(x, y + i * altura, w, altura - 3)
            sel = i == menu.sel
            cor_bg = C["ambar"] if sel and ok else (C["card2"] if ok else (20, 27, 32))
            pygame.draw.rect(self.tela, cor_bg, r, border_radius=int(2 * self.s))
            cor_t = C["tinta"] if sel and ok else (C["texto"] if ok else (80, 92, 100))
            prefixo = "▶ " if sel and ok else "   "
            txt = self._cortar(prefixo + rot, "corpo_b", r.w - int(12 * self.s))
            self.tela.blit(self.f["corpo_b"].render(txt, True, cor_t),
                           (r.x + int(6 * self.s), r.y + (r.h - self.f["corpo_b"].get_height()) // 2))
            menu.rects.append(r)

    def desenhar_como(self):
        self.desenhar_briefing("E / ESC — Voltar ao menu")

    def desenhar_codigo(self):
        self.tela.fill(C["bg"])
        W, _ = self.tela.get_size()
        self.texto("Abrir caso pelo código", "h1", C["texto"], W // 2, self.P(0, 70)[1], centro=True)
        self.bloco("O mesmo código gera o mesmo sorteio — bom para comparar pontuação com a outra equipe.",
                   "corpo", C["fraco"], self.P(110, 0)[0], self.P(0, 92)[1], int(260 * self.s), centro=True)
        r = self.RR(170, 120, 140, 26)
        pygame.draw.rect(self.tela, C["papel"], r)
        self.texto(self.texto_codigo + ("_" if int(self.t * 2) % 2 == 0 else " "), "h1", C["tinta"],
                   r.centerx, r.y + int(4 * self.s), centro=True, sombra=False)
        self.texto("Digite os números e aperte Enter · ESC volta", "peq", C["fraco"], W // 2,
                   self.P(0, 156)[1], centro=True)

    def desenhar_recordes(self):
        self.tela.fill(C["bg"])
        W, _ = self.tela.get_size()
        self.texto("Recordes", "h1", C["texto"], W // 2, self.P(0, 20)[1], centro=True)
        dados = ler_recordes()
        y = self.P(0, 48)[1]
        if not dados:
            self.texto("Nenhum caso encerrado ainda.", "corpo", C["fraco"], W // 2, y, centro=True)
        for i, r in enumerate(dados, 1):
            self.texto(f"{i}º  {r['pontos']} pts — {r['titulo']}  ·  caso nº {r['codigo']}  ·  "
                       f"{r['resultado']}  ·  {r['data']}", "corpo", C["texto"], W // 2, y, centro=True)
            y += int(14 * self.s)
        self.texto("ESC ou E para voltar", "peq", C["fraco"], W // 2, self.P(0, 258)[1], centro=True)

    # ============================================================ PARTIDA
    def novo_jogo(self, codigo=None):
        self.caso = Caso(codigo)
        self.modo = "jogo"
        self.menu = None
        self.fila = []
        self.balao = None
        self.carta = None
        self.painel_aberto = None
        self.fade = 0.0
        self.fade_alvo = 0.0
        self.flash = None
        self.tremor = 0.0
        self.espera = 0.0
        self.capitulo_titulo = None
        self.objetivo = ""
        self.chegou = set()
        self.ultimo_toque = 0.0
        self.t_passo = 0.0
        self.scroll = 0
        self.dpad = {}
        self.ents = {}
        self.player = Ent("helena", "Helena", 0, 0, PALETAS["helena"], True, "helena")
        self.briefing = "inicio"   # tela de comandos antes da história começar
        self.som.musica("tema")

    # ---------------- salvar / carregar (igual videogame)
    def estado_salvo(self):
        c = self.caso
        d = dict(c.__dict__)
        d["inicio"] = time.time() - c.inicio       # guarda o tempo real já jogado
        return {"versao": 1, "caso": d, "objetivo": self.objetivo, "chegou": set(self.chegou),
                "pos": (self.player.x, self.player.y, self.player.dir),
                "forcado": getattr(self, "_forcado", False),
                "resumo": f"Cap. {c.cap} · {texto_relogio(c.relogio)} · {c.pontos} pts"}

    def salvar_jogo(self):
        if self.modo != "jogo" or not self.caso or getattr(self, "briefing", None) == "inicio":
            return False
        ok = gravar_save(self.estado_salvo())
        if ok:
            self._cap_salvo = self.caso.cap
            self.som.sfx("papel")
        return ok

    def carregar_jogo(self):
        sv = ler_save()
        if not sv:
            return False
        try:
            self.novo_jogo(sv["caso"]["codigo"])
            c = self.caso
            dados = dict(sv["caso"])
            dados["inicio"] = time.time() - dados.get("inicio", 0)
            c.__dict__.update(dados)
            self.briefing = None
            self.objetivo = sv.get("objetivo", "")
            self.chegou = set(sv.get("chegou", ()))
            self._forcado = sv.get("forcado", False)
            self._cap_salvo = c.cap
            self.carregar_sala(c.sala)
            x, y, d = sv["pos"]
            self.player.x, self.player.y, self.player.dir = x, y, d
            self.na_saida = True
            self.fade, self.fade_alvo = 1.0, 0.0
            self.musica_ambiente()
            self.mostrar_toast(f"Jogo carregado — {sv['resumo']}")
            return True
        except Exception:
            return False

    def fechar_briefing(self):
        origem = self.briefing
        self.briefing = None
        self.som.sfx("clique")
        if origem == "inicio":
            self.prologo()

    # ---------------- salas e personagens
    def carregar_sala(self, sid, tx=None, ty=None):
        c = self.caso
        c.sala = sid
        if not hasattr(c, "visitadas"):
            c.visitadas = set()
        c.visitadas.add(sid)
        if sid not in self.salas_cache:
            self.salas_cache[sid] = construir_sala(sid)
        self.fundo, self.solido = self.salas_cache[sid]
        if tx is None:
            tx, ty = SALAS[sid]["inicio"]
        self.player.x, self.player.y = tx * T + T / 2, ty * T + T - 2
        self.player.visivel = True
        self.player.dir = "cima" if ty > 7 else "baixo"
        self.ents = {"helena": self.player}
        self._popular(sid)
        self.na_saida = True  # evita reabrir o mapa ao nascer na porta

    def _npc(self, eid, nome, tx, ty, pal_key=None, retrato=None, dir="baixo", pal=None, longo=None):
        p = pal or PALETAS[pal_key]
        e = Ent(eid, nome, tx * T + T / 2, ty * T + T - 2, p,
                CABELO_LONGO.get(pal_key, True) if longo is None else longo, retrato)
        e.dir = dir
        self.ents[eid] = e
        return e

    def _popular(self, sid):
        c = self.caso
        if sid == "salao" and c.cap >= 2:
            self._npc("sofia", "Sofia", 16, 8, "sofia", "sofia")
        if sid == "salao" and c.cap == 2:
            self._npc("al1", "Formando", 6, 5, "aluno1", None, dir="direita")
            self._npc("al2", "Formanda", 23, 5, "aluno2", None, dir="esquerda")
            self._npc("al3", "Formando", 9, 12, "aluno3", None, dir="cima")
        if sid == "banheiro_baile" and c.cap == 2:
            self._npc("olivia", "Olívia", 12, 8, "olivia", "olivia", dir="esquerda")
        if sid == "salao" and c.cap == 2:
            self._npc("rodrigo", "Rodrigo", 24, 10, "rodrigo", "rodrigo", dir="esquerda")
        if sid == "tulane" and c.cap == 3:
            self._npc("olivia", "Olívia", 11, 6, "olivia", "olivia", dir="esquerda")
        if sid == "banheiro_tulane" and c.cap == 3:
            self._npc("rodrigo", "Rodrigo", 7, 5, "rodrigo", "rodrigo", dir="baixo")
        if sid == "interrogatorio" and c.cap >= 4:
            self._npc("olivia", "Olívia", 18, 8, "olivia", "olivia", dir="esquerda")
            if "entrevista" not in c.feitos:
                for i, a in enumerate(c.alunas):
                    pal = {"cabelo": a["cabelo"], "roupa": a["roupa"], "pele": "#ecc7aa",
                           "calca": "#22262a"}
                    self._npc(a["id"], a["nome"].split()[0], 4 + i * 2, 10, pal=pal, longo=True,
                              retrato="ruivas", dir="baixo")
            self._npc("rodrigo", "Rodrigo", 20, 11, "rodrigo", "rodrigo", dir="esquerda")
        if sid == "casa" and c.cap >= 5:
            self._npc("rodrigo", "Rodrigo", 7, 10, "rodrigo", "rodrigo", dir="direita")
            m = Ent("max", "Max", 23 * T, 12 * T, cao=True, retrato="max")
            m.dir = "esquerda"
            self.ents["max"] = m

    def objeto_em(self, sid):
        """Lista de pontos interativos da sala: (rect_mundo, chave, nome)."""
        out = []
        for tipo, tx, ty, tw, th, sol, p in SALAS[sid]["moveis"]:
            if p is None:
                continue
            r = pygame.Rect(tx * T, ty * T, tw * T, th * T)
            nome = "Telefone" if p == "telefone" else PONTOS_SALA[sid][p]
            out.append((r, p, nome))
        return out

    # ---------------- fila de cena (cutscenes)
    def cena(self, *acoes):
        self.fila.extend(acoes)

    def cena_ja(self, *acoes):
        self.fila = list(acoes) + self.fila

    def ocupado(self):
        return bool(self.fila or self.balao or self.carta or self.menu or self.painel_aberto
                    or self.espera > 0 or self.capitulo_titulo or self._andando_cena())

    def _andando_cena(self):
        return any(e.alvo for e in self.ents.values())

    def _processar_fila(self):
        while self.fila and not (self.balao or self.carta or self.menu or self.espera > 0
                                 or self.capitulo_titulo or self._andando_cena()
                                 or abs(self.fade - self.fade_alvo) > 0.01):
            a = self.fila.pop(0)
            tipo = a[0]
            if tipo == "narra":
                pags = self._paginar(a[1], "narra", LARG_NARRA - 22, 4)
                self.balao = {"tipo": "narra", "pags": pags, "i": 0, "n": 0.0, "voz": "voz_narra"}
                self.som.sfx("papel")
            elif tipo == "fala":
                ent = self.ents.get(a[1])
                tem_ret = bool(ent and ent.retrato and ent.retrato in self.img)
                pags = self._paginar(a[2], "corpo", LARG_FALA - (48 if tem_ret else 10) - 10, 4)
                self.balao = {"tipo": "fala", "ent": a[1], "nome": ent.nome if ent else a[1],
                              "retrato": ent.retrato if ent else None, "pags": pags, "i": 0, "n": 0.0,
                              "voz": voz_de(a[1])}
                self.som.sfx("balao")
            elif tipo == "cena_img":
                self.balao = {"tipo": "cena", "img": a[1], "pags": self._paginar(a[2], "narra", LARG_CENA - 24, 3)
                              if a[2] else [""], "i": 0, "n": 0.0, "voz": "voz_narra",
                              "data": a[3] if len(a) > 3 else None}
                self.som.sfx("papel")
            elif tipo == "tel":
                self.balao = {"tipo": "tel", "retrato": a[1], "nome": a[2],
                              "pags": self._paginar(a[3], "corpo", LARG_TEL - 84, 4),
                              "i": 0, "n": 0.0, "voz": "voz_tel"}
                self.som.sfx("balao")
            elif tipo == "anda":
                e = self.ents.get(a[1])
                if e:
                    e.alvo = (a[2] * T + T / 2, a[3] * T + T - 2)
            elif tipo == "vira":
                if a[1] in self.ents:
                    self.ents[a[1]].dir = a[2]
            elif tipo == "espera":
                self.espera = a[1]
            elif tipo == "som":
                self.som.sfx(a[1])
            elif tipo == "musica":
                self.som.musica(a[1])
            elif tipo == "fade":
                self.fade_alvo = 1.0 if a[1] == "out" else 0.0
            elif tipo == "sala":
                self.carregar_sala(a[1], *(a[2:4] if len(a) > 2 else (None, None)))
            elif tipo == "flash":
                self.flash = [a[1], a[2], a[2]]
            elif tipo == "tremor":
                self.tremor = a[1]
            elif tipo == "fn":
                a[1]()
            elif tipo == "carta":
                self.carta = dict(a[1], n=0.0)
                self.som.sfx("papel")
            elif tipo == "cap":
                self.capitulo_titulo = [a[1], 1.6, 0.0]
                self.som.sfx("evento")
            elif tipo == "hora":
                self.caso.relogio = a[1]
            elif tipo == "objetivo":
                self.objetivo = a[1]
            elif tipo == "mostra":
                if a[1] in self.ents:
                    self.ents[a[1]].visivel = a[2]
            elif tipo == "npc":
                self._npc(*a[1:])
            elif tipo == "remove":
                self.ents.pop(a[1], None)
            elif tipo == "menu":
                self.menu = a[1]

    def _paginar(self, texto, fonte, largura_logica, max_linhas):
        """Quebra o texto na largura REAL do balão e divide em páginas de até N linhas."""
        linhas = [l for l in quebrar(texto, self.f[fonte], int(largura_logica * self.s))]
        return ["\n".join(linhas[i:i + max_linhas]) for i in range(0, len(linhas), max_linhas)] or [""]

    def _desenhar_digitado(self, texto, n, fonte, cor, x, y, entre=1.12):
        """Desenha as linhas já quebradas mostrando só as n primeiras letras (sem pular palavras)."""
        f = self.f[fonte]
        resto = int(n)
        for linha in texto.split("\n"):
            if resto <= 0:
                break
            self.tela.blit(f.render(linha[:resto], True, cor), (x, y))
            resto -= len(linha) + 1
            y += int(f.get_linesize() * entre)
        return y

    def _seta_baixo(self, cx, cy, cor):
        s = self.s
        pygame.draw.polygon(self.tela, cor, [(cx - int(3 * s), cy - int(2 * s)), (cx + int(3 * s), cy - int(2 * s)),
                                            (cx, cy + int(2 * s))])

    # ============================================================ HISTÓRIA
    def prologo(self):
        c = self.caso
        c.cap = 0
        self.carregar_sala("salao", 14, 12)
        self.player.visivel = False
        self._npc("al1", "Estudante", 13, 6, "aluno1", None)
        self._npc("al2", "Estudante", 17, 6, "aluno2", None)
        self._npc("al3", "Estudante", 6, 8, "aluno3", None, dir="direita")
        self._npc("al4", "Estudante", 22, 8, "aluno1", None, dir="esquerda", longo=False)
        self.cena(
            ("musica", "tema"), ("fn", lambda: setattr(self.caso, "relogio", MARCOS["prologo"])),
            ("cena_img", "salao", "Nova Orleans, 3 de fevereiro de 2026. Baile de formatura de Arquitetura "
                                  "da Tulane University. A festa está quase no fim."),
            ("cap", CAPITULOS[0]), ("som", "murmurio"),
            ("narra", "Música alta, taças erguidas, fotos com a família. Ninguém repara nos minutos que passam. "
                      "Ninguém repara em quem não está mais no salão."),
            ("fala", "al3", "Já é quase meia-noite. Cadê o coordenador? Ele não ia fechar a festa?"),
            ("fala", "al4", "Vi ele saindo do salão faz horas. Achei que tinha ido embora."),
            ("espera", 0.6),
            ("fala", "al2", "Alguém viu o professor Nakamura? Ele ia fazer o discurso de encerramento…"),
            ("fala", "al1", "O paletó dele ainda está na cadeira. Ele não foi embora sem o paletó. Vou ver no banheiro."),
            ("anda", "al1", 27, 6), ("anda", "al1", 27, 7), ("vira", "al1", "direita"),
            ("som", "trinco"), ("espera", 0.5), ("som", "trinco"), ("som", "hein"),
            ("fala", "al1", "Professor? …Professor Nakamura?"),
            ("espera", 0.9), ("som", "trinco"),
            ("fala", "al1", "A porta está trancada! Professor? PROFESSOR?! Me ajudem aqui!"),
            ("anda", "al2", 26, 7),
            ("fala", "al2", "No três, a gente força! Um… dois… TRÊS!"),
            ("som", "porta_arrombada"), ("tremor", 0.4),
            ("fade", "out"), ("fn", self._prologo_banheiro), ("fn", lambda: self.caso.marco("porta")),
            ("fade", "in"),
            ("anda", "al1", 4, 6), ("vira", "al1", "baixo"),
            ("som", "grito"), ("tremor", 0.6), ("flash", (150, 20, 24), 0.8), ("espera", 0.5),
            ("som", "grito_m"),
            ("fala", "al1", "NÃO… Professor Nakamura!"),
            ("espera", 0.8),
            ("cena_img", "banheiro_baile", "23h58. Atrás da porta trancada, no chão do banheiro, o "
                                           "coordenador de Arquitetura."),
            ("fala", "al2", "Ele… ele ficou aqui a festa inteira? Enquanto a gente dançava lá fora?"),
            ("cena_img", "nakamura", "Augusto Nakamura está morto — esfaqueado no coração. O corpo ficou "
                                     "trancado aqui enquanto a festa continuava lá fora."),
            ("som", "cochicho"),
            ("npc", "olivia", "Olívia", 0, 7, "olivia", "olivia", "direita"),
            ("npc", "rodrigo", "Rodrigo", 0, 8, "rodrigo", "rodrigo", "direita"),
            ("anda", "olivia", 3, 8), ("anda", "rodrigo", 2, 9),
            ("fala", "olivia", "Polícia de Nova Orleans! Policial Olívia. Ninguém toca em nada."),
            ("fala", "rodrigo", "Policial Rodrigo. Todo mundo de volta ao salão — ninguém sai da festa "
                                "até a gente liberar."),
            ("narra", "23h59 de 3 de fevereiro. Olívia e Rodrigo isolam o banheiro, mas não sabem por onde "
                      "começar. A promotoria dá 48 horas para apontar um culpado. Sofia, sobrinha do "
                      "professor, liga para a única detetive que conhece."),
            ("fade", "out"), ("fn", self._ir_cap1), ("fade", "in"),
        )

    def _prologo_banheiro(self):
        self.carregar_sala("banheiro_baile", 2, 7)
        self.player.visivel = False
        self._npc("al1", "Estudante", 1, 7, "aluno1", None, dir="direita")
        self._npc("al2", "Estudante", 2, 9, "aluno2", None, dir="direita")

    def _ir_cap1(self):
        c = self.caso
        c.cap = 1
        self.carregar_sala("escritorio", 14, 9)
        self.cena(
            ("fn", lambda: self.caso.marco("ligacao")),
            ("musica", "investigacao"), ("cap", CAPITULOS[1]),
            ("cena_img", "helena", "Meia-noite. No escritório da detetive Helena Cortez, 23 anos, "
                                   "ex-aluna de Arquitetura da Tulane. O telefone toca."),
            ("objetivo", "Atenda o telefone na mesa (aproxime-se e aperte E)."),
        )
        self.ultimo_toque = -10

    def atender_telefone(self):
        c = self.caso
        c.feitos.add("telefone")
        self.som.sfx("gravador")
        c.ganhar("E", "F", "G")
        self.cena(
            ("cena_img", "sofia", "Do outro lado da linha, no meio do salão do baile, Sofia Mori Nakamura."),
            ("tel", "sofia", "Sofia Mori Nakamura", "Helena? É a Sofia… Sofia Mori Nakamura, da "
             "Arquitetura. Desculpa a hora."),
            ("som", "soluco"),
            ("tel", "sofia", "Sofia Mori Nakamura", "Meu tio, o professor Nakamura… acharam ele morto agora, "
             "trancado no banheiro do baile. A polícia está perdida. Você é a única detetive que eu conheço."),
            ("fala", "helena", "Eu estudei Arquitetura na Tulane em 2020, antes de mudar para a perícia. "
                               "Eu conhecia o seu tio…"),
            ("tel", "sofia", "Sofia Mori Nakamura", "Por favor, vem pra cá. Eu te espero no salão. "
             "Ninguém mexeu em nada no banheiro."),
            ("fala", "helena", "Estou indo."),
            ("som", "gravador"), ("espera", 0.7),
            ("narra", "A linha fica muda. Professor Augusto Nakamura. Fazia seis anos que você não ouvia esse "
                      "nome — e, por algum motivo, ele te deixa com frio."),
            ("fn", lambda: self.feito_pts("conversa")),
            ("objetivo", "Saia pela porta e vá ao Salão do Baile."),
        )

    def feito_pts(self, tipo):
        self.caso.pontos += PONTOS[tipo]

    def ao_chegar(self, sid):
        c = self.caso
        if sid == "salao" and c.cap == 1 and "telefone" in c.feitos:
            c.cap = 2
            self._popular("salao")
            self.cena(
                ("som", "cochicho"),
                ("cena_img", "salao", "O salão do baile, de madrugada. A música parou. Os formandos "
                                      "cochicham em grupos; ninguém pode ir embora."),
                ("cap", CAPITULOS[2]), ("musica", "investigacao"),
                ("anda", "sofia", 15, 10), ("vira", "sofia", "baixo"),
                ("fala", "sofia", "Helena! Obrigada por vir. O banheiro é por aquela porta, à direita. "
                                  "A policial Olívia está lá com… com ele."),
                ("fala", "sofia", "Os formandos estão assustados. Se precisar de alguém, eles estão todos aqui."),
                ("objetivo", ""), ("fn", self.atualizar_objetivo),
            )
        elif sid == "banheiro_baile" and c.cap == 2 and "c2b" not in self.chegou:
            self.chegou.add("c2b")
            self.cena(
                ("som", "suspiro"),
                ("cena_img", "banheiro_baile", "A cena do crime. Fita da polícia, espelhos dourados… e o "
                                               "professor Nakamura caído no chão."),
                ("narra", "A porta arrombada range atrás de você. Cheiro de ferro. Luz fria. Por um segundo, "
                          "você tem a sensação estranha de já ter estado num lugar assim."),
                ("fala", "olivia", "Detetive Cortez? Policial Olívia. O corpo ainda está aqui, não mexemos em "
                                   "nada. Fale comigo e examine o que precisar."),
            )
        elif sid == "tulane" and c.cap == 3 and "c3t" not in self.chegou:
            self.chegou.add("c3t")
            self.cena(("som", "trovao"),
                      ("cena_img", "tulane", "Tulane University, ainda de madrugada. Prédios antigos, chuva, e "
                                             "um arquivo com o nome de todos os alunos de 2020."),
                      ("fala", "helena", "Seis anos sem pisar aqui. Eu larguei a Arquitetura em 2020… e quase "
                                         "não lembro desse último ano."),
                      ("narra", "Os corredores parecem familiares e estranhos ao mesmo tempo, como uma "
                                "lembrança que alguém apagou pela metade."))
        elif sid == "banheiro_tulane" and c.cap == 3 and "c3b" not in self.chegou:
            self.chegou.add("c3b")
            self.cena(("cena_img", "banheiro_tulane", "O banheiro do campus. As câmeras daqui gravam há "
                                                      "anos… e ninguém nunca olhou as imagens antigas."),
                      ("fala", "rodrigo", "A segurança diz que ninguém pediu essas gravações em seis anos. "
                                          "Se o professor escondia alguma coisa, está aqui."),
                      ("som", "coracao"),
                      ("narra", "Você olha para os fundos do prédio e sente o estômago gelar. Não sabe por quê."))
        elif sid == "interrogatorio" and c.cap == 4 and "c4" not in self.chegou:
            self.chegou.add("c4")
            self.cena(
                ("som", "cochicho"),
                ("cena_img", "ruivas", "Quarta-feira, 10 da manhã. Na Sala de Interrogatório, as quatro "
                                       "primeiras ruivas dos registros de 2020 esperam, nervosas."),
                ("fala", "olivia", "Detetive Cortez. Eu e o Rodrigo convocamos as quatro primeiras ruivas dos registros "
                                   "de 2020. Estão naquele banco."),
                ("fala", "olivia", "Converse com cada uma e compare com o que as câmeras mostraram. "
                                   "Depois decida: liberar… ou acusar."),
                ("fn", self.atualizar_objetivo),
            )
        elif sid == "casa" and c.cap == 5 and "c5" not in self.chegou:
            self.chegou.add("c5")
            self.cena(
                ("som", "rosnado"),
                ("cena_img", "casa", "Quarta-feira à noite. A casa de Augusto Nakamura: luzes acesas, "
                                     "silêncio… e um cachorro rosnando no quintal."),
                ("fala", "rodrigo", "A polícia já revistou tudo uma vez. Mas talvez estar aqui desperte "
                                    "alguma lembrança em você."),
                ("fala", "helena", "Esta rua… eu conheço esta rua. Não sei de onde."),
                ("narra", "O portão range. No quintal, uma sombra se levanta devagar e fica olhando para você."),
                ("fn", self.atualizar_objetivo),
            )

    def atualizar_objetivo(self):
        c = self.caso
        objs = OBJETIVOS.get(c.cap, [])
        feitos = sum(1 for o in objs if o in c.feitos)
        textos = {
            2: "Investigue a cena do crime: fale com Sofia e Olívia e examine o banheiro do baile",
            3: ("Procure onde Beatriz pode estar e descubra quem era a testemunha ruiva"
                if "cam_univ" in c.pistas else
                "Encontre as gravações antigas nas câmeras do banheiro da Tulane"),
            4: "Interrogue as quatro alunas ruivas e fale com a policial Olívia",
            5: "Investigue a casa do professor com o policial Rodrigo",
            6: "Compare as gravações no computador da Sala de Interrogatório e fale com Olívia",
        }
        if c.cap in textos:
            self.objetivo = f"{textos[c.cap]} ({feitos}/{len(objs)})"

    def marcar(self, chave):
        c = self.caso
        if chave in c.feitos:
            return
        c.feitos.add(chave)
        self.atualizar_objetivo()
        if c.capitulo_completo():
            self.cena(("fn", lambda n=c.cap: self.fim_de_capitulo(n)))

    def fim_de_capitulo(self, n):
        c = self.caso
        if n != c.cap or not c.capitulo_completo():
            return
        if c.cap == 2:
            self.cena(
                ("espera", 0.5),
                ("narra", "A cena do crime está examinada. Helena, Olívia e Sofia se reúnem num canto do "
                          "salão vazio para juntar as peças."),
                ("fade", "out"), ("fn", self._montar_reuniao), ("fade", "in"),
                ("musica", "tensao"),
                ("fala", "helena", "Uma mulher ruiva entrou no banheiro logo depois do professor, às 22:41. "
                                   "Às 22:47 saiu sozinha e trancou a porta."),
                ("som", "hm"),
                ("fala", "olivia", "Um golpe só, no coração. Isso não foi briga: foi ódio. Quem odiaria o "
                                   "coordenador a esse ponto?"),
                ("fala", "rodrigo", "Ódio assim não nasce numa noite. Se existe um motivo, ele está no passado "
                                    "do professor — e o passado dele é a Tulane."),
                ("espera", 0.6),
                ("som", "suspiro"),
                ("fala", "sofia", "Falando em passado… em 2020 a minha melhor amiga foi embora da Tulane. "
                                  "Olha, essa é ela."),
                ("cena_img", "beatriz", "Na tela do celular de Sofia, uma foto antiga: Beatriz Valença, aluna "
                                        "de Arquitetura, a \"Bia\"."),
                ("som", "soluco"),
                ("fala", "sofia", "Todo mundo diz que ela foi para um intercâmbio na Itália em maio de 2020. "
                                  "Mas depois disso ela nunca mais me respondeu direito."),
                ("fala", "olivia", "A segurança da Tulane guarda as gravações das câmeras dos banheiros por "
                                   "anos. Vamos ver o que o professor fazia lá."),
                ("fala", "rodrigo", "Eu vou com você, Helena. A Olívia leva os registros dos alunos."),
                ("fala", "helena", "Então vamos à Tulane. Agora."),
                ("fn", lambda: self._novo_cap(3, "Encontre as gravações antigas nas câmeras do banheiro "
                                                 "da Tulane (saia pelo mapa)")),
            )
        elif c.cap == 3:
            self.cena(
                ("fala", "helena", "Cinco alunas ruivas em 2020. A polícia vai convocar as quatro "
                                   "primeiras. E a quinta… sou eu."),
                ("fala", "olivia", "Você também vai ser entrevistada, Helena. Como qualquer outra aluna. É o "
                                   "protocolo."),
                ("fala", "helena", "Eu sei. Não tenho nada a esconder."),
                ("narra", "Lá fora, a chuva para. Ninguém dorme naquela madrugada."),
                ("fn", lambda: self._novo_cap(4, "Vá à Sala de Interrogatório")),
            )
        elif c.cap == 5:
            self.cena(
                ("fala", "rodrigo", "Helena… o Max nunca late assim para estranhos. Vamos voltar à "
                                    "delegacia e comparar as câmeras do baile com as suas imagens."),
                ("fala", "helena", "Você está achando que…"),
                ("fala", "rodrigo", "Eu não estou achando nada. Ainda. As imagens vão dizer."),
                ("narra", "O caminho de volta é em silêncio. Pelo vidro do carro, as luzes de Nova Orleans "
                          "passam borradas. Max continua latindo, cada vez mais longe."),
                ("fn", lambda: self._novo_cap(6, "Volte à Sala de Interrogatório e use o computador")),
            )

    def _montar_reuniao(self):
        """Reúne Helena, Olívia, Rodrigo e Sofia no salão para a cena de ligação entre os capítulos 2 e 3."""
        self.carregar_sala("salao", 14, 11)
        self.player.dir = "cima"
        if "sofia" in self.ents:
            self.ents["sofia"].x, self.ents["sofia"].y = 13 * T + T / 2, 9 * T + T - 2
            self.ents["sofia"].dir = "baixo"
        self._npc("olivia", "Olívia", 16, 10, "olivia", "olivia", dir="esquerda")
        if "rodrigo" in self.ents:
            self.ents["rodrigo"].x, self.ents["rodrigo"].y = 15 * T + T / 2, 8 * T + T - 2
            self.ents["rodrigo"].dir = "baixo"

    def _novo_cap(self, n, objetivo):
        self.caso.cap = n
        self.cena(("fn", self.atualizar_objetivo))
        if n == 4:  # as alunas são convocadas na manhã de quarta
            self.caso.marco("convocacao")
        if n == 5:  # Rodrigo leva Helena à casa do professor à noite
            self.caso.marco("noite_casa")
        self.cena(("cap", CAPITULOS[n]), ("objetivo", objetivo + "."))
        if n == 6:
            self.cena(("musica", "tensao"))

    # ---------------- interações
    def interagir(self):
        c = self.caso
        alvo = self.alvo_proximo()
        if not alvo:
            return
        tipo, val = alvo[0], alvo[1]
        if tipo == "npc":
            self.falar(val)
        elif tipo == "ponto":
            if val == "telefone":
                if c.cap == 1 and "telefone" not in c.feitos:
                    self.atender_telefone()
                else:
                    self.cena(("fala", "helena", "Nenhuma ligação nova."))
            else:
                self.examinar(val)

    def alvo_proximo(self):
        px, py = self.player.x, self.player.y - 6
        melhor, dist = None, 26
        for eid, e in self.ents.items():
            if eid == "helena" or not e.visivel:
                continue
            d = math.hypot(e.x - px, (e.y - 6) - py)
            if d < dist:
                melhor, dist = ("npc", eid, e.nome), d
        for r, p, nome in self.objeto_em(self.caso.sala):
            cx = min(max(px, r.left), r.right)
            cy = min(max(py, r.top), r.bottom)
            d = math.hypot(cx - px, cy - py)
            if d < dist:
                melhor, dist = ("ponto", p, nome), d
        return melhor

    def examinar(self, idx):
        c = self.caso
        sid = c.sala
        chave = (sid, idx)
        alvo = c.mapa.get(chave)
        reexame = self.pode_reexaminar(sid, idx)
        if chave in c.examinados and not reexame:
            self.cena(("fala", "helena", "Já examinei isso."))
            return
        if c.exame_gratis:
            c.exame_gratis = False
            c.acoes += 1
        else:
            c.gastar(CUSTO_MIN["examinar"])
        c.examinados.add(chave)
        self.som.sfx("busca")
        ev = c.sortear_evento()
        if alvo is None:
            self.cena(("espera", 0.5), ("som", "nada"), ("fala", "helena", c.rng.choice(VAZIOS)))
        elif alvo[0] == "falsa":
            c.pontos += PONTOS["falsa"]
            t, d = alvo[1]
            self.cena(("espera", 0.5), ("som", "nada"),
                      ("carta", {"titulo": t, "texto": d + "\n\n(Pista falsa.)", "img": None,
                                 "novas": [], "pts": PONTOS["falsa"]}))
        else:
            self.cena(("espera", 0.45))
            self.revelar(alvo[1])
        if ev:
            self.cena(("fn", lambda: self.mostrar_toast(ev)))
        self.verificar_horas()

    def pode_reexaminar(self, sid, idx):
        c = self.caso
        alvo = c.mapa.get((sid, idx))
        if alvo == ("pista", "computador"):
            return c.cap >= 6 and "comparacao" not in c.feitos
        if alvo in (("pista", "terra"), ("pista", "livro")):
            return "cam_univ" in c.pistas and alvo[1] not in c.pistas
        return False

    def _tr(self, cat):
        return f"{TRACOS[cat][0]}: {self.caso.helena[cat]}"

    def ficha_item(self, pid):
        if pid not in FICHAS_ITENS:
            return ""
        nome, quem, quando, paraque, _ = FICHAS_ITENS[pid]
        pq = paraque(self.caso) if callable(paraque) else paraque
        return f"\n\nQUEM USOU: {quem(self.caso)}\nQUANDO: {quando}\nPARA QUÊ: {pq}"

    def _carta_pista(self, pid, titulo, texto, img, novas):
        c = self.caso
        if pid in FICHAS_ITENS:
            texto += self.ficha_item(pid)
        pts = 0
        if pid not in c.pistas:
            c.pistas.add(pid)
            pts = PONTOS["pista"]
            c.pontos += pts
        self.cena(("som", "pista"), ("carta", {"titulo": titulo, "texto": texto, "img": img,
                                                "novas": novas, "pts": pts}))
        return pts

    FOTOS_PISTAS = {'faca': ('faca', 'Atrás das pias, jogada às pressas: a arma do crime.'), 'cam_baile': ('cam_baile', 'A câmera do corredor do baile. Ela gravou tudo entre 22:41 e 22:47.'), 'cam_univ': ('cam_univ', 'As câmeras do banheiro da Tulane guardam gravações de anos.'), 'livro': ('livro', 'O livro de registros dos alunos de Arquitetura de 2020.'), 'celular': ('celular', 'Numa gaveta trancada do professor: o celular de Beatriz, com a tela quebrada.'), 'computador': ('computador', 'O computador do caso. Rodrigo abre as gravações do baile.'), 'terra': ('banheiro_tulane', 'No campus, entre a vegetação, um trecho de terra revirada — diferente do resto.')}

    def revelar(self, pid):
        c = self.caso
        if pid in ("terra", "livro") and "cam_univ" not in c.pistas:
            if pid == "terra":
                t, d = ("Terra revirada", "Um trecho de terra mexido há muito tempo, diferente do resto do "
                        "jardim. Estranho… mas, por enquanto, não há motivo para cavar.")
            else:
                t, d = ("Arquivo de registros", "Milhares de fichas de alunos. Sem saber quem procurar, "
                        "seria impossível achar algo aqui.")
            self.cena(("carta", {"titulo": t, "texto": d + "\n\n(Talvez valha voltar aqui depois.)",
                                 "img": None, "novas": [], "pts": 0}))
            return
        if pid in self.FOTOS_PISTAS and pid not in c.pistas:
            chave, legenda = self.FOTOS_PISTAS[pid]
            if pid in ("cam_baile", "computador"):
                self.cena(("som", "estatica"))
            self.cena(("cena_img", chave, legenda))
        if pid == "corpo":
            novas = c.ganhar("A", "B", "M")
            self._carta_pista(pid, "O corpo do professor",
                              "Augusto Nakamura, coordenador de Arquitetura. Um único golpe de faca, no "
                              "coração. Sem sinais de briga: ele conhecia quem o atacou. Pelo sangue já seco e pela "
                              "temperatura do corpo, você calcula a hora da morte: 22:45. O corpo ficou "
                              "trancado aqui até o fim da festa.", "nakamura", novas)
            self.cena(("fn", lambda: self.marcar("corpo")))
        elif pid == "faca":
            c.tracos_conhecidos.add("mao")
            novas = c.ganhar("L")
            self._carta_pista(pid, "Faca do assassinato",
                              "Atrás das pias, jogada às pressas: a faca, ainda com sangue. Pelo ângulo do golpe "
                              f"no coração, quem atacou era {c.helena['mao'].upper()}.\n\n"
                              f"Traço da assassina → {self._tr('mao')}", "faca", novas)
            self.cena(("fn", lambda: self.marcar("faca")))
        elif pid == "cam_baile":
            for t in c.revela_cam_baile:
                c.tracos_conhecidos.add(t)
            self.cena(
                ("fala", "olivia", "A segurança do salão mandou as imagens do corredor. Vamos ver, minuto a minuto."),
                ("cena_img", "cam_baile", "O professor Nakamura sai do salão e caminha sozinho até o banheiro.",
                 "CÂMERA DO CORREDOR · TER 03/02/2026 · 22:40"),
                ("som", "coracao"),
                ("cena_img", "cam_baile", "Segundos depois, uma mulher entra atrás dele. De costas. O rosto "
                                          "nunca aparece.", "CÂMERA DO CORREDOR · TER 03/02/2026 · 22:41"),
                ("narra", "O corredor fica vazio. 22:42… 22:43… 22:44… Ninguém entra, ninguém sai."),
                ("som", "estatica"),
                ("cena_img", "cam_baile", "A porta se abre. A mulher sai sozinha, ajeitando o cabelo — ruivo. "
                                          "Tranca a porta e volta para a festa.", "CÂMERA DO CORREDOR · TER 03/02/2026 · 22:47"),
            )
            self._carta_pista(pid, "Câmera do corredor do baile",
                              "22:41 — uma mulher entra no banheiro logo depois do professor. 22:47 — "
                              "ela sai sozinha, ajeitando o cabelo RUIVO. O rosto não aparece.\n\n"
                              "Traços da assassina → " + " · ".join(self._tr(t) for t in c.revela_cam_baile),
                              "cam_baile", [])
            self.cena(("fala", "helena", "Ruiva… A Sofia tem cabelo escuro. Não foi ela."),
                      ("fn", lambda: self.marcar("cam_baile")))
        elif pid == "cam_univ":
            novas = c.ganhar("N", "O", "T", "X")
            self.cena(
                ("narra", "Rodrigo abre no notebook da polícia o arquivo das câmeras. Vocês avançam as gravações: 2018… 2019… "
                          "e o professor Nakamura aparece de novo e de novo, levando alunas para os fundos."),
                ("fala", "rodrigo", "Ele segura a aluna pelo braço… Olha a postura dela. Isso é ameaça. Chantagem."),
                ("fala", "helena", "E ninguém nunca viu isso? Durante anos?"),
                ("musica", "tensao"),
                ("som", "hm"),
                ("narra", "Uma data chama sua atenção: sexta-feira, 1º de maio de 2020 — a semana em que, "
                          "segundo Sofia, Bia teria viajado."),
                ("som", "estatica"),
                ("cena_img", "cam_univ", "21:38. O professor arrasta uma aluna de cabelo cacheado para os "
                                         "fundos do banheiro.", "GRAVAÇÃO · SEX 01/05/2020 · 21:38"),
                ("som", "coracao"), ("som", "susto"),
                ("cena_img", "beatriz", "Você congela a imagem e amplia o rosto. É a moça da foto de Sofia: "
                                        "Beatriz Valença.", "GRAVAÇÃO · SEX 01/05/2020 · 21:39"),
                ("narra", "Você avança a gravação minuto a minuto. O professor sai sozinho. Beatriz nunca "
                          "mais aparece."),
                ("tremor", 0.3), ("som", "susto"),
                ("narra", "E no canto da imagem, por um segundo, uma jovem RUIVA assiste a tudo… e foge."),
            )
            self._carta_pista(pid, "Gravações de 2020",
                              "Arquivos de seis anos atrás: o professor chantageando alunas e "
                              "arrastando-as para perto dos banheiros. Em 1º de maio de 2020 ele arrasta "
                              "Beatriz Valença — que nunca mais sai de lá. No canto da imagem, por um "
                              "segundo, uma jovem RUIVA vê tudo.", "cam_univ", novas)
            self.cena(("fala", "helena", "Beatriz nunca foi para a Itália. Se ela não saiu do campus… "
                                         "onde está? E quem era a testemunha ruiva?"),
                      ("musica", "investigacao"),
                      ("fn", lambda: self.marcar("cam_univ")))
        elif pid == "terra":
            novas = c.ganhar("U")
            self.cena(
                ("fala", "helena", "Este trecho de terra… é diferente do resto do jardim. Mexido há muito tempo."),
                ("fala", "olivia", "Beatriz entrou no banheiro e nunca mais saiu nas gravações. Vou pedir a escavação."),
                ("som", "trovao"),
                ("narra", "Na chuva, a perícia isola o jardim. Pás, lanternas, lona preta. Ninguém fala. "
                          "As horas passam devagar."),
                ("som", "coracao"),
            )
            self._carta_pista(pid, "Terra revirada",
                              "Com as gravações em mãos, a polícia autoriza a escavação daquele trecho de terra "
                              "diferente do resto. A confirmação vem horas depois: é o corpo de Beatriz "
                              "Valença, enterrado no campus em 2020.", "tulane", novas)
            self.cena(("fn", lambda: self.marcar("terra")))
        elif pid == "livro":
            novas = c.ganhar("Z", "AA", "H", "I", "J", "K", "AC")
            self.cena(
                ("fala", "olivia", "A testemunha de 2020 era ruiva — e ruivas não eram comuns no curso. Vamos "
                                   "filtrar os registros daquele ano."),
                ("narra", "Fichas amareladas, fotos 3×4, centenas de nomes. Olívia separa só as alunas ruivas "
                          "compatíveis com a imagem da câmera."),
                ("narra", "Sobram cinco. Ela lê os nomes em voz alta, um por um."),
            )
            for i, a in enumerate(c.alunas):
                self.cena(("som", "papel"), ("fala", "olivia", f"{i + 1}. {a['nome']}."))
            self.cena(("espera", 0.8), ("som", "coracao"), ("fala", "olivia", "E a quinta…"), ("espera", 1.0))
            nomes = "\n".join(f"{i+1}. {a['nome']}" for i, a in enumerate(c.alunas))
            self._carta_pista(pid, "Livro de registros de 2020",
                              "Alunas de 2020 compatíveis com a testemunha ruiva:\n" + nomes +
                              "\n5. Helena Cortez", "livro", novas)
            self.cena(("musica", "tensao"), ("som", "susto"), ("som", "coracao"), ("tremor", 0.3),
                      ("fala", "helena", "O quinto nome… é o meu. Eu estudei com ele em 2020. Mas eu "
                                         "não lembro de nada disso."),
                      ("musica", "investigacao"), ("fn", lambda: self.marcar("livro")))
        elif pid == "celular":
            novas = c.ganhar("V", "W")
            self.cena(
                ("fala", "rodrigo", "Essa gaveta estava trancada na primeira revista. Ninguém achou a chave."),
                ("som", "trinco"), ("espera", 0.5), ("som", "porta_arrombada"),
                ("narra", "Rodrigo força a gaveta. Lá dentro, embrulhado num pano, um celular antigo. "
                          "Não é do professor."),
                ("som", "coracao"),
            )
            self._carta_pista(pid, "Celular de Beatriz",
                              "Numa gaveta trancada, o celular de Beatriz. O professor ficou com ele e, depois de "
                              "1º de maio de 2020, mandou mensagens fingindo que ela estava viva: os amigos achavam "
                              "que ela estava na Itália, e a família, que já morava lá, achava que ela seguia "
                              "estudando. Só quando os pais marcaram um encontro com a filha descobriram que ela "
                              "tinha desaparecido.", "celular", novas)
            self.cena(("fn", lambda: self.marcar("celular")))
        elif pid == "max":
            novas = c.ganhar("AF", "AG", "AH")
            m = self.ents.get("max")
            if m:
                m.alvo = (self.player.x + 14, self.player.y)
            self.cena(("som", "rosnado"), ("espera", 0.5), ("som", "latido"), ("tremor", 0.25), ("som", "susto"),
                      ("espera", 0.6), ("som", "latido"),
                      ("fala", "max", "AU! AU! AU!"),
                      ("cena_img", "max", "Max não late para Rodrigo. Late para você — sem parar."),
                      ("som", "coracao"),
                      ("fala", "helena", "Ele late como se me conhecesse… como se eu já tivesse "
                                         "estado aqui muitas vezes."))
            self._carta_pista(pid, "Max reconhece você",
                              "O cachorro do professor fareja o ar, crava os olhos em você e late sem "
                              "parar. Não como late para estranhos.", "max", novas)
            self.cena(("fn", lambda: self.marcar("max")))
        elif pid == "computador":
            c.tracos_conhecidos.add(c.revela_computador)
            if c.cap >= 6:
                novas = c.ganhar("AI")
                if "computador" in c.pistas:
                    c.pontos += PONTOS["pista"]
                self.cena(
                    ("musica", "tensao"),
                    ("fala", "rodrigo", "De um lado, a assassina no corredor do baile. Do outro, as câmeras "
                                        "da entrada da festa. Vamos traço por traço."),
                    ("som", "estatica"),
                    ("cena_img", "cam_baile", "A mulher do corredor: cabelo ruivo, de costas.",
                     "CÂMERA DO CORREDOR · TER 03/02/2026 · 22:41"),
                    ("narra", "Na outra tela, Rodrigo abre as câmeras da entrada da festa e congela o quadro de uma "
                              "mulher ruiva chegando ao baile."),
                )
                for k in TRACOS:
                    self.cena(("som", "coracao"),
                              ("fala", "rodrigo", f"{TRACOS[k][0]}: {c.helena[k]}… confere."))
                self.cena(("espera", 0.8), ("fala", "rodrigo", "Helena… a mulher da entrada é você."),
                          ("som", "susto"), ("espera", 0.8))
                self._carta_pista(pid, "Comparação das gravações",
                                  "Rodrigo coloca lado a lado a assassina das câmeras do baile e as "
                                  "imagens de você chegando à festa. Mesmo cabelo, mesma altura, mesmos "
                                  "traços.\n\n" + " · ".join(self._tr(k) for k in TRACOS),
                                  "computador", novas)
                self.cena(("som", "coracao"), ("som", "hm_m"), ("fn", lambda: self.marcar("comparacao")),
                          ("objetivo", "Fale com a policial Olívia para fazer a acusação."))
            else:
                self._carta_pista(pid, "Computador do caso",
                                  "Rodrigo amplia um quadro da câmera do baile. Um detalhe aparece no "
                                  f"reflexo do espelho.\n\nTraço da assassina → {self._tr(c.revela_computador)}",
                                  "computador", [])

    def falar(self, eid):
        c = self.caso
        if eid in ("sofia", "olivia", "rodrigo"):
            c.gastar(CUSTO_MIN["conversar"])
        if eid == "sofia":
            primeira = "sofia" not in c.feitos
            novas = c.ganhar("E", "Q", "P", "R", "S")
            self.cena(
                ("fala", "sofia", "Ele era meu tio, mas tinha um lado que ninguém via. A Bia — Beatriz "
                                  "Valença — era minha melhor amiga na Arquitetura."),
                ("fala", "sofia", "Em 1º de maio de 2020 ela tinha passagem para um intercâmbio de alguns "
                                  "meses na Itália. Nunca mais me respondeu direito."),
                ("fala", "sofia", f"Eu? Várias pessoas viram: eu {c.sofia_alibi}."),
            )
            if primeira:
                c.pontos += PONTOS["conversa"]
                self.cena(("carta", {"titulo": "Depoimento de Sofia", "texto": "Sofia tem álibi "
                                     "confirmado e cabelo escuro. Beatriz, amiga dela, sumiu em 2020.",
                                     "img": "sofia", "novas": novas, "pts": PONTOS["conversa"]}),
                          ("fn", lambda: self.marcar("sofia")))
        elif eid == "olivia":
            if c.cap == 3:
                if "cam_univ" in c.pistas:
                    self.cena(("fala", "olivia", "Se houve uma testemunha ruiva em 2020, ela está nestes "
                                                 "registros. O arquivo é seu, Helena."))
                else:
                    self.cena(("fala", "olivia", "O Rodrigo está com a segurança, nas câmeras do banheiro do "
                                                 "campus. Eu fico com os registros, para quando soubermos "
                                                 "quem procurar."))
            elif c.cap <= 2:
                primeira = "olivia" not in c.feitos
                novas = c.ganhar("C", "D")
                self.cena(("fala", "olivia", "Policial Olívia. O professor foi visto vivo no salão, no "
                                             "baile de 3 de fevereiro, pouco antes das 22:40. Depois, ninguém mais o viu."),
                          ("fala", "olivia", "Quem fez isso trancou a porta e voltou para a festa como "
                                             "se nada tivesse acontecido. Examine tudo, detetive."))
                if primeira:
                    c.pontos += PONTOS["conversa"]
                    self.cena(("carta", {"titulo": "Depoimento de Olívia", "texto": "O crime aconteceu em "
                                         "3/02/2026, durante o baile de formatura.", "img": "olivia", "novas": novas,
                                         "pts": PONTOS["conversa"]}),
                              ("fn", lambda: self.marcar("olivia")))
            elif c.cap == 4:
                if c.todas_interrogadas() and "entrevista" not in c.feitos:
                    self.entrevista()
                else:
                    faltam = sum(1 for a in c.alunas if not a["interrogada"])
                    self.cena(("fala", "olivia", f"Ainda faltam {faltam} aluna(s) para interrogar."))
            elif c.cap >= 6:
                if "comparacao" in c.feitos:
                    self.cena(("fala", "olivia", "Você tem as provas, Helena. Quem matou o professor?"),
                              ("fn", lambda: self.abrir_acusacao(final=True)))
                else:
                    self.cena(("fala", "olivia", "Use o computador do caso antes. Precisamos das imagens."))
            else:
                self.cena(("fala", "olivia", "Vá com o Rodrigo. Eu cuido daqui."))
        elif eid == "rodrigo":
            if c.cap == 2:
                self.cena(("fala", "rodrigo", "Policial Rodrigo. Estou segurando os formandos aqui no salão. "
                                              "A cena do crime é com a Olívia, no banheiro."))
            elif c.cap == 3:
                self.cena(("fala", "rodrigo", "A segurança liberou as câmeras deste banheiro. Gravam há anos. "
                                              "Examine a câmera — eu abro o arquivo para você."))
            elif c.cap == 4:
                self.cena(("fala", "rodrigo", "Eu e a Olívia conduzimos os interrogatórios. Ouça cada uma "
                                              "delas, Helena."))
            elif c.cap == 5:
                self.cena(("fala", "rodrigo", "O escritório e o quarto ainda têm gavetas trancadas. E o "
                                              "Max está no quintal — passe pelo portão da cerca."))
            else:
                self.cena(("fala", "rodrigo", "Estou com você, Helena."))
        elif eid == "max":
            self.examinar(1) if c.sala == "casa" else None
        elif eid.startswith("aluna"):
            self.interrogar(eid)
        elif eid.startswith("al"):
            falas = {
                "al1": ["Fui eu que encontrei ele. A porta estava trancada… e ninguém tinha estranhado nada "
                        "a noite toda.", "Desculpa. Eu ainda não consigo parar de tremer."],
                "al2": ["Ele saiu do salão antes das onze. Era sempre assim: sumia e voltava. Desta vez não "
                        "voltou.", "A polícia não deixa ninguém ir embora."],
                "al3": ["O professor Nakamura era… difícil. Exigente. Ninguém aqui era próximo dele.",
                        "Tomara que vocês descubram logo quem fez isso."],
            }.get(eid, ["Que noite…"])
            self.cena(*[("fala", eid, f) for f in falas])

    def interrogar(self, aid):
        c = self.caso
        a = c.aluna(aid)
        if a["interrogada"]:
            self.cena(("fala", aid, "Eu já disse tudo o que sei."))
            return
        c.gastar(CUSTO_MIN["interrogar"])
        a["interrogada"] = True
        c.pontos += PONTOS["conversa"]
        tr = a["tracos"]
        self.som.sfx("gravador")
        self.cena(
            ("fala", "olivia", "Gravando. Diga seu nome e o que faz hoje, por favor."),
            ("fala", aid, f"Sou {a['nome']}, {a['idade']} anos. Estudei Arquitetura em 2020; hoje "
                          f"{a['ocupacao'].replace('hoje é', 'sou').replace('faz', 'faço').replace('trabalha', 'trabalho').replace('mudou', 'mudei').replace('é professora', 'sou professora')}."),
            ("fala", "rodrigo", "Onde você estava às 22:45 do dia 3, durante o baile?"),
            ("fala", aid, f"No baile? Eu {a['alibi']}."),
            ("fala", "olivia", "Você teve aulas com o professor Nakamura em 2020?"),
            ("fala", aid, "Algumas. Ele era o coordenador… mas eu nunca tive problema com ele."),
            ("fala", "olivia", "Lembra de alguma coisa no banheiro do campus em 1º de maio de 2020?"),
            ("fala", aid, "Primeiro de maio? Não… não lembro de nada desse dia. Por que essa data?"),
            ("carta", {"titulo": f"Ficha — {a['nome']}", "img": "ruivas", "pts": PONTOS["conversa"],
                       "novas": [], "texto": "\n".join(f"{TRACOS[k][0]}: {v}" for k, v in tr.items()) +
                       ("\n\nÁlibi CONFIRMADO por Olívia." if a["modo"] == "alibi" else
                        "\n\nÁlibi não confirmado. Compare os traços com os da assassina (tecla Q).")}),
            ("menu", Menu(f"O que fazer com {a['nome']}?",
                          [("Liberar — ela não é a assassina", "liberar", True),
                           (f"Acusar {a['nome'].split()[0]} do assassinato", "acusar", True),
                           ("Decidir depois", "depois", True)],
                          lambda v, aid=aid: self._decidir_aluna(aid, v), cancelavel=False,
                          subtitulo="Use o quadro de suspeitas (Q) para comparar com as câmeras.")),
        )
        self.verificar_horas()

    def _decidir_aluna(self, aid, v):
        c = self.caso
        a = c.aluna(aid)
        if v == "liberar":
            c.descartes.add(aid)
            c.pontos += PONTOS["liberar_certo"]
            self.cena(("fala", "olivia", f"{a['nome']} está liberada."), ("som", "certo"))
        elif v == "acusar":
            self.acusacao_errada(aid)
        if c.todas_interrogadas() and "interrogatorios" not in c.feitos:
            novas = c.ganhar("AB")
            self.cena(("fala", "olivia", "Nenhuma das quatro tem relação com o crime. Falta a QUINTA "
                                         "aluna dos registros. Fale comigo quando estiver pronta, Helena."),
                      ("carta", {"titulo": "Quatro alunas ouvidas", "texto": "As quatro primeiras alunas "
                                 "interrogadas não tinham relação com o crime.", "img": "ruivas",
                                 "novas": [("¬" + l) for l in novas], "pts": 0}),
                      ("fn", lambda: self.marcar("interrogatorios")))

    def entrevista(self):
        c = self.caso
        c.gastar(CUSTO_MIN["entrevista"])
        novas = c.ganhar("AD", "AE", "Y")
        c.pontos += PONTOS["pista"]
        self.cena(
            ("musica", "tensao"),
            ("fala", "olivia", "Helena Cortez. A quinta aluna dos registros. Sente-se, por favor."),
            ("anda", "helena", 14, 8), ("vira", "helena", "direita"),
            ("fn", lambda: [setattr(self.ents[x], "visivel", False) for x in list(self.ents) if x.startswith("aluna")]),
            ("fala", "olivia", "Você estudou Arquitetura em 2020. Teve aulas com o professor Nakamura. "
                               "Lembra de alguma coisa estranha daquele ano?"),
            ("fala", "helena", "Não… Só das aulas. Desse ano eu não lembro quase nada."),
            ("fala", "olivia", "Lembra de alguma coisa no banheiro do campus em 1º de maio de 2020?"),
            ("fala", "helena", "Não. Eu juro que não. Pode perguntar o que quiser."),
            ("narra", "Você responde tudo com sinceridade. Olívia anota, em silêncio. Depois fecha o caderno, "
                      "olha nos seus olhos… e faz uma última pergunta."),
            ("espera", 0.8),
            ("fala", "olivia", "Então só mais uma pergunta. Você lembra da Beatriz Valença, da sua turma?"),
            ("som", "susto"), ("som", "coracao"), ("espera", 0.9), ("som", "coracao"), ("som", "ofego"),
            ("tremor", 0.6), ("flash", (184, 90, 48), 1.0), ("som", "revelacao"),
            ("cena_img", "beatriz", "O corredor do banheiro da Tulane, 1º de maio de 2020. O professor "
                                    "arrastando Beatriz. Você atrás da porta, sem ar.", "LEMBRANÇA · SEX 01/05/2020 · 21:40"),
            ("cena_img", "nakamura", "Ele te viu. A voz dele, baixa: \"Se contar a alguém, você é a "
                                     "próxima.\"", "LEMBRANÇA · SEX 01/05/2020 · 21:43"),
            ("narra", "Você fica pálida. Falta o ar. Você abre a boca e não consegue dizer nada."),
            ("narra", "Sua mente apagou aquele 1º de maio de 2020 — amnésia dissociativa. Mas ele nunca "
                      "foi embora de verdade."),
            ("som", "ofego"),
            ("fala", "helena", "Eu… eu estava lá. Eu vi ele matar a Beatriz."),
            ("carta", {"titulo": "A pergunta decisiva", "img": "helena", "pts": PONTOS["pista"],
                       "novas": novas, "texto": "Helena era a testemunha ruiva de 2020. Ameaçada pelo "
                       "professor, desenvolveu amnésia dissociativa."}),
            ("anda", "rodrigo", 17, 10),
            ("fala", "rodrigo", "Helena, hoje à noite eu vou te levar à casa do professor. Talvez lá você lembre do "
                                "resto."),
            ("fn", lambda: self.marcar("entrevista")),
            ("fn", lambda: self._novo_cap(5, "Vá à casa de Augusto Nakamura")),
            ("musica", "investigacao"),
        )

    # ---------------- viagem
    def abrir_mapa(self):
        c = self.caso
        ops = []
        sug = self.destino_sugerido()
        for sid in SALAS_MAPA:
            ok = c.sala_liberada(sid)
            if not ok and sid not in getattr(c, "visitadas", set()):
                continue   # local ainda não faz parte da história: não aparece (sem spoiler)
            rot = NOMES_SALAS[sid]
            if sid == sug and sid != c.sala:
                rot += "   ★ OBJETIVO"
            if sid == c.sala:
                rot += "  — você está aqui"
            ops.append((rot, sid, ok))
        self.menu = Menu("Mapa de Nova Orleans", ops, self.viajar, img="mapa")
        vals = [o[1] for o in ops]
        if sug in vals and sug != c.sala and c.sala_liberada(sug):
            self.menu.sel = vals.index(sug)

    def viajar(self, sid):
        c = self.caso
        if sid is None or sid == c.sala:
            return
        custo = 0 if c.viagem_gratis else CUSTO_MIN["viajar"] + (CUSTO_MIN["chuva"] if c.chuva else 0)
        c.chuva = False
        c.viagem_gratis = False
        c.gastar(custo)
        ev = c.sortear_evento()
        self.som.sfx("passos")
        self.cena(("fade", "out"), ("espera", 0.6), ("fn", lambda: self.carregar_sala(sid)),
                  ("fade", "in"), ("fn", lambda: self.ao_chegar(sid)))
        if ev:
            self.cena(("fn", lambda: self.mostrar_toast(ev)))
        self.cena(("fn", self.verificar_horas))

    def mostrar_toast(self, txt):
        nome = self.caso.evento_som
        self.som.sfx({"imprensa": "flash", "cafe": "cafe", "chuva": "trovao", "acesso": "evento",
                      "anonimo": "telefone"}.get(nome, "evento"))
        self.toast = [txt, 4.5]

    def verificar_horas(self):
        c = self.caso
        if c.relogio >= PRAZO and not getattr(self, "_forcado", False):
            self._forcado = True
            self.cena(("musica", "tensao"), ("som", "coracao"),
                      ("narra", "O prazo de 48 horas acabou. A promotoria exige um nome AGORA."),
                      ("fn", lambda: self.abrir_acusacao(forcada=True)))

    # ---------------- acusação
    def abrir_acusacao(self, final=False, forcada=False):
        c = self.caso
        if c.cap < 2 and not forcada:
            self.cena(("fala", "helena", "Ainda não sei nada sobre o caso."))
            return
        ops = [("Sofia Mori Nakamura", "sofia", True)]
        if "livro" in c.pistas:
            ops += [(a["nome"], a["id"], True) for a in c.alunas] + [("Helena Cortez (você)", "helena", True)]
        else:
            ops += [("Uma aluna ruiva desconhecida", "ruiva", True)]
        sub = ("As horas acabaram — escolha agora." if forcada else
               f"Errar: {PONTOS['acusacao_errada']} pontos e −1 de credibilidade. "
               "Sem provas suficientes, a promotoria recusa.")
        self.som.musica("tensao")
        self.menu = Menu("Quem matou o professor?", ops, lambda v: self._escolher_motivo(v, forcada),
                         subtitulo=sub, cancelavel=not forcada, img="nakamura")
        self.menu.painel = self._painel_suspeita

    def _escolher_motivo(self, quem, forcada):
        ops = [(t, k, True) for k, t in MOTIVOS]
        random.shuffle(ops)
        self.menu = Menu("Qual foi o motivo?", ops, lambda m: self.julgar(quem, m, forcada),
                         cancelavel=not forcada)
        self.menu.painel = self._painel_motivo

    def acusacao_errada(self, quem, forcada=False):
        c = self.caso
        c.erros += 1
        c.credibilidade -= 1
        c.pontos += PONTOS["acusacao_errada"]
        if quem == "sofia":
            motivo = f"Sofia {c.sofia_alibi}. E as câmeras mostram uma assassina ruiva."
        elif quem == "ruiva":
            motivo = "Sem os registros de 2020 você nem sabe quem ela é."
        else:
            a = c.aluna(quem)
            if a["modo"] == "alibi":
                motivo = f"O álibi de {a['nome']} foi confirmado: ela {a['alibi']}."
            else:
                cat = a["traco_diferente"]
                motivo = (f"A assassina tem {TRACOS[cat][0].lower()} \"{c.helena[cat]}\", mas "
                          f"{a['nome']} tem \"{a['tracos'][cat]}\".")
            c.descartes.add(quem)
        self.cena(("som", "erro"), ("tremor", 0.3))
        if c.credibilidade <= 0 or forcada:
            self.cena(("narra", "Acusação errada. " + motivo),
                      ("fn", lambda: self.encerrar(False, "Acusação errada. " + motivo)))
        else:
            self.cena(("carta", {"titulo": "Acusação recusada", "texto": motivo +
                                 f"\n\n{PONTOS['acusacao_errada']} pontos e −1 de credibilidade.",
                                 "img": None, "novas": [], "pts": 0}),
                      ("musica", "investigacao"))

    def julgar(self, quem, mot, forcada=False):
        c = self.caso
        if quem != "helena":
            return self.acusacao_errada(quem, forcada)
        if not c.provas_suficientes():
            c.pontos += PONTOS["sem_provas"]
            texto = ("A promotoria rejeita: \"Sem premissas, não há conclusão.\" Ainda faltam elos entre "
                     "você e a cena do crime.")
            self.cena(("som", "erro"))
            if forcada:
                return self.cena(("fn", lambda: self.encerrar(False, texto)))
            return self.cena(("carta", {"titulo": "Faltam provas", "texto": texto +
                                        f"\n\n{PONTOS['sem_provas']} pontos.", "img": None, "novas": [],
                                        "pts": 0}), ("musica", "investigacao"))
        if mot != "vinganca":
            c.pontos += PONTOS["motivo_errado"]
            self.cena(("som", "errado"))
            if forcada:
                return self.cena(("fn", lambda: self.encerrar(False, "O motivo não se sustenta.")))
            return self.cena(("carta", {"titulo": "O motivo não fecha", "texto": "A pessoa está certa, mas "
                                        "as evidências apontam outro motivo. O que aconteceu em 1º de maio "
                                        f"de 2020?\n\n{PONTOS['motivo_errado']} pontos.", "img": None,
                                        "novas": [], "pts": 0}))
        bonus = PONTOS["acerto"] + c.horas * PONTOS["por_hora"]
        c.pontos += bonus
        c.feitos.add("acusacao")
        novas = c.ganhar("AJ", "AK", "AL", "AM")
        self.cena(
            ("som", "revelacao"), ("tremor", 0.6), ("flash", (184, 90, 48), 1.2),
            ("musica", "final"),
            ("cena_img", "helena", "Foi você. Seis anos depois, sem lembrar o porquê, sua mente só guardava "
                                   "que aquele homem tinha matado alguém da sua turma."),
            ("narra", "No baile em que Beatriz deveria ter se formado, às 22:45, você o seguiu até o "
                      "banheiro. E tudo voltou ao seu lugar."),
            ("carta", {"titulo": "Caso solucionado", "img": "helena", "novas": novas,
                       "pts": bonus, "texto": "Acerto + bônus pelas horas que sobraram até o prazo."}),
            ("narra", "Helena Cortez não foi condenada: ela tinha uma doença — a amnésia dissociativa — "
                      "que atingiu sua saúde mental."),
            ("cena_img", "tulane", "O caso foi solucionado. O corpo de Beatriz Valença foi entregue à família. "
                                   "Tudo em seu lugar.",
             "MESES DEPOIS · AGOSTO DE 2026"),
            ("fn", lambda: self.encerrar(True, "")),
        )

    # ---------------- dica
    # Dicas em dois níveis para cada tarefa pendente: 1º uma pista para PENSAR (barata);
    # se pedir de novo, 2º o caminho concreto. Nunca entrega quem é a assassina.
    DICAS = {
        "telefone": ("Alguém está tentando falar com você. O que toca num escritório à meia-noite?",
                     "O telefone está na mesa de trabalho. Chegue perto e aperte E."),
        "chegar": ("Sofia está esperando por você no lugar do crime.",
                   "Saia pela porta (siga a seta) e escolha o Salão do Baile no mapa (TAB)."),
        "sofia": ("Quem chamou você conhece a vítima melhor que ninguém. O que ela sabe do passado dele?",
                  "Sofia está no Salão do Baile. Chegue perto e aperte E."),
        "olivia2": ("A polícia chegou primeiro à cena. O que ela já sabe sobre a hora em que ele foi visto vivo?",
                    "A policial Olívia está no Banheiro do Baile. Fale com ela."),
        "corpo": ("Comece pelo que a vítima pode contar: como ele morreu, e quando?",
                  None),
        "cam_baile": ("Ninguém chega a um banheiro de festa sem passar pelo corredor. Quem estaria olhando?",
                      None),
        "faca": ("Quem golpeia precisa se livrar da arma às pressas. Onde algo some rápido num banheiro?",
                 None),
        "cam_univ": ("Ódio assim tem passado. Que lugar da Tulane guardaria anos de imagens do professor?",
                     None),
        "terra": ("Se Beatriz nunca saiu do campus nas gravações… onde ela poderia estar até hoje?",
                  None),
        "livro": ("A testemunha era uma aluna ruiva de 2020. Onde ficam os nomes dos alunos daquele ano?",
                  None),
        "aluna": ("Compare cada aluna com o perfil da assassina (tecla Q). Basta UM traço diferente — ou um "
                  "álibi confirmado — para descartar.", None),
        "olivia4": ("Quatro alunas ouvidas. Mas quantos nomes havia no livro de registros?",
                    "Fale com a policial Olívia: falta a entrevista da quinta aluna."),
        "celular": ("Beatriz sumiu e ninguém desconfiou por meses. Como alguém fingiria que ela estava bem?",
                    None),
        "max": ("Animais não esquecem quem já esteve por perto.", None),
        "comparacao": ("As câmeras do baile mostraram a assassina. Compare com quem estava na festa.",
                       "Use o computador do caso, na Sala de Interrogatório."),
        "olivia6": ("Você já tem as provas. Quem estava no banheiro às 22:45 — e por quê?",
                    "Fale com a policial Olívia. Na tela de acusação, o perfil da assassina aparece ao lado."),
    }

    def _alvo_dica(self):
        c = self.caso
        p = self.pendencias()
        if not p:
            return None, None
        sala, tipo, alvo = p[0]
        if tipo == "chegar":
            return "chegar", None
        if tipo == "ponto" and alvo == "telefone":
            return "telefone", None
        if tipo == "ponto":
            return "comparacao", None
        if tipo == "pista":
            pid = c.mapa.get((sala, alvo), (None, None))[1]
            onde = f"Examine \"{PONTOS_SALA[sala][alvo]}\" em {NOMES_SALAS[sala]}."
            return pid, onde
        if alvo.startswith("aluna"):
            a = c.aluna(alvo)
            return "aluna", f"Ainda falta interrogar {a['nome']}, no banco da Sala de Interrogatório."
        if alvo == "olivia":
            return {2: "olivia2", 4: "olivia4"}.get(c.cap, "olivia6"), None
        return alvo, None

    def pedir_dica(self):
        chave, _ = self._alvo_dica()
        if not chave:
            self.cena(("fala", "helena", "Agora não preciso de dica."))
            return
        nivel = getattr(self.caso, "dica_nivel", {}).get(chave, 0)
        custo = PONTOS["dica"] // 2 if nivel == 0 else PONTOS["dica"]
        rot = "Uma pista para pensar" if nivel == 0 else "O caminho exato"
        self.menu = Menu("Pedir uma dica?", [(f"Sim — {rot} ({custo} pontos)", True, True),
                                             ("Não, vou investigar sozinha", False, True)], self._dar_dica,
                         subtitulo="Peça de novo para receber uma dica mais direta.")

    def _dar_dica(self, sim):
        if not sim:
            return
        c = self.caso
        chave, onde = self._alvo_dica()
        if not chave:
            return
        if not hasattr(c, "dica_nivel"):
            c.dica_nivel = {}
        nivel = c.dica_nivel.get(chave, 0)
        c.dica_nivel[chave] = nivel + 1
        c.dicas += 1
        c.pontos += PONTOS["dica"] // 2 if nivel == 0 else PONTOS["dica"]
        self.som.sfx("dica")
        pensar, caminho = self.DICAS.get(chave, ("Siga a seta âmbar: ela aponta o próximo passo.", None))
        if nivel == 0:
            d = pensar
        else:
            d = caminho or onde or pensar
        self.cena(("narra", f"Dica {'1' if nivel == 0 else '2'}: {d}"))

    # ---------------- final
    def encerrar(self, venceu, motivo):
        c = self.caso
        self.final_info = {"venceu": venceu, "motivo": motivo, "dur": int(time.time() - c.inicio)}
        self.final_titulo = titulo_rank(c.pontos, venceu)
        salvar_recorde({"pontos": c.pontos, "titulo": self.final_titulo, "codigo": c.codigo,
                        "resultado": "Vitória" if venceu else "Derrota", "data": time.strftime("%d/%m/%Y")})
        self.som.musica("final" if venceu else "derrota")
        self.modo = "final"
        self.fila = []
        self.menu = Menu("", [("Novo caso (novo sorteio)", "novo", True),
                              ("Repetir este mesmo caso", "repetir", True), ("Menu principal", "menu", True)],
                         self._escolha_final, cancelavel=False)

    def _escolha_final(self, v):
        cod = self.caso.codigo
        if v == "novo":
            self.novo_jogo()
        elif v == "repetir":
            self.novo_jogo(cod)
        else:
            self.titulo_menu()

    def desenhar_final(self):
        c = self.caso
        W, H = self.tela.get_size()
        self.tela.fill(C["bg"])
        v = self.final_info["venceu"]
        r = self.retrato("helena" if v else "helena", 90 * self.s)
        if r:
            self.tela.blit(r, self.P(24, 24))
            pygame.draw.rect(self.tela, C["ambar"], (*self.P(24, 24), r.get_width(), r.get_height()), 2)
        x = self.P(128, 0)[0]
        self.texto("CASO SOLUCIONADO" if v else "CASO ARQUIVADO", "titulo",
                   C["texto"] if v else C["cobre2"], x, self.P(0, 20)[1])
        self.texto(self.final_titulo, "h1", C["ambar"], x, self.P(0, 50)[1])
        if v:
            self.texto(CONCLUSAO_SIMBOLICA, "h2", C["texto"], x, self.P(0, 70)[1])
            self.bloco(CONCLUSAO_TEXTO, "corpo", C["fraco"], x, self.P(0, 84)[1], int(330 * self.s))
        else:
            self.bloco(self.final_info["motivo"] or "Você ficou sem credibilidade.", "corpo", C["cobre2"],
                       x, self.P(0, 72)[1], int(330 * self.s))
        dur = self.final_info["dur"]
        stats = [("Pontuação final", c.pontos), ("Pistas principais", f"{len(c.pistas)} de {len(PISTAS_PRINCIPAIS)}"),
                 ("Proposições", f"{len(c.props)} de {len(PROPOSICOES)}"), ("Capítulo alcançado", c.cap),
                 ("Horas até o prazo", c.horas), ("Dicas usadas", c.dicas), ("Acusações erradas", c.erros),

                 ("Tempo de jogo", f"{dur // 60} min {dur % 60:02d} s"), ("Código do caso", c.codigo)]
        y = self.P(0, 124)[1]
        for i, (k, val) in enumerate(stats):
            col = i % 2
            yy = y + (i // 2) * int(12 * self.s)
            bx = self.P(24 + col * 220, 0)[0]
            self.tela.blit(self.f["corpo"].render(k, True, C["fraco"]), (bx, yy))
            vv = self.f["corpo_b"].render(str(val), True, C["texto"])
            self.tela.blit(vv, (bx + int(200 * self.s) - vv.get_width(), yy))
        self.bloco("Sorteado nesta partida: nomes e álibis das 4 ruivas, traços da assassina, lugar das pistas "
                   "e eventos. Jogue de novo para ver outra versão do caso.", "peq", C["fraco"],
                   self.P(20, 0)[0], self.P(0, 181)[1], int(440 * self.s), 1.0, centro=True)
        self.desenhar_opcoes(self.menu, 140, 204, 200, 16)

    # ============================================================ LAÇO
    def executar(self):
        while self.rodando:
            dt = min(0.05, self.relogio.tick(60) / 1000)
            self.t += dt
            for ev in pygame.event.get():
                self.evento(ev)
            self.atualizar(dt)
            self.desenhar()
            pygame.display.flip()
        self.som.parar()
        pygame.quit()

    # ---------------- eventos
    def evento(self, ev):
        if ev.type == pygame.QUIT:
            self.rodando = False
            return
        if ev.type == pygame.VIDEORESIZE and not self.android and not self.tela_cheia:
            self.tela = pygame.display.set_mode((max(640, ev.w), max(360, ev.h)), pygame.RESIZABLE)
            self._recalcular()
            return
        if ev.type == pygame.FINGERDOWN:
            self.toque = True
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
            self.alternar_tela_cheia()
            return
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_m and self.modo != "codigo":
            self.som.alternar()
            return
        # cliques e toques
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.modo == "jogo" and getattr(self, "briefing", None):
            self.fechar_briefing()
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.menu and self._clique_menu(ev.pos):
                return
            if self.painel_aberto == "caderno":
                for i, rr in enumerate(getattr(self, "rects_abas", [])):
                    if rr.collidepoint(ev.pos):
                        self.aba_caderno, self.scroll = i, 0
                        self.som.sfx("papel")
                        return
            if self.modo == "jogo" and self._clique_ui(ev.pos):
                return
            if self.modo == "jogo" and (self.balao or self.carta or self.capitulo_titulo):
                self._avancar()
                return
            if self.modo in ("como", "recordes"):
                self.titulo_menu()
                return
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.dpad = {}
        if ev.type == pygame.MOUSEMOTION and self.menu:
            for i, r in enumerate(self.menu.rects):
                if r.collidepoint(ev.pos) and self.menu.opcoes[i][2] and i != self.menu.sel:
                    self.menu.sel = i
                    self.som.sfx("hover")
        if ev.type == pygame.MOUSEWHEEL and self.painel_aberto:
            self.scroll = max(0, self.scroll - ev.y * 3)
        if self.modo == "jogo" and getattr(self, "briefing", None):
            if (ev.type == pygame.KEYDOWN and (ev.key in TECLAS_OK or ev.key == pygame.K_ESCAPE)) or \
                    (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1):
                self.fechar_briefing()
            return
        if ev.type != pygame.KEYDOWN:
            return
        k = ev.key
        if k == getattr(pygame, "K_AC_BACK", -1):
            k = pygame.K_ESCAPE
        if self.menu:
            return self._tecla_menu(k)
        if self.modo == "codigo":
            if k == pygame.K_ESCAPE:
                self.titulo_menu()
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.texto_codigo:
                self.novo_jogo(int(self.texto_codigo))
            elif k == pygame.K_BACKSPACE:
                self.texto_codigo = self.texto_codigo[:-1]
            elif ev.unicode.isdigit() and len(self.texto_codigo) < 6:
                self.texto_codigo += ev.unicode
            return
        if self.modo in ("como", "recordes"):
            if k in TECLAS_OK or k == pygame.K_ESCAPE:
                self.titulo_menu()
            return
        if self.modo != "jogo":
            return
        if self.painel_aberto == "caderno" and (k in TECLAS_ESQ or k in TECLAS_DIR):
            d = 1 if k in TECLAS_DIR else -1
            self.aba_caderno = (getattr(self, "aba_caderno", 0) + d) % len(self.ABAS_CADERNO)
            self.scroll = 0
            self.som.sfx("papel")
            return
        if self.painel_aberto:
            if k in TECLAS_CIMA:
                self.scroll = max(0, self.scroll - 2)
                if self.painel_aberto == "suspeitas":
                    self.sel_susp = max(0, self.sel_susp - 1)
            elif k in TECLAS_BAIXO:
                self.scroll += 2
                if self.painel_aberto == "suspeitas":
                    self.sel_susp += 1
            elif self.painel_aberto == "suspeitas" and k in (pygame.K_RETURN, pygame.K_SPACE):
                self._alternar_descarte()
            elif k in (pygame.K_ESCAPE, pygame.K_c, pygame.K_q, pygame.K_e):
                self.painel_aberto = None
            return
        if self.balao or self.carta or self.capitulo_titulo:
            if k in TECLAS_OK or k == pygame.K_ESCAPE:
                self._avancar()
            return
        if self.ocupado():
            return
        if k in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
            self.interagir()
        elif k == pygame.K_c:
            self.painel_aberto, self.scroll = "caderno", 0
            self.som.sfx("busca")
        elif k == pygame.K_q:
            self.painel_aberto, self.scroll, self.sel_susp = "suspeitas", 0, 0
            self.som.sfx("busca")
        elif k == pygame.K_h:
            self.pedir_dica()
        elif k == pygame.K_x:
            self.abrir_acusacao()
        elif k == pygame.K_TAB:
            self.abrir_mapa()
        elif k == pygame.K_ESCAPE:
            self.abrir_pausa()

    def abrir_pausa(self):
        if True:
            dur = int(time.time() - self.caso.inicio)
            self.menu = Menu("Pausa", [("Continuar jogando", "cont", True), ("Salvar jogo", "salvar", True),
                                       ("Salvar e sair", "salvar_sair", True),
                                       ("Sair sem salvar", "sair", True),
                                       ("Como jogar", "como", True)], self._pausa,
                             subtitulo=f"Tempo real de partida: {dur // 60} min {dur % 60:02d} s "
                                       "(a partida completa foi pensada para ~15–17 min).")

    def _pausa(self, v):
        if v == "como":
            self.briefing = "pausa"
        elif v == "salvar":
            ok = self.salvar_jogo()
            self.mostrar_toast("Jogo salvo. Para retomar: menu principal → Continuar caso salvo."
                               if ok else "Não foi possível salvar o jogo nesta pasta.")
            self.musica_ambiente()
        elif v == "salvar_sair":
            ok = self.salvar_jogo()
            self.titulo_menu()
            if not ok:
                self.mostrar_toast("Não foi possível salvar o jogo nesta pasta.")
        elif v == "sair":
            self.menu = Menu("Sair sem salvar?",
                             [("Sim, sair (o progresso desde o último salvamento será perdido)", "sim", True),
                              ("Não, voltar à pausa", "nao", True)],
                             lambda r: self.titulo_menu() if r == "sim" else self.musica_ambiente(),
                             cancelavel=True)
        else:
            self.musica_ambiente()

    def _tecla_menu(self, k):
        m = self.menu
        if k in TECLAS_CIMA or k in TECLAS_ESQ:
            self._mover_sel(-1)
        elif k in TECLAS_BAIXO or k in TECLAS_DIR:
            self._mover_sel(1)
        elif k in TECLAS_OK:
            self._confirmar_menu()
        elif k == pygame.K_ESCAPE and m.cancelavel:
            self.menu = None
            if self.modo == "jogo":
                self.musica_ambiente()

    def _mover_sel(self, d):
        m = self.menu
        n = len(m.opcoes)
        for _ in range(n):
            m.sel = (m.sel + d) % n
            if m.opcoes[m.sel][2]:
                break
        self.som.sfx("hover")

    def _confirmar_menu(self):
        m = self.menu
        rot, val, ok = m.opcoes[m.sel]
        if not ok:
            self.som.sfx("errado")
            return
        self.som.sfx("clique")
        self.menu = None
        m.cb(val)

    def _clique_menu(self, pos):
        for i, r in enumerate(self.menu.rects):
            if r.collidepoint(pos):
                self.menu.sel = i
                self._confirmar_menu()
                return True
        return False

    def _clique_ui(self, pos):
        for nome, r in getattr(self, "botoes_ui", {}).items():
            if r.collidepoint(pos):
                if nome in ("cima", "baixo", "esquerda", "direita"):
                    self.dpad = {nome: True}
                    return True
                if self.painel_aberto:
                    self.painel_aberto = None
                    return True
                if self.balao or self.carta or self.capitulo_titulo:
                    self._avancar()
                    return True
                if self.ocupado():
                    return True
                acao = {"E": self.interagir, "Caderno": lambda: setattr(self, "painel_aberto", "caderno"),
                        "Suspeitas": self._abrir_susp, "Dica": self.pedir_dica, "Acusar": self.abrir_acusacao,
                        "Mapa": self.abrir_mapa, "Som": self.som.alternar,
                        "Pausa": self.abrir_pausa}.get(nome)
                if acao:
                    self.som.sfx("clique")
                    acao()
                return True
        return False

    def _abrir_susp(self):
        self.painel_aberto, self.scroll, self.sel_susp = "suspeitas", 0, 0

    def _avancar(self):
        if self.capitulo_titulo:
            if self.capitulo_titulo[2] < len(self.capitulo_titulo[0]):
                self.capitulo_titulo[2] = len(self.capitulo_titulo[0])
            else:
                self.capitulo_titulo = None
            return
        if self.carta:
            if self.carta["n"] < len(self.carta["texto"]):
                self.carta["n"] = len(self.carta["texto"])
                return
            self.carta = None
            self.som.sfx("clique")
            return
        b = self.balao
        if not b:
            return
        texto = b["pags"][b["i"]]
        if b["n"] < len(texto):
            b["n"] = len(texto)
        elif b["i"] + 1 < len(b["pags"]):
            b["i"] += 1
            b["n"] = 0
            self.som.sfx("clique")
        else:
            self.balao = None
            self.som.sfx("clique")

    def _alternar_descarte(self):
        lista = self._lista_suspeitas()
        if not lista:
            return
        self.sel_susp = min(self.sel_susp, len(lista) - 1)
        chave = lista[self.sel_susp][0]
        self.caso.descartes.symmetric_difference_update({chave})
        self.som.sfx("clique")

    def musica_ambiente(self):
        c = self.caso
        if c and (c.horas <= 5 or c.cap >= 6):
            self.som.musica("tensao")
        else:
            self.som.musica("investigacao")

    # ---------------- atualização
    def _sob_chuva(self):
        c = self.caso
        if not c.chovendo():
            return None
        zonas = SALAS[c.sala].get("ceu_aberto", [])
        if not zonas:
            return None
        tx, ty = self.player.x / T, (self.player.y - 2) / T
        dentro = any(zx <= tx < zx + zw and zy <= ty < zy + zh for zx, zy, zw, zh in zonas)
        return "fora" if dentro else "perto"

    def _som_ambiente(self):
        if self.modo != "jogo" or not self.caso or getattr(self, "briefing", None) == "inicio":
            self.som.ambiente(None)
            self.som.molhado = False
            return
        onde = self._sob_chuva()
        self.som.molhado = onde == "fora"
        if onde is None:
            self.som.ambiente(None)
        else:   # a céu aberto: chuva alta; sob o telhado: abafada
            self.som.ambiente("chuva_loop", 0.8 if onde == "fora" else 0.25)

    def atualizar(self, dt):
        self.som.atualizar()
        self._som_ambiente()
        if self.modo != "jogo" or getattr(self, "briefing", None):
            return
        c = self.caso
        if (c.cap >= 1 and c.cap != getattr(self, "_cap_salvo", None) and not self.ocupado()
                and self.fade_alvo == 0 and self.modo == "jogo"):
            if self.salvar_jogo():
                self.mostrar_toast(f"Progresso salvo automaticamente — início do capítulo {c.cap}.")
            else:
                self._cap_salvo = c.cap
        if self.toast and not (self.carta or self.menu or self.painel_aberto or self.balao):
            self.toast[1] -= dt
            if self.toast[1] <= 0:
                self.toast = None
        if self.espera > 0:
            self.espera -= dt
        if self.capitulo_titulo and self.capitulo_titulo[2] >= len(self.capitulo_titulo[0]):
            self.capitulo_titulo[1] -= dt
            if self.capitulo_titulo[1] <= 0:
                self.capitulo_titulo = None
        if self.flash:
            self.flash[1] -= dt
            if self.flash[1] <= 0:
                self.flash = None
        self.tremor = max(0, self.tremor - dt)
        if self.fade != self.fade_alvo:
            passo = dt * 2.5
            self.fade = min(self.fade_alvo, self.fade + passo) if self.fade < self.fade_alvo else max(self.fade_alvo, self.fade - passo)
        if self.balao:
            b = self.balao
            antes = int(b["n"])
            b["n"] += dt * VELOCIDADE_TEXTO.get(b["tipo"], 55)
            self._som_digitacao(b["pags"][b["i"]], antes, int(b["n"]), b.get("voz"), 2)
        if self.carta and self.carta["n"] < len(self.carta["texto"]):
            antes = int(self.carta["n"])
            self.carta["n"] += dt * VELOCIDADE_TEXTO["carta"]
            self._som_digitacao(self.carta["texto"], antes, int(self.carta["n"]), "voz_narra", 3)
        if self.capitulo_titulo and self.capitulo_titulo[2] < len(self.capitulo_titulo[0]):
            antes = int(self.capitulo_titulo[2])
            self.capitulo_titulo[2] += dt * VELOCIDADE_TEXTO["capitulo"]
            self._som_digitacao(self.capitulo_titulo[0], antes, int(self.capitulo_titulo[2]), "voz_narra", 1)
        # telefone tocando no capítulo 1
        if c.cap == 1 and "telefone" not in c.feitos and self.t - self.ultimo_toque > 3.0 and not self.balao:
            self.ultimo_toque = self.t
            self.som.sfx("telefone")
        # personagens andando por cena
        for e in self.ents.values():
            if e.alvo:
                ax, ay = e.alvo
                dx, dy = ax - e.x, ay - e.y
                d = math.hypot(dx, dy)
                vel = 75 * dt
                if d <= vel:
                    e.x, e.y = ax, ay
                    e.alvo = None
                    e.andando = False
                else:
                    if abs(dx) > abs(dy):
                        e.dir = "direita" if dx > 0 else "esquerda"
                    else:
                        e.dir = "baixo" if dy > 0 else "cima"
                    e.x += dx / d * vel
                    e.y += dy / d * vel
                    e.andando = True
                    e.t_anim += dt
            elif e.id == "max" and not self.ocupado() and random.random() < 0.01:
                e.alvo = (random.randint(21, 28) * T, random.randint(9, 13) * T + 8)
        self._processar_fila()
        if not self.ocupado():
            self._mover_jogador(dt)

    def _som_digitacao(self, texto, antes, depois, voz, cada):
        """Toca a 'voz' do personagem a cada N letras novas (estilo jogos de história)."""
        if not voz or depois <= antes:
            return
        for i in range(antes, min(depois, len(texto))):
            ch = texto[i]
            if ch.strip() and ch not in ".,!?…—-\"'" and i % cada == 0:
                self.som.sfx(f"{voz}_{random.randint(0, 2)}")
                return

    def _teclas_dir(self):
        k = pygame.key.get_pressed()
        dx = (1 if any(k[t] for t in TECLAS_DIR) else 0) - (1 if any(k[t] for t in TECLAS_ESQ) else 0)
        dy = (1 if any(k[t] for t in TECLAS_BAIXO) else 0) - (1 if any(k[t] for t in TECLAS_CIMA) else 0)
        if self.dpad and pygame.mouse.get_pressed()[0]:
            dx += (1 if "direita" in self.dpad else 0) - (1 if "esquerda" in self.dpad else 0)
            dy += (1 if "baixo" in self.dpad else 0) - (1 if "cima" in self.dpad else 0)
        return dx, dy

    def _livre(self, x, y):
        for px, py in ((x - 5, y - 3), (x + 5, y - 3), (x - 5, y), (x + 5, y)):
            tx, ty = int(px // T), int(py // T)
            if tx < 0 or ty < 0 or tx >= COLS or ty >= LINHAS or self.solido[ty][tx]:
                return False
        return True

    def _mover_jogador(self, dt):
        p = self.player
        dx, dy = self._teclas_dir()
        if dx or dy:
            n = math.hypot(dx, dy)
            vel = VELOCIDADE_ANDAR * dt
            nx, ny = p.x + dx / n * vel, p.y + dy / n * vel
            if self._livre(nx, p.y):
                p.x = nx
            if self._livre(p.x, ny):
                p.y = ny
            if abs(dx) >= abs(dy) and dx:
                p.dir = "direita" if dx > 0 else "esquerda"
            elif dy:
                p.dir = "baixo" if dy > 0 else "cima"
            p.andando = True
            p.t_anim += dt
            self.t_passo -= dt
            if self.t_passo <= 0:
                self.t_passo = 0.32
                self.som.sfx("passo")
        else:
            p.andando = False
        # portas e saídas
        S = SALAS[self.caso.sala]
        tx, ty = int(p.x // T), int((p.y - 2) // T)
        na_saida = False
        if "saida" in S:
            sx, sy = S["saida"]
            if ty >= sy - 0 and sx - 1 <= tx <= sx + 2 and p.y > (LINHAS - 1) * T - 4:
                na_saida = True
        if na_saida and not self.na_saida:
            p.y -= 6
            self.abrir_mapa()
        self.na_saida = na_saida
        if "porta_lado" in S:
            (ptx, pty), destino, (dtx, dty) = S["porta_lado"]
            if abs(tx - ptx) <= 0 and abs(ty - pty) <= 1:
                self.som.sfx("passos")
                self.cena(("fade", "out"), ("fn", lambda: self.carregar_sala(destino, dtx, dty)),
                          ("fade", "in"), ("fn", lambda: self.ao_chegar(destino)))

    # ============================================================ DESENHO
    def desenhar(self):
        if self.modo == "titulo":
            self.desenhar_titulo()
        elif self.modo == "como":
            self.desenhar_como()
        elif self.modo == "codigo":
            self.desenhar_codigo()
        elif self.modo == "recordes":
            self.desenhar_recordes()
        elif self.modo == "final":
            self.desenhar_final()
        elif self.modo == "jogo" and getattr(self, "briefing", None):
            self.desenhar_briefing()
        elif self.modo == "jogo":
            self.desenhar_jogo()
            if self.menu:
                self.desenhar_menu(self.menu)
        if self.menu and self.modo in ("titulo",):
            pass

    def _luzes(self):
        sid = self.caso.sala
        S = SALAS[sid]
        escuro = pygame.Surface((LW, LH), pygame.SRCALPHA)
        escuro.fill((6, 12, 18, S["escuro"]))
        lista = [(lx * T + T / 2, ly * T + T / 2 + OY, r) for lx, ly, r in S["luzes"]]
        lista.append((self.player.x, self.player.y - 8 + OY, 62))
        for x, y, r in lista:
            m = self.luz_cache.setdefault(("m", r), mascara_luz(int(r)))
            escuro.blit(m, (int(x - r), int(y - r)), special_flags=pygame.BLEND_RGBA_SUB)
        self.mundo.blit(escuro, (0, 0))
        for x, y, r in lista[:-1]:
            g = self.luz_cache.setdefault(("g", r), brilho_luz(int(r), C["ambar"]))
            self.mundo.blit(g, (int(x - r), int(y - r)), special_flags=pygame.BLEND_RGB_ADD)

    def desenhar_jogo(self):
        c = self.caso
        self.botoes_ui = {}
        m = self.mundo
        m.fill(C["barra"])
        m.blit(self.fundo, (0, OY))
        # personagens (ordenados pela profundidade)
        for e in sorted(self.ents.values(), key=lambda e: e.y):
            if not e.visivel:
                continue
            spr = e.sprite()
            spr2 = pygame.transform.scale(spr, (spr.get_width() * 2, spr.get_height() * 2))
            pygame.draw.ellipse(m, (0, 0, 0), (e.x - 8, e.y + OY - 3, 16, 5))
            m.blit(spr2, (int(e.x - spr2.get_width() / 2), int(e.y + OY - spr2.get_height())))
        # chuva: só a céu aberto e só quando a história diz que chove
        for zx, zy, zw, zh in (SALAS[c.sala].get("ceu_aberto", []) if c.chovendo() else []):
            area = pygame.Rect(zx * T, zy * T + OY, zw * T, zh * T).clip(pygame.Rect(0, OY, LW, LH - OY))
            if area.w <= 0 or area.h <= 0:
                continue
            m.set_clip(area)
            rnd = random.Random(int(self.t * 30))
            gotas = max(8, area.w * area.h // 900)
            for _ in range(gotas):
                x = area.x + rnd.randrange(area.w + 6)
                y = area.y + rnd.randrange(area.h)
                pygame.draw.line(m, (120, 150, 180), (x, y), (x - 2, y + 6))
            for _ in range(gotas // 4):   # respingos no chão
                x, y = area.x + rnd.randrange(area.w), area.y + rnd.randrange(area.h)
                pygame.draw.circle(m, (95, 120, 145), (x, y), 1)
            m.set_clip(None)
        self._luzes()
        # tremor de tela
        W, H = self.tela.get_size()
        self.tela.fill((0, 0, 0))
        dx = dy = 0
        if self.tremor > 0:
            dx, dy = random.randint(-3, 3), random.randint(-3, 3)
        esc = pygame.transform.scale(m, (int(LW * self.s), int(LH * self.s)))
        self.tela.blit(esc, (self.ox + dx, self.oy + dy))
        if self.flash:
            cor, rest, tot = self.flash
            f = pygame.Surface((W, H), pygame.SRCALPHA)
            f.fill(cor + (int(170 * rest / tot),))
            self.tela.blit(f, (0, 0))
        self.desenhar_marcadores()
        self.desenhar_hud()
        self.desenhar_guia()
        self.desenhar_prompt()
        self.desenhar_balao()
        if self.carta:
            self.desenhar_carta(self.carta)
        if self.painel_aberto == "caderno":
            self.desenhar_caderno()
        elif self.painel_aberto == "suspeitas":
            self.desenhar_suspeitas()
        if self.capitulo_titulo:
            self.desenhar_capitulo()
        if self.toast and not (self.carta or self.menu or self.painel_aberto or self.balao):
            lin = quebrar("! " + self.toast[0], self.f["peq"], int(250 * self.s))
            r = self.RR(110, OY + 4, 260, 0)
            r.h = len(lin) * self.f["peq"].get_linesize() + int(8 * self.s)
            self.painel(r, C["azulfundo"], C["azul"])
            yy = r.y + int(4 * self.s)
            for l in lin:
                self.tela.blit(self.f["peq"].render(l, True, C["azul2"]), (r.x + int(5 * self.s), yy))
                yy += self.f["peq"].get_linesize()
        if self.toque:
            self.desenhar_toque()
        if self.fade > 0:
            f = pygame.Surface((W, H))
            f.set_alpha(int(255 * self.fade))
            self.tela.blit(f, (0, 0))

    # ---------------- HUD
    def _chip(self, x_dir, y, conteudo, borda=None):
        """Desenha um 'chip' do HUD alinhado pela direita; conteudo = lista de (surface, gap)."""
        s = self.s
        larg = sum(sup.get_width() + int(g * s) for sup, g in conteudo) + int(10 * s)
        alt = int(15 * s)
        r = pygame.Rect(x_dir - larg, y, larg, alt)
        self.painel(r, (14, 20, 24), borda or C["linha"], 235)
        x = r.x + int(5 * s)
        for sup, g in conteudo:
            self.tela.blit(sup, (x, r.centery - sup.get_height() // 2))
            x += sup.get_width() + int(g * s)
        return r

    def _barra(self, larg, frac, cor):
        s = self.s
        sup = pygame.Surface((int(larg * s), max(3, int(4 * s))), pygame.SRCALPHA)
        sup.fill((40, 52, 60))
        pygame.draw.rect(sup, cor, (0, 0, int(larg * s * max(0, min(1, frac))), sup.get_height()))
        return sup

    def desenhar_hud(self):
        c = self.caso
        s = self.s
        r = self.RR(0, 0, LW, OY)
        pygame.draw.rect(self.tela, C["barra"], r)
        pygame.draw.line(self.tela, C["ambar"], r.bottomleft, r.bottomright)
        f, fb = self.f["peq"], self.f["corpo_b"]
        y = self.P(0, (OY - 15) / 2)[1]
        x = self.P(LW - 4, 0)[0]
        # som
        x = self._chip(x, y, [(f.render("♪" if self.som.ligado else "♪ ×", True, C["fraco"]), 0)]).x - int(3 * s)
        # pistas
        x = self._chip(x, y, [(fb.render("◆", True, C["azul2"]), 3),
                              (fb.render(f"{len(c.pistas)}/{len(PISTAS_PRINCIPAIS)}", True, C["texto"]), 4),
                              (self._barra(22, len(c.pistas) / len(PISTAS_PRINCIPAIS), C["azul2"]), 0)]).x - int(3 * s)
        # credibilidade
        coracoes = "♥" * c.credibilidade + "♡" * (CREDIBILIDADE_INICIAL - c.credibilidade)
        x = self._chip(x, y, [(fb.render(coracoes, True, C["cobre2"]), 0)],
                       C["cobre"] if c.credibilidade == 1 else None).x - int(3 * s)
        # pontos
        x = self._chip(x, y, [(fb.render("★", True, C["ambar"]), 3),
                              (fb.render(str(c.pontos), True, C["texto"]), 0)]).x - int(3 * s)
        # horas
        frac = c.horas / HORAS_INICIAIS
        cor_h = C["cobre2"] if c.horas <= 5 else C["ambar"]
        resta_min = max(0, int((PRAZO - c.relogio).total_seconds() // 60))
        txt_h = f"{c.horas}h" if c.horas >= 1 else f"{resta_min} min"
        x = self._chip(x, y, [(fb.render(txt_h, True, cor_h), 4),
                              (self._barra(34, frac, cor_h), 0)],
                       C["cobre"] if c.horas <= 5 else None).x
        # capítulo + objetivo (à esquerda, cortado para não invadir os chips)
        x0 = self.P(6, 0)[0]
        limite = x - int(8 * s) - x0
        tit = fb.render(self._cortar(CAPITULOS.get(c.cap, ""), "corpo_b", limite), True, C["ambar"])
        self.tela.blit(tit, (x0, self.P(0, 1.5)[1]))
        if self.objetivo:
            rot = f.render("OBJETIVO", True, C["tinta"])
            tag = pygame.Rect(x0, self.P(0, 1.5)[1] + tit.get_height() + int(1 * s),
                              rot.get_width() + int(8 * s), rot.get_height() + int(2 * s))
            pygame.draw.rect(self.tela, C["ambar"], tag, border_radius=int(2 * s))
            self.tela.blit(rot, (tag.x + int(4 * s), tag.y + int(1 * s)))
            obj = f.render(self._cortar(self.objetivo, "peq", limite - tag.w - int(6 * s)), True, C["texto"])
            self.tela.blit(obj, (tag.right + int(5 * s), tag.y + int(1 * s)))
        # nome do local (etiqueta legível sobre o cenário)
        nm = f.render(NOMES_SALAS[c.sala], True, C["ambar"])
        nr = pygame.Rect(x0 - int(2 * s), self.P(0, OY + 2)[1], nm.get_width() + int(8 * s), nm.get_height() + int(2 * s))
        self.painel(nr, (9, 11, 14), C["linha"], 200)
        self.tela.blit(nm, (nr.x + int(4 * s), nr.y + int(1 * s)))
        # relógio da cena (canto inferior direito, como carimbo de câmera de segurança)
        if self.painel_aberto or self.carta:
            return
        rel = texto_relogio(c.relogio)
        im = fb.render(rel, True, C["ambar"])
        r = pygame.Rect(0, 0, im.get_width() + int(18 * s), im.get_height() + int(6 * s))
        r.bottomright = self.P(LW - 4, LH - 4)
        self.painel(r, (9, 11, 14), C["linha"], 220)
        pygame.draw.circle(self.tela, (235, 80, 70) if int(self.t * 1.5) % 2 == 0 else (90, 30, 28),
                           (r.x + int(7 * s), r.centery), max(2, int(2 * s)))
        self.tela.blit(im, (r.x + int(13 * s), r.y + int(3 * s)))
        self.desenhar_dock()

    def _marcador(self, sx, sy, pendente):
        """Selo sobre objetos/pessoas: ! âmbar = pendente · ✓ verde = já investigado."""
        s = self.s
        rad = max(4, int(5 * s))
        cor = C["ambar"] if pendente else C["verde"]
        if pendente:
            sy += int(math.sin(self.t * 4) * 2 * s)
        pygame.draw.circle(self.tela, (0, 0, 0), (sx + 1, sy + 1), rad + 1)
        pygame.draw.circle(self.tela, cor, (sx, sy), rad)
        g = self.f["peq"].render("!" if pendente else "✓", True, C["tinta"])
        self.tela.blit(g, (sx - g.get_width() // 2, sy - g.get_height() // 2))

    def desenhar_marcadores(self):
        c = self.caso
        if c.cap == 0:
            return
        for r, p, nome in self.objeto_em(c.sala):
            if p == "telefone":
                if c.cap > 1 and "telefone" not in c.feitos:
                    continue
                pendente = "telefone" not in c.feitos
            else:
                pendente = (c.sala, p) not in c.examinados or self.pode_reexaminar(c.sala, p)
            topo = r.top + OY - 7
            if topo < OY + 7:            # objeto encostado na parede de cima: selo embaixo dele
                topo = r.bottom + OY + 7
            sx, sy = self.P(min(r.right - 6, r.centerx + 10), topo)
            self._marcador(sx, sy, pendente)
        pend_npc = {p[2] for p in self.pendencias() if p[1] == "npc"}
        for eid, e in self.ents.items():
            if eid == "helena" or not e.visivel or e.cao:
                continue
            if eid.startswith("al") and not eid.startswith("aluna"):
                continue
            if eid in pend_npc:
                pendente = True
            elif eid.startswith("aluna"):
                pendente = not c.aluna(eid)["interrogada"]
            elif eid in ("sofia", "olivia"):
                if eid not in c.feitos and c.cap == 2:
                    pendente = True
                elif eid in c.feitos or eid in c.conversas:
                    pendente = False
                else:
                    continue
            else:
                continue
            sx, sy = self.P(e.x + 9, e.y + OY - 36)
            self._marcador(sx, sy, pendente)

    def _cortar(self, texto, fonte, largura):
        f = self.f[fonte]
        if f.size(texto)[0] <= largura:
            return texto
        while texto and f.size(texto + "…")[0] > largura:
            texto = texto[:-1]
        return texto + "…"

    DOCK = [("Caderno", "C"), ("Suspeitas", "Q"), ("Dica", "H"), ("Acusar", "X"), ("Mapa", "TAB")]

    def desenhar_dock(self):
        """Barra de ferramentas clicável (canto inferior esquerdo; no celular, à direita)."""
        s = self.s
        f, fb = self.f["peq"], self.f["corpo_b"]
        apagado = self.ocupado()
        if self.toque:
            x, y = self.P(LW - 58, OY + 30)
        else:
            x, y = self.P(4, LH - 19)
        for nome, tecla in self.DOCK:
            tk_ = f.render(tecla, True, C["tinta"])
            lb = f.render(nome, True, C["texto"])
            kw = max(tk_.get_width() + int(6 * s), int(11 * s))
            w = kw + lb.get_width() + int(10 * s)
            h = int(15 * s)
            r = pygame.Rect(x, y, w if not self.toque else int(54 * s), h)
            sup = pygame.Surface(r.size, pygame.SRCALPHA)
            sup.fill((14, 20, 24, 150 if apagado else 225))
            self.tela.blit(sup, r.topleft)
            pygame.draw.rect(self.tela, C["linha"], r, 1, border_radius=int(3 * s))
            k = pygame.Rect(r.x + int(2 * s), r.y + int(2 * s), kw, h - int(4 * s))
            pygame.draw.rect(self.tela, C["cobre"] if nome == "Acusar" else C["ambar"], k, border_radius=int(2 * s))
            self.tela.blit(tk_, (k.centerx - tk_.get_width() // 2, k.centery - tk_.get_height() // 2))
            self.tela.blit(lb, (k.right + int(4 * s), r.centery - lb.get_height() // 2))
            self.botoes_ui[nome] = r
            if self.toque:
                y += h + int(3 * s)
            else:
                x = r.right + int(3 * s)

    # ---------------- briefing (tela de comandos)
    BRIEFING = [
        ("CONTROLES", [
            ("WASD", "Andar", "Mova a Helena pelo cenário (ou use as setas)."),
            ("E", "Interagir", "Conversar, examinar objetos e avançar as falas. O aviso [E] aparece em cima "
                               "do que dá para usar."),
            ("↓", "Seta guia", "A seta âmbar mostra o próximo passo da história: com quem falar, onde "
                               "investigar ou por onde sair."),
            ("TAB", "Mapa", "Viajar entre os locais (45 min). O destino certo vem marcado como OBJETIVO."),
            ("ESC", "Pausa", "Salvar, salvar e sair ou rever este resumo. O jogo também salva sozinho a "
                             "cada capítulo."),
        ]),
        ("FERRAMENTAS", [
            ("C", "Caderno", "Proposições descobertas (as letras dos slides), fichas dos itens (quem usou, "
                             "quando, para quê), dos locais e as regras de inferência."),
            ("Q", "Suspeitas", "Compare os traços da assassina vistos nas câmeras com cada suspeita e "
                               "descarte quem não bate."),
            ("H", "Dica", "1ª: uma pista para pensar (−15). Pediu de novo: o caminho exato (−30). Nunca entrega a culpada."),
            ("X", "Acusar", "Arrisque quem matou e por quê. Errar custa 150 pontos e 1 de credibilidade."),
        ]),
        ("HUD — NA TELA", [
            ("46h", "Prazo", "A promotoria deu 48h desde o crime. Cada ação avança o relógio: examinar 30 min, "
                             "interrogar 45 min, viajar 45 min. Acabou? Acusação obrigatória."),
            ("★", "Pontos", "Pistas, conversas e acertos somam; dicas e erros tiram."),
            ("♥", "Credibilidade", "Você tem 3 chances. Perdeu todas: está fora do caso."),
            ("◆", "Pistas", "Pistas principais encontradas, de 9."),
            ("●", "Relógio", "Data e hora da cena na história (canto inferior direito). Começa na noite do "
                             "crime, ter 03/02/2026."),
        ]),
    ]

    def _fundo_inteiro(self, chave, alfa):
        """Imagem de fundo INTEIRA (sem cortar em cima/embaixo), com as sobras preenchidas pela
        própria imagem desfocada."""
        W, H = self.tela.get_size()
        im = self.img.get(chave)
        if not im:
            return
        k = ("fundo_inteiro", chave, W, H, alfa)
        if k not in self.retratos:
            iw, ih = im.get_size()
            base = pygame.Surface((W, H))
            esc_f = max(W / iw, H / ih)
            peq = pygame.transform.smoothscale(im, (max(1, iw // 24), max(1, ih // 24)))
            borrado = pygame.transform.smoothscale(peq, (int(iw * esc_f) + 1, int(ih * esc_f) + 1))
            base.blit(borrado, ((W - borrado.get_width()) // 2, (H - borrado.get_height()) // 2))
            esc = min(W / iw, H / ih)
            nit = pygame.transform.smoothscale(im, (int(iw * esc), int(ih * esc)))
            base.blit(nit, ((W - nit.get_width()) // 2, (H - nit.get_height()) // 2))
            base.set_alpha(alfa)
            self.retratos[k] = base
        self.tela.blit(self.retratos[k], (0, 0))

    def _layout_briefing(self, larg):
        """Escolhe fonte e espaçamento para que as 3 colunas caibam inteiras nos cartões."""
        s = self.s
        alt_max = int(210 * s)
        for fonte, gap in (("peq", 4), ("peq", 2), ("mini", 3), ("mini", 1)):
            fp = self.f[fonte]
            maior = 0
            for _, itens in self.BRIEFING:
                h = int(19 * s)
                for _, _, desc in itens:
                    h += int(13 * s) + len(quebrar(desc, fp, larg)) * fp.get_linesize() + int(gap * s)
                maior = max(maior, h)
            if maior <= alt_max - int(4 * s):
                break
        return fonte, gap

    def desenhar_briefing(self, rotulo=None):
        s = self.s
        W, H = self.tela.get_size()
        self.tela.fill(C["bg"])
        self._fundo_inteiro("salao", 38)
        self.texto("Antes de começar: como funciona a investigação", "h1", C["texto"], W // 2,
                   self.P(0, 8)[1], centro=True)
        fb = self.f["corpo_b"]
        col_w = 148
        larg_txt = int(col_w * s) - int(12 * s)
        fonte, gap = self._layout_briefing(larg_txt)
        fp = self.f[fonte]
        for ci, (titulo, itens) in enumerate(self.BRIEFING):
            x0 = 10 + ci * (col_w + 8)
            r = self.RR(x0, 28, col_w, 210)
            self.painel(r, (12, 17, 21), C["linha"], 225)
            self.tela.blit(fb.render(titulo, True, C["ambar"]), (r.x + int(6 * s), r.y + int(5 * s)))
            y = r.y + int(19 * s)
            for tecla, nome, desc in itens:
                kt = fb.render(tecla, True, C["tinta"])
                kw = max(kt.get_width() + int(6 * s), int(14 * s))
                kr = pygame.Rect(r.x + int(6 * s), y, kw, int(12 * s))
                cor = C["cobre"] if nome == "Acusar" else C["ambar"]
                pygame.draw.rect(self.tela, cor, kr, border_radius=int(2 * s))
                self.tela.blit(kt, (kr.centerx - kt.get_width() // 2, kr.centery - kt.get_height() // 2))
                self.tela.blit(fb.render(nome, True, C["texto"]), (kr.right + int(5 * s), y))
                y += int(13 * s)
                for linha in quebrar(desc, fp, larg_txt):
                    self.tela.blit(fp.render(linha, True, C["fraco"]), (r.x + int(6 * s), y))
                    y += fp.get_linesize()
                y += int(gap * s)
            self._medida_brief = max(getattr(self, "_medida_brief", 0), y - r.bottom)
        rot = rotulo or ("E / Enter — Começar o caso" if getattr(self, "briefing", None) == "inicio"
                         else "E / ESC — Voltar ao jogo")
        im = fb.render(rot, True, C["tinta"])
        br = pygame.Rect(0, 0, im.get_width() + int(20 * s), im.get_height() + int(8 * s))
        br.midbottom = (W // 2, self.P(0, LH - 6)[1])
        pygame.draw.rect(self.tela, C["ambar"], br, border_radius=int(4 * s))
        self.tela.blit(im, (br.x + int(10 * s), br.y + int(4 * s)))

    # ---------------- guia de objetivo (setas)
    def localizar_pista(self, pid):
        for chave, v in self.caso.mapa.items():
            if v == ("pista", pid):
                return chave
        return None

    def pendencias(self):
        """Tarefas obrigatórias que faltam no capítulo, na ordem da história: (sala, tipo, alvo)."""
        c = self.caso
        f = c.feitos
        out = []
        if c.cap == 1:
            out.append(("escritorio", "ponto", "telefone") if "telefone" not in f else ("salao", "chegar", None))
        elif c.cap == 2:
            if "sofia" not in f:
                out.append(("salao", "npc", "sofia"))
            if "olivia" not in f:
                out.append(("banheiro_baile", "npc", "olivia"))
            for pid in ("corpo", "cam_baile", "faca"):
                if pid not in c.pistas:
                    out.append(self.localizar_pista(pid) + ("pista",))
        elif c.cap == 3:
            for pid in (("cam_univ",) if "cam_univ" not in c.pistas else ("terra", "livro")):
                if pid not in c.pistas:
                    out.append(self.localizar_pista(pid) + ("pista",))
        elif c.cap == 4:
            for a in c.alunas:
                if not a["interrogada"]:
                    out.append(("interrogatorio", "npc", a["id"]))
            if not out and "entrevista" not in f:
                out.append(("interrogatorio", "npc", "olivia"))
        elif c.cap == 5:
            for pid in ("celular", "max"):
                if pid not in c.pistas:
                    out.append(self.localizar_pista(pid) + ("pista",))
        elif c.cap == 6:
            if "comparacao" not in f:
                out.append(("interrogatorio", "ponto", 0))
            elif "acusacao" not in f:
                out.append(("interrogatorio", "npc", "olivia"))
        # normaliza (sala, idx, "pista") -> (sala, "pista", idx)
        return [(p[0], "pista", p[1]) if len(p) == 3 and p[2] == "pista" else p for p in out]

    def destino_sugerido(self):
        p = self.pendencias()
        if not p:
            return None
        sala = p[0][0]
        return "salao" if sala == "banheiro_baile" else sala

    def alvo_objetivo(self):
        """(x, y_topo, rótulo) em coordenadas da sala para a seta guia, ou None."""
        c = self.caso
        if c.cap == 0:
            return None
        pend = self.pendencias()
        if not pend:
            return None
        aqui = [p for p in pend if p[0] == c.sala]
        if aqui:
            sala, tipo, alvo = aqui[0]
            if tipo == "npc" and alvo in self.ents and self.ents[alvo].visivel:
                e = self.ents[alvo]
                verbo = "Interrogue" if alvo.startswith("aluna") else "Fale com"
                return (e.x, e.y - 34, e.y + 2, f"{verbo} {e.nome}", ("npc", alvo))
            if tipo == "ponto":
                for r, p, nome in self.objeto_em(c.sala):
                    if p == alvo:
                        return (r.centerx, r.top - 6, r.bottom + 4,
                                "Atenda o telefone" if alvo == "telefone" else f"Use: {nome}", ("ponto", alvo))
            if tipo in ("pista", "ponto"):
                melhor = None
                for r, p, nome in self.objeto_em(c.sala):
                    if p == "telefone" or ((c.sala, p) in c.examinados and not self.pode_reexaminar(c.sala, p)):
                        continue
                    d = math.hypot(r.centerx - self.player.x, r.centery - self.player.y)
                    if melhor is None or d < melhor[0]:
                        melhor = (d, r)
                if melhor:
                    rr = melhor[1]
                    p_alvo = next(p for r2, p, n2 in self.objeto_em(c.sala) if r2 == rr)
                    return (rr.centerx, rr.top - 6, rr.bottom + 4, "Investigue aqui", ("ponto", p_alvo))
        destino = pend[0][0]
        S = SALAS[c.sala]
        if "porta_lado" in S and (c.sala == "banheiro_baile" or destino == "banheiro_baile"):
            (tx, ty), dest, _ = S["porta_lado"]
            return (tx * T + T / 2, ty * T - 14, ty * T + 18, "Porta → " + NOMES_SALAS[dest], ("porta", None))
        if "saida" in S:
            tx, ty = S["saida"]
            sug = self.destino_sugerido()
            return (tx * T + T, ty * T - 10, ty * T, "Saída → " + (NOMES_SALAS[sug] if sug else "mapa"), ("saida", None))
        return None

    def desenhar_guia(self):
        if self.ocupado() or self.toque and False:
            return
        alvo = self.alvo_objetivo()
        if not alvo:
            return
        x, y, y_base, rotulo, chave = alvo
        s = self.s
        perto = self.alvo_proximo()
        if perto and (perto[0], perto[1]) == chave:
            return  # o aviso "E" já está em cima do alvo
        bob = math.sin(self.t * 5) * 3
        cor = C["ambar"]
        im = self.f["peq"].render(rotulo, True, C["tinta"])
        lab = pygame.Rect(0, 0, im.get_width() + int(8 * s), im.get_height() + int(4 * s))
        para_cima = (y + OY - 30) < OY + 14  # alvo encostado no topo: seta embaixo apontando para cima
        if not para_cima:
            sx, sy = self.P(x, y + OY + bob)
            pts = [(sx - int(7 * s), sy - int(9 * s)), (sx + int(7 * s), sy - int(9 * s)), (sx, sy)]
            haste = (sx - int(2.5 * s), sy - int(16 * s), int(5 * s), int(8 * s))
            lab.midbottom = (sx, sy - int(17 * s))
        else:
            sx, sy = self.P(x, y_base + OY - bob)
            pts = [(sx - int(7 * s), sy + int(9 * s)), (sx + int(7 * s), sy + int(9 * s)), (sx, sy)]
            haste = (sx - int(2.5 * s), sy + int(8 * s), int(5 * s), int(8 * s))
            lab.midtop = (sx, sy + int(17 * s))
        pygame.draw.polygon(self.tela, (0, 0, 0), [(px + 2, py + 2) for px, py in pts])
        pygame.draw.polygon(self.tela, cor, pts)
        pygame.draw.rect(self.tela, cor, haste)
        lab.clamp_ip(self.RR(2, OY + 1, LW - 4, LH - OY - 3))
        pygame.draw.rect(self.tela, cor, lab, border_radius=int(3 * s))
        self.tela.blit(im, (lab.x + int(4 * s), lab.y + int(2 * s)))
        # bússola ao lado da Helena quando o alvo está longe
        p = self.player
        dx, dy = x - p.x, (y + 20) - p.y
        d = math.hypot(dx, dy)
        if d > 70:
            ux, uy = dx / d, dy / d
            cx, cy = self.P(p.x + ux * 22, p.y - 14 + uy * 22 + OY)
            ang = [(ux * 6, uy * 6), (-uy * 4 - ux * 3, ux * 4 - uy * 3), (uy * 4 - ux * 3, -ux * 4 - uy * 3)]
            poly = [(cx + a * s, cy + b * s) for a, b in ang]
            pygame.draw.polygon(self.tela, (0, 0, 0), [(a + 2, b + 2) for a, b in poly])
            pygame.draw.polygon(self.tela, cor, poly)

    def desenhar_prompt(self):
        """Aviso de interação ancorado em cima da pessoa/objeto, com tecla E em destaque."""
        if self.ocupado():
            return
        alvo = self.alvo_proximo()
        if not alvo:
            return
        tipo, val, nome = alvo
        c = self.caso
        if tipo == "npc":
            e = self.ents[val]
            ax, ay = e.x, e.y - 36
            if val.startswith("aluna"):
                acao, cor = f"Interrogar {c.aluna(val)['nome'].split()[0]}  ·  45 min", C["azul2"]
            elif val == "max":
                acao, cor = "Aproximar-se do Max  ·  30 min", C["azul2"]
            else:
                acao, cor = f"Conversar com {nome}", C["azul2"]
        else:
            r = next(rr for rr, p, n in self.objeto_em(c.sala) if p == val)
            ax, ay = r.centerx, r.top - 4
            if val == "telefone":
                acao, cor = "Atender o telefone", C["verde"]
            else:
                custo = "sem custo" if c.exame_gratis else "30 min"
                acao, cor = f"Examinar {nome}  ·  {custo}", C["ambar"]
        s = self.s
        tecla = self.f["corpo_b"].render("E", True, C["tinta"])
        txt = self.f["corpo_b"].render(acao, True, cor)
        kw = max(tecla.get_width(), tecla.get_height()) + int(6 * s)
        larg = kw + txt.get_width() + int(14 * s)
        alt = kw + int(4 * s)
        sx, sy = self.P(ax, ay + OY)
        r = pygame.Rect(0, 0, larg, alt)
        r.midbottom = (sx, sy - int(4 * s))
        r.clamp_ip(self.RR(2, OY + 1, LW - 4, LH - OY - 3))
        pygame.draw.rect(self.tela, (9, 11, 14), r, border_radius=int(4 * s))
        pygame.draw.rect(self.tela, cor, r, max(1, int(0.8 * s)), border_radius=int(4 * s))
        k = pygame.Rect(r.x + int(2 * s), r.y + int(2 * s), kw, kw)
        pygame.draw.rect(self.tela, cor, k, border_radius=int(3 * s))
        pygame.draw.line(self.tela, escurecer(cor, 0.6), k.bottomleft, k.bottomright, max(1, int(s)))
        self.tela.blit(tecla, (k.centerx - tecla.get_width() // 2, k.centery - tecla.get_height() // 2))
        self.tela.blit(txt, (k.right + int(6 * s), r.centery - txt.get_height() // 2))

    def desenhar_balao(self):
        b = self.balao
        if not b:
            return
        pagina = b["pags"][b["i"]]
        n = b["n"]
        completo = n >= len(pagina)
        piscar = completo and int(self.t * 3) % 2 == 0
        s = self.s
        W, H = self.tela.get_size()
        nl = pagina.count("\n") + 1
        if b["tipo"] == "cena":
            self.desenhar_cena(b, pagina, n, nl, piscar)
            return
        if b["tipo"] == "narra":
            f = self.f["narra"]
            alt = int(nl * f.get_linesize() * 1.12 + 18 * s)
            r = pygame.Rect(self.P((LW - LARG_NARRA) / 2, OY + 8), (int(LARG_NARRA * s), alt))
            self.painel(r, (9, 11, 14), C["ambar"], 245)
            yf = self._desenhar_digitado(pagina, n, "narra", C["papel"], r.x + int(11 * s), r.y + int(8 * s))
            self._medida = ("narra", r, r.y + int(8 * s) + int(nl * f.get_linesize() * 1.12))
            if piscar:
                self._seta_baixo(r.right - int(9 * s), r.bottom - int(7 * s), C["ambar"])
            return
        if b["tipo"] == "tel":
            f = self.f["corpo"]
            alt = max(int(70 * s), int(nl * f.get_linesize() * 1.12 + 28 * s))
            r = pygame.Rect(0, 0, int(LARG_TEL * s), alt)
            r.midbottom = self.P(LW / 2, LH - 8)
            self.painel(r, (9, 11, 14), C["azul"], 245)
            ret = self.retrato(b["retrato"], 60 * s)
            if ret:
                self.tela.blit(ret, (r.x + int(5 * s), r.y + int(5 * s)))
                pygame.draw.rect(self.tela, C["azul"], (r.x + int(5 * s), r.y + int(5 * s), ret.get_width(), ret.get_height()), 1)
            tx = r.x + int(74 * s)
            self.tela.blit(self.f["corpo_b"].render(b["nome"].upper() + " · AO TELEFONE", True, C["azul2"]),
                           (tx, r.y + int(5 * s)))
            self._desenhar_digitado(pagina, n, "corpo", C["texto"], tx, r.y + int(18 * s))
            self._medida = ("tel", r, r.y + int(18 * s) + int(nl * f.get_linesize() * 1.12),
                            max(f.size(l)[0] for l in pagina.split("\n")) + tx)
            if piscar:
                self._seta_baixo(r.right - int(9 * s), r.bottom - int(7 * s), C["ambar"])
            return
        ent = self.ents.get(b["ent"])
        f = self.f["corpo"]
        ret = self.retrato(b["retrato"], 36 * s) if b.get("retrato") and b["retrato"] in self.img else None
        larg = int(LARG_FALA * s)
        alt_txt = int(nl * f.get_linesize() * 1.12)
        alt = max(int(46 * s) if ret else 0, alt_txt + int(24 * s))
        if ent:
            ax, ay = self.P(ent.x, ent.y + OY - 36)
        else:
            ax, ay = W // 2, H // 2
        r = pygame.Rect(0, 0, larg, alt)
        r.midbottom = (ax, ay - int(8 * s))
        r.clamp_ip(self.RR(4, OY + 2, LW - 8, LH - OY - 6))
        preto, borda = (9, 11, 14), C["papel"]
        ponta = [(ax - int(6 * s), r.bottom - 2), (ax + int(6 * s), r.bottom - 2),
                 (ax, min(max(ay, r.bottom + int(4 * s)), r.bottom + int(10 * s)))]
        if r.bottom < ay:
            pygame.draw.polygon(self.tela, preto, ponta)
            pygame.draw.lines(self.tela, borda, False, [ponta[0], ponta[2], ponta[1]], max(1, int(s * 0.8)))
        pygame.draw.rect(self.tela, preto, r, border_radius=int(6 * s))
        pygame.draw.rect(self.tela, borda, r, max(1, int(s * 0.8)), border_radius=int(6 * s))
        if r.bottom < ay:
            pygame.draw.line(self.tela, preto, (ponta[0][0] + 2, r.bottom - 1), (ponta[1][0] - 2, r.bottom - 1), max(1, int(s)))
        tx = r.x + int(8 * s)
        if ret:
            self.tela.blit(ret, (r.x + int(6 * s), r.y + int(6 * s)))
            pygame.draw.rect(self.tela, C["ambar"], (r.x + int(6 * s), r.y + int(6 * s), ret.get_width(), ret.get_height()), 1)
            tx = r.x + int(48 * s)
        self.tela.blit(self.f["corpo_b"].render(b["nome"].upper(), True, C["ambar"]), (tx, r.y + int(5 * s)))
        self._desenhar_digitado(pagina, n, "corpo", C["texto"], tx, r.y + int(17 * s))
        self._medida = ("fala", r, r.y + int(17 * s) + alt_txt, max(f.size(l)[0] for l in pagina.split("\n")) + tx)
        if piscar:
            self._seta_baixo(r.right - int(9 * s), r.bottom - int(7 * s), C["ambar"])

    def desenhar_cena(self, b, pagina, n, nl, piscar):
        """Ilustração da equipe em tela cheia, INTEIRA (sem cortes), com a legenda numa faixa embaixo."""
        s = self.s
        W, H = self.tela.get_size()
        self.tela.fill((0, 0, 0))
        f = self.f["narra"]
        # faixa da legenda: sempre do tamanho de 3 linhas, para a imagem não "pular" entre páginas
        alt_leg = int(3 * f.get_linesize() * 1.12 + 18 * s)
        margem = int(6 * s)
        area = pygame.Rect(0, margem, W, H - alt_leg - 3 * margem)
        chave = b["img"] + "_cena" if b["img"] + "_cena" in self.img else b["img"]
        im = self.img.get(chave)
        if im:
            iw, ih = im.get_width(), im.get_height()
            k_fundo = ("cena_fundo", chave, W, H)
            if k_fundo not in self.retratos:
                # fundo: a mesma imagem, desfocada e escurecida, preenchendo as laterais
                esc_f = max(W / iw, H / ih)
                peq = pygame.transform.smoothscale(im, (max(1, iw // 24), max(1, ih // 24)))
                fundo = pygame.transform.smoothscale(peq, (int(iw * esc_f), int(ih * esc_f)))
                vela = pygame.Surface(fundo.get_size(), pygame.SRCALPHA)
                vela.fill((0, 0, 0, 170))
                fundo.blit(vela, (0, 0))
                self.retratos[k_fundo] = fundo
            fundo = self.retratos[k_fundo]
            self.tela.blit(fundo, ((W - fundo.get_width()) // 2, (H - fundo.get_height()) // 2))
            esc = min(area.w / iw, area.h / ih)
            k = ("cena", chave, area.w, area.h)
            if k not in self.retratos:
                self.retratos[k] = pygame.transform.smoothscale(im, (int(iw * esc), int(ih * esc)))
            sup = self.retratos[k]
            ir = sup.get_rect(center=area.center)
            pygame.draw.rect(self.tela, (0, 0, 0), ir.inflate(int(4 * s), int(4 * s)))
            self.tela.blit(sup, ir)
        else:
            ir = area
        carimbo = b.get("data") or texto_relogio(self.caso.relogio)
        im_d = self.f["corpo_b"].render("● " + carimbo, True, (235, 80, 70) if b.get("data") else C["ambar"])
        pr = pygame.Rect(ir.x + int(6 * s), ir.y + int(6 * s), im_d.get_width() + int(10 * s),
                         im_d.get_height() + int(4 * s))
        self.painel(pr, (9, 11, 14), C["linha"], 210)
        self.tela.blit(im_d, (pr.x + int(5 * s), pr.y + int(2 * s)))
        if pagina:
            r = pygame.Rect(0, 0, int(LARG_CENA * s), alt_leg)
            r.midbottom = (W // 2, H - margem)
            self.painel(r, (9, 11, 14), C["ambar"], 235)
            self._desenhar_digitado(pagina, n, "narra", C["papel"], r.x + int(12 * s), r.y + int(8 * s))
            self._medida = ("cena", r, r.y + int(8 * s) + int(nl * f.get_linesize() * 1.12))
            if piscar:
                self._seta_baixo(r.right - int(9 * s), r.bottom - int(7 * s), C["ambar"])
        elif piscar:
            self.texto("E para continuar", "peq", C["ambar"], W // 2, H - alt_leg // 2 - margem, centro=True)

    def _layout_carta(self, cd):
        """Mede o conteúdo da carta e escolhe fontes que caibam no cartão."""
        s = self.s
        tem_img = bool(cd.get("img") and cd["img"] in self.img)
        larg = int(320 * s)
        larg_t = larg - (int(118 * s) if tem_img else 0)
        max_alt = int((LH - 40) * s)
        for fonte_txt, fonte_prop in (("carta", "peq"), ("corpo", "peq"), ("peq", "peq")):
            titulo = quebrar(cd["titulo"], self.f["h1"], larg_t)
            corpo = quebrar(cd["texto"], self.f[fonte_txt], larg_t)
            props = []
            for l in cd.get("novas") or []:
                props += quebrar(f"{l} = {PROPOSICOES.get(l.lstrip('¬'), '')}", self.f[fonte_prop], larg)
            alt_topo = (len(titulo) * self.f["h1"].get_linesize() + int(4 * s) +
                        len(corpo) * int(self.f[fonte_txt].get_linesize() * 1.1))
            if tem_img:
                alt_topo = max(alt_topo, int(84 * s))
            alt = (int(12 * s) + alt_topo + (int(14 * s) if cd.get("pts") else 0) +
                   ((int(13 * s) + len(props) * self.f[fonte_prop].get_linesize()) if props else 0) + int(22 * s))
            if alt <= max_alt:
                break
        if alt > max_alt and props:  # resume as proposições em uma linha
            letras = ", ".join(cd["novas"])
            props = quebrar(f"{letras}  (detalhes no caderno — tecla C)", self.f["peq"], larg)
            alt = (int(12 * s) + alt_topo + (int(14 * s) if cd.get("pts") else 0) +
                   int(13 * s) + len(props) * self.f["peq"].get_linesize() + int(22 * s))
        return titulo, corpo, props, fonte_txt, fonte_prop, larg, larg_t, min(alt, max_alt), tem_img

    def desenhar_carta(self, cd):
        s = self.s
        titulo, corpo, props, ft, fp, larg, larg_t, alt, tem_img = self._layout_carta(cd)
        r = pygame.Rect(0, 0, larg + int(20 * s), alt)
        r.center = self.P(LW / 2, OY + (LH - OY) / 2)
        self.painel(r, C["papel"], C["ambar"], 250)
        x, y = r.x + int(10 * s), r.y + int(8 * s)
        if tem_img:
            # imagem INTEIRA dentro de uma moldura de 110×80 (sem cortar rosto nem cenário)
            cw, ch = int(110 * s), int(80 * s)
            k = ("caixa", cd["img"], cw, ch)
            if k not in self.retratos:
                fonte_im = self.img[cd["img"]]
                esc = min(cw / fonte_im.get_width(), ch / fonte_im.get_height())
                self.retratos[k] = pygame.transform.smoothscale(
                    fonte_im, (max(1, int(fonte_im.get_width() * esc)), max(1, int(fonte_im.get_height() * esc))))
            im = self.retratos[k]
            caixa = pygame.Rect(r.right - cw - int(10 * s), y, cw, ch)
            pygame.draw.rect(self.tela, (20, 22, 26), caixa)
            self.tela.blit(im, im.get_rect(center=caixa.center))
            pygame.draw.rect(self.tela, C["tinta"], caixa, 1)
        y0 = y
        for l in titulo:
            self.tela.blit(self.f["h1"].render(l, True, C["cobre"]), (x, y))
            y += self.f["h1"].get_linesize()
        y += int(4 * s)
        texto = "\n".join(corpo)
        y = self._desenhar_digitado(texto, cd.get("n", 9999), ft, C["tinta"], x, y, 1.1)
        if cd.get("n", 9999) < len(cd["texto"]):
            return
        if tem_img:
            y = max(y, y0 + int(84 * s))
        if cd.get("pts"):
            self.tela.blit(self.f["corpo_b"].render(f"+{cd['pts']} pontos", True, (150, 100, 30)), (x, y))
            y += int(14 * s)
        if props:
            self.tela.blit(self.f["corpo_b"].render("Novas proposições no caderno:", True, C["tinta"]), (x, y))
            y += int(13 * s)
            for l in props:
                self.tela.blit(self.f[fp].render(l, True, (60, 66, 70)), (x, y))
                y += self.f[fp].get_linesize()
        self.texto("E / clique para continuar", "peq", C["cobre"], r.centerx, r.bottom - int(13 * s),
                   centro=True, sombra=False)
        self._medida = ("carta", r, y + int(12 * s), max([self.f[ft].size(l)[0] for l in corpo] + [0]) + x)

    def desenhar_capitulo(self):
        nome, rest, n = self.capitulo_titulo
        nome = nome[:int(n)]
        W, H = self.tela.get_size()
        a = max(0, min(1, rest / 0.6))
        f = pygame.Surface((W, int(60 * self.s)), pygame.SRCALPHA)
        f.fill((0, 0, 0, int(200 * a)))
        self.tela.blit(f, (0, H // 2 - int(30 * self.s)))
        im = self.f["titulo"].render(nome, True, C["texto"])
        im.set_alpha(int(255 * a))
        self.tela.blit(im, (W // 2 - im.get_width() // 2, H // 2 - im.get_height() // 2))
        pygame.draw.line(self.tela, C["ambar"], (W // 2 - int(60 * self.s), H // 2 + int(20 * self.s)),
                         (W // 2 + int(60 * self.s), H // 2 + int(20 * self.s)), 2)

    # ---------------- painel lateral da acusação
    def _perfil_assassina(self):
        c = self.caso
        out = []
        if "cam_baile" in c.pistas:
            out.append(("Cabelo", "ruivo", None))
            out.append(("No baile", "entrou no banheiro às 22:41 e saiu sozinha às 22:47", None))
        for k in TRACOS:
            conhecido = k in c.tracos_conhecidos
            out.append((TRACOS[k][0], c.helena[k] if conhecido else "? (ainda não descoberto)", None))
        return out

    def _ficha_suspeita(self, quem):
        """(título, linhas [(rótulo, valor, bate?)], observação)"""
        c = self.caso
        if quem == "sofia":
            linhas = [("Cabelo", "escuro", False)]
            obs = (f"Álibi: {c.sofia_alibi}." if "sofia" in c.feitos else "Álibi: ainda não ouvido.")
            return "Sofia Mori Nakamura", linhas, obs
        if quem == "ruiva":
            return "Uma aluna ruiva desconhecida", [], "Sem os registros de 2020, ela ainda não tem nome."
        if quem == "helena":
            if "entrevista" not in c.feitos:
                return "Helena Cortez (você)", [("Cabelo", "ruivo", True)], "Ainda não entrevistada."
            linhas = [("Cabelo", "ruivo", True)]
            for k in TRACOS:
                linhas.append((TRACOS[k][0], c.helena[k],
                               (k in c.tracos_conhecidos) or None))
            obs = "Testemunha de 2020 (amnésia dissociativa)."
            if "max" in c.feitos:
                obs += " Max a reconheceu."
            if "comparacao" in c.feitos:
                obs += " As câmeras do baile batem com ela."
            return "Helena Cortez (você)", linhas, obs
        a = c.aluna(quem)
        if not a["interrogada"]:
            return a["nome"], [("Cabelo", "ruivo", True)], "Ainda não interrogada."
        linhas = [("Cabelo", "ruivo", True)]
        for k, v in a["tracos"].items():
            if k in c.tracos_conhecidos:
                linhas.append((TRACOS[k][0], v, v == c.helena[k]))
            else:
                linhas.append((TRACOS[k][0], v, None))
        obs = "Álibi CONFIRMADO." if a["modo"] == "alibi" else "Álibi não confirmado."
        if quem in c.descartes:
            obs += " Liberada por você."
        return a["nome"], linhas, obs

    def _painel_suspeita(self, quem):
        blocos = [("QUEM PROCURAMOS — a assassina das câmeras", self._perfil_assassina(), None)]
        tit, linhas, obs = self._ficha_suspeita(quem)
        blocos.append(("SUSPEITA: " + tit, linhas, obs))
        return blocos

    def _painel_motivo(self, _v):
        c = self.caso
        fatos = []
        if "sofia" in c.feitos:
            fatos.append(("Beatriz", "amiga de Sofia; todos achavam que tinha ido para a Itália em maio de 2020", None))
        if "cam_univ" in c.pistas:
            fatos.append(("Gravações", "em 01/05/2020 o professor arrastou Beatriz para o banheiro do campus; "
                                       "ela nunca mais saiu", None))
        if "terra" in c.pistas:
            fatos.append(("Campus", "o corpo de Beatriz estava enterrado no jardim", None))
        if "celular" in c.pistas:
            fatos.append(("Celular", "o professor ficou com o celular dela para esconder o crime", None))
        if "entrevista" in c.feitos:
            fatos.append(("Testemunha", "Helena viu tudo, foi ameaçada e desenvolveu amnésia dissociativa", None))
        if "comparacao" in c.feitos:
            fatos.append(("Baile", "o crime foi no baile da turma em que Beatriz deveria ter se formado", None))
        return [("O QUE A INVESTIGAÇÃO JÁ MOSTROU", fatos, None)]

    def _desenhar_painel_lateral(self, blocos, r):
        s = self.s
        self.painel(r, C["card"], C["linha"], 248)
        larg = r.w - int(16 * s)
        for fonte in ("corpo", "peq", "mini"):
            fp, fb = self.f[fonte], self.f["corpo_b"]
            plano = []
            for tit, linhas, obs in blocos:
                plano.append(("tit", quebrar(tit, fb, larg)))
                for rot, val, ok in linhas:
                    marca = "" if ok is None else ("✓ " if ok else "✗ ")
                    plano.append(("lin", (ok, quebrar(f"{marca}{rot}: {val}", fp, larg))))
                if obs:
                    plano.append(("obs", quebrar(obs, fp, larg)))
                plano.append(("esp", None))
            alt = 0
            for tipo, d in plano:
                if tipo == "tit":
                    alt += len(d) * fb.get_linesize() + int(2 * s)
                elif tipo == "lin":
                    alt += len(d[1]) * fp.get_linesize()
                elif tipo == "obs":
                    alt += len(d) * fp.get_linesize() + int(2 * s)
                else:
                    alt += int(6 * s)
            if alt <= r.h - int(12 * s):
                break
        x, y = r.x + int(8 * s), r.y + int(6 * s)
        for tipo, d in plano:
            if tipo == "tit":
                for l in d:
                    self.tela.blit(fb.render(l, True, C["ambar"]), (x, y))
                    y += fb.get_linesize()
                y += int(2 * s)
            elif tipo == "lin":
                ok, ls = d
                cor = C["texto"] if ok is None else ((120, 190, 140) if ok else (220, 110, 95))
                for l in ls:
                    self.tela.blit(fp.render(l, True, cor), (x, y))
                    y += fp.get_linesize()
            elif tipo == "obs":
                for l in d:
                    self.tela.blit(fp.render(l, True, C["fraco"]), (x, y))
                    y += fp.get_linesize()
                y += int(2 * s)
            else:
                pygame.draw.line(self.tela, C["linha"], (x, y + int(2 * s)), (r.right - int(8 * s), y + int(2 * s)))
                y += int(6 * s)
        self._medida = ("painel_acusacao", r, y - int(6 * s))

    def desenhar_menu(self, m):
        if m.painel:
            return self._desenhar_menu_com_painel(m)
        n = len(m.opcoes)
        fs, ft = self.f["peq"] if len(m.subtitulo) > 220 else self.f["corpo"], self.f["h2"]
        tit_lin = quebrar(m.titulo, ft, int(340 * self.s))
        sub_lin = quebrar(m.subtitulo, fs, int(340 * self.s)) if m.subtitulo else []
        ls = fs.get_linesize() / self.s
        alt = 10 + len(tit_lin) * ft.get_linesize() / self.s + 4 + len(sub_lin) * ls + 4 + n * 16 + 6
        topo = max(OY + 4, (LH - alt) / 2)
        r = self.RR(60, topo, 360, alt)
        self.painel(r, C["card"], C["ambar"], 248)
        y = r.y + int(6 * self.s)
        for l in tit_lin:
            self.tela.blit(ft.render(l, True, C["ambar"]), (r.x + int(10 * self.s), y))
            y += ft.get_linesize()
        y += int(4 * self.s)
        for l in sub_lin:
            self.tela.blit(fs.render(l, True, C["fraco"]), (r.x + int(10 * self.s), y))
            y += fs.get_linesize()
        self.desenhar_opcoes(m, 70, (y - self.oy) / self.s + 4, 340, 16)

    def _desenhar_menu_com_painel(self, m):
        s = self.s
        n = len(m.opcoes)
        fs, ft = self.f["peq"], self.f["h2"]
        larg = 200
        tit_lin = quebrar(m.titulo, ft, int((larg - 20) * s))
        sub_lin = quebrar(m.subtitulo, fs, int((larg - 20) * s)) if m.subtitulo else []
        alt = (10 + len(tit_lin) * ft.get_linesize() / s + 4 + len(sub_lin) * fs.get_linesize() / s + 4 +
               n * 16 + 6)
        topo = OY + 18
        r = self.RR(8, topo, larg, max(alt, 60))
        self.painel(r, C["card"], C["ambar"], 248)
        y = r.y + int(6 * s)
        for l in tit_lin:
            self.tela.blit(ft.render(l, True, C["ambar"]), (r.x + int(10 * s), y))
            y += ft.get_linesize()
        y += int(4 * s)
        for l in sub_lin:
            self.tela.blit(fs.render(l, True, C["fraco"]), (r.x + int(10 * s), y))
            y += fs.get_linesize()
        self.desenhar_opcoes(m, 16, (y - self.oy) / s + 4, larg - 16, 16)
        sel = m.opcoes[m.sel][1] if m.opcoes else None
        rp = self.RR(214, topo, LW - 214 - 8, LH - topo - 28)
        self._desenhar_painel_lateral(m.painel(sel), rp)

    def _lista_suspeitas(self):
        c = self.caso
        out = [("sofia", "Sofia Mori Nakamura", "Cabelo escuro. " + (f"Álibi: {c.sofia_alibi}." if "sofia" in c.feitos else ""))]
        if "livro" in c.pistas:
            for a in c.alunas:
                info = (" · ".join(f"{TRACOS[k][0]}: {v}" for k, v in a["tracos"].items()) +
                        (" · álibi CONFIRMADO" if a["modo"] == "alibi" else " · álibi não confirmado")
                        if a["interrogada"] else "Ainda não interrogada.")
                out.append((a["id"], a["nome"], info))
            if "entrevista" in c.feitos:
                info = " · ".join(f"{TRACOS[k][0]}: {v}" for k, v in c.helena.items())
            else:
                info = "Ainda não entrevistada. Você não se lembra de nada de 2020."
            out.append(("helena", "Helena Cortez (você) — 5ª aluna", info))
        return out

    def desenhar_suspeitas(self):
        c = self.caso
        s = self.s
        r = self.RR(24, OY + 4, 432, LH - OY - 10)
        self.painel(r, C["card"], C["ambar"], 250)
        x = r.x + int(10 * s)
        larg = r.w - int(20 * s)
        tit = self.f["h1"].render("Quadro de suspeitas", True, C["texto"])
        self.tela.blit(tit, (x, r.y + int(5 * s)))
        y = r.y + int(5 * s) + tit.get_height() + int(2 * s)
        tr = "   ".join(f"{TRACOS[k][0]}: {c.helena[k] if k in c.tracos_conhecidos else '?'}" for k in TRACOS)
        cab = "ruivo" if "cam_baile" in c.pistas else "?"
        y = self.bloco(f"A ASSASSINA (câmeras/perícia) — Cabelo: {cab}   {tr}", "corpo_b", C["cobre2"], x, y, larg, 1.05)
        rodape = self.f["peq"].render("↑↓ escolher · Enter descartar/reconsiderar · Q ou ESC fechar", True, C["ambar"])
        fundo_lista = r.bottom - rodape.get_height() - int(8 * s)
        lista = self._lista_suspeitas()
        self.sel_susp = max(0, min(getattr(self, "sel_susp", 0), len(lista) - 1))
        y += int(4 * s)
        fb, fp = self.f["corpo_b"], self.f["peq"]
        for i, (chave, nome, info) in enumerate(lista):
            desc = chave in c.descartes
            linhas = quebrar(info, fp, larg - int(8 * s))[:2]
            alt = fb.get_linesize() + len(linhas) * fp.get_linesize() + int(4 * s)
            if y + alt > fundo_lista:
                self.tela.blit(fp.render("…", True, C["fraco"]), (x, y))
                break
            rr = pygame.Rect(x - int(4 * s), y - int(2 * s), larg + int(8 * s), alt)
            if i == self.sel_susp:
                pygame.draw.rect(self.tela, C["card2"], rr)
                pygame.draw.rect(self.tela, C["ambar"], rr, 1)
            self.tela.blit(fb.render(self._cortar(("[x] " if desc else "") + nome, "corpo_b", larg), True,
                                     C["fraco"] if desc else C["texto"]), (x, y))
            yy = y + fb.get_linesize()
            for l in linhas:
                self.tela.blit(fp.render(l, True, C["fraco"]), (x, yy))
                yy += fp.get_linesize()
            y += alt + int(2 * s)
        self.tela.blit(rodape, (r.centerx - rodape.get_width() // 2, r.bottom - rodape.get_height() - int(4 * s)))

    ABAS_CADERNO = ["Proposições", "Itens", "Locais", "Regras"]

    def _linhas_caderno(self, aba):
        c = self.caso
        L = []
        if aba == 0:
            ordem = list(PROPOSICOES)
            L.append((f"{len(c.props)} de {len(PROPOSICOES)} proposições descobertas", C["cobre"]))
            for l in sorted(c.props, key=ordem.index):
                L.append((("¬" if l in NEGADAS else "") + f"{l} — {PROPOSICOES[l]}", C["tinta"]))
        elif aba == 1:
            for pid, (nome, quem, quando, paraque, pista) in FICHAS_ITENS.items():
                if pista not in c.pistas:
                    continue
                pq = paraque(c) if callable(paraque) else paraque
                L.append((nome.upper(), C["cobre"]))
                L.append((f"Quem usou: {quem(c)}", C["tinta"]))
                L.append((f"Quando: {quando}", C["tinta"]))
                L.append((f"Para quê: {pq}", C["tinta"]))
                L.append(("", C["tinta"]))
            if not L:
                L.append(("Nenhum item encontrado ainda.", (120, 120, 120)))
        elif aba == 2:
            visit = getattr(c, "visitadas", set())
            for sid in LOCAIS_SLIDES:
                if sid not in visit:
                    continue
                linhas = [t for t, cond in FICHAS_LOCAIS[sid]
                          if cond is None or cond in c.feitos or cond in c.pistas or cond in c.props or cond in self.chegou]
                if not linhas:
                    continue
                L.append((NOMES_SALAS[sid].upper() + " — quem esteve aqui e quando", C["cobre"]))
                L += [("• " + t, C["tinta"]) for t in linhas]
                L.append(("", C["tinta"]))
            if not L:
                L.append(("Nenhum local registrado ainda.", (120, 120, 120)))
        else:
            for k, v in REGRAS_EXPLICADAS.items():
                L.append((f"{k}:  {v}", C["tinta"]))
            L.append(("", C["tinta"]))
            L.append(("EVIDÊNCIAS ENCONTRADAS", C["cobre"]))
            achadas = [NOMES_PISTAS[p] for p in PISTAS_PRINCIPAIS if p in c.pistas]
            L += [("• " + n, C["tinta"]) for n in achadas] or [("Nenhuma ainda.", (120, 120, 120))]
        return L

    def desenhar_caderno(self):
        s = self.s
        r = self.RR(30, OY + 4, 420, LH - OY - 12)
        self.painel(r, C["papel"], C["ambar"], 252)
        x = r.x + int(10 * s)
        aba = getattr(self, "aba_caderno", 0)
        self.rects_abas = []
        ax = x
        for i, nome in enumerate(self.ABAS_CADERNO):
            f = self.f["corpo_b"]
            im = f.render(nome, True, C["papel"] if i == aba else C["tinta"])
            rr = pygame.Rect(ax, r.y + int(6 * s), im.get_width() + int(14 * s), im.get_height() + int(6 * s))
            pygame.draw.rect(self.tela, C["cobre"] if i == aba else C["papel2"], rr, border_radius=int(3 * s))
            self.tela.blit(im, (rr.x + int(7 * s), rr.y + int(3 * s)))
            self.rects_abas.append(rr)
            ax = rr.right + int(5 * s)
        f = self.f["peq"]
        quebradas = []
        for t, cor in self._linhas_caderno(aba):
            for q in (quebrar(t, f, r.w - int(24 * s)) if t else [""]):
                quebradas.append((q, cor))
        y0 = r.y + int(26 * s)
        vis = int((r.bottom - int(16 * s) - y0) // f.get_linesize())
        self.scroll = max(0, min(self.scroll, max(0, len(quebradas) - vis)))
        y = y0
        for q, cor in quebradas[self.scroll:self.scroll + vis]:
            self.tela.blit(f.render(q, True, cor), (x, y))
            y += f.get_linesize()
        self.texto("←/→ trocar aba · ↑↓ rolar · C ou ESC fechar", "peq", C["cobre"], r.centerx,
                   r.bottom - int(11 * s), centro=True, sombra=False)

    def desenhar_toque(self):
        base = (34, LH - 50)
        for nome, (dx, dy), seta in (("cima", (0, -16), "▲"), ("baixo", (0, 16), "▼"),
                                     ("esquerda", (-16, 0), "◀"), ("direita", (16, 0), "▶")):
            r = self.RR(base[0] + dx - 8, base[1] + dy - 8, 16, 16)
            pygame.draw.rect(self.tela, C["card2"], r, border_radius=int(3 * self.s))
            self.texto(seta, "corpo_b", C["texto"], r.centerx, r.y + int(3 * self.s), centro=True, sombra=False)
            self.botoes_ui[nome] = r
        r = self.RR(LW - 50, LH - 64, 30, 30)
        pygame.draw.ellipse(self.tela, C["ambar"], r)
        self.texto("E", "h1", C["tinta"], r.centerx, r.y + int(7 * self.s), centro=True, sombra=False)
        self.botoes_ui["E"] = r
        rp = self.RR(LW - 46, LH - 88, 22, 16)
        pygame.draw.rect(self.tela, C["card2"], rp, border_radius=int(3 * self.s))
        pygame.draw.rect(self.tela, C["ambar"], rp, 1, border_radius=int(3 * self.s))
        self.texto("II", "corpo_b", C["texto"], rp.centerx, rp.y + int(3 * self.s), centro=True, sombra=False)
        self.botoes_ui["Pausa"] = rp


# ---------------------------------------------------------------- utilidades
DIAS_SEMANA = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]


def texto_relogio(dt):
    return f"{DIAS_SEMANA[dt.weekday()]} {dt.strftime('%d/%m/%Y · %H:%M')}"


def voz_de(eid):
    """Timbre da 'voz' de cada personagem enquanto o texto aparece."""
    if eid in ("helena", "sofia", "olivia", "rodrigo", "max"):
        return "voz_" + eid
    if eid.startswith("aluna"):
        return "voz_aluna"
    return "voz_estudante"


def titulo_rank(pts, venceu):
    if not venceu:
        return "Afastada do caso"
    if pts >= 1050:
        return "Lenda da Perícia"
    if pts >= 800:
        return "Detetive Brilhante"
    if pts >= 550:
        return "Investigadora Competente"
    return "Detetive Novata"


def _arq_recordes():
    try:
        pasta = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        pasta = os.getcwd()
    return [os.path.join(pasta, "recordes_tudo_em_seu_lugar.json"),
            os.path.join(os.path.expanduser("~"), "recordes_tudo_em_seu_lugar.json")]


def ler_recordes():
    for c in _arq_recordes():
        try:
            with open(c, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            continue
    return []


def _arq_save():
    return [p.replace("recordes_", "save_") for p in _arq_recordes()]


def _cod(o):
    """JSON não conhece set/tuple/datetime/Random: marca cada tipo para voltar igual."""
    if isinstance(o, set):
        return {"__set": [_cod(x) for x in sorted(o, key=repr)]}
    if isinstance(o, tuple):
        return {"__tup": [_cod(x) for x in o]}
    if isinstance(o, datetime.datetime):
        return {"__dt": o.isoformat()}
    if isinstance(o, random.Random):
        return {"__rng": _cod(o.getstate())}
    if isinstance(o, dict):
        if all(isinstance(k, str) for k in o):
            return {k: _cod(v) for k, v in o.items()}
        return {"__dict": [[_cod(k), _cod(v)] for k, v in o.items()]}
    if isinstance(o, list):
        return [_cod(x) for x in o]
    return o


def _dec(o):
    if isinstance(o, list):
        return [_dec(x) for x in o]
    if isinstance(o, dict):
        if "__set" in o:
            return set(_dec(x) for x in o["__set"])
        if "__tup" in o:
            return tuple(_dec(x) for x in o["__tup"])
        if "__dt" in o:
            return datetime.datetime.fromisoformat(o["__dt"])
        if "__rng" in o:
            r = random.Random()
            r.setstate(_dec(o["__rng"]))
            return r
        if "__dict" in o:
            return {_dec(k): _dec(v) for k, v in o["__dict"]}
        return {k: _dec(v) for k, v in o.items()}
    return o


def gravar_save(estado):
    texto = json.dumps(_cod(estado), ensure_ascii=False)
    for c in _arq_save():
        try:
            with open(c, "w", encoding="utf-8") as fh:
                fh.write(texto)
            return True
        except OSError:
            continue
    return False


def ler_save():
    for c in _arq_save():
        try:
            with open(c, "r", encoding="utf-8") as fh:
                sv = _dec(json.load(fh))
            if isinstance(sv, dict) and sv.get("versao") == 1:
                return sv
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return None


def salvar_recorde(reg):
    dados = sorted(ler_recordes() + [reg], key=lambda r: -r["pontos"])[:10]
    for c in _arq_recordes():
        try:
            with open(c, "w", encoding="utf-8") as fh:
                json.dump(dados, fh, ensure_ascii=False, indent=1)
            return
        except OSError:
            continue


VOCAIS = {"grito", "grito_m", "susto", "ofego", "suspiro", "hm", "hm_m", "hein", "cochicho",
          "murmurio", "soluco"}
VARIANTES = {"passo": ["passo_0", "passo_1", "passo_2", "passo_3"],
             "passo_molhado": ["passo_molhado_1", "passo_molhado_2", "passo_molhado_3"]}


def _pasta_sons_extra():
    """Pasta opcional "sons" ao lado do jogo: um arquivo grito.ogg (ou .wav/.mp3) lá dentro
    substitui o som de mesmo nome. Serve para a equipe gravar as próprias vozes."""
    try:
        base = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base = os.getcwd()
    return os.path.join(base, "sons")


class SomPygame:
    """Efeitos GRAVADOS (CC0, embutidos) + trilhas originais geradas por Sintetizador."""

    def __init__(self):
        self.ligado = True
        self.ok = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)
            self.canal_amb = pygame.mixer.Channel(0)
            self.ok = True
        except Exception:
            self.ok = False
        self.pasta = os.path.join(tempfile.gettempdir(), f"tudo_em_seu_lugar_sons_{VERSAO_SOM}")
        self.extra = {}
        pe = _pasta_sons_extra()
        if os.path.isdir(pe):
            for arq in os.listdir(pe):
                nome, ext = os.path.splitext(arq)
                if ext.lower() in (".ogg", ".wav", ".mp3"):
                    self.extra[nome.lower()] = os.path.join(pe, arq)
        self.prontos = set()
        self.sons = {}
        self.desejada = None
        self.atual = None
        self.canal = None
        self.amb_atual = None
        self.molhado = False
        if self.ok:
            try:
                os.makedirs(self.pasta, exist_ok=True)
                threading.Thread(target=self._gerar, daemon=True).start()
            except OSError:
                self.ok = False

    def _arq(self, n):
        return os.path.join(self.pasta, n + ".wav")

    def _gerar(self):
        prioridade = [k for k in SFX if k.startswith("voz_")] + ["tema", "coracao"]
        ordem = prioridade + [k for k in SFX if k not in prioridade] + [k for k in MUSICAS if k not in prioridade]
        for nome in ordem:
            if nome in SONS_REAIS or nome in self.extra or nome in VOCAIS:
                continue   # já existe a versão gravada
            try:
                cam = self._arq(nome)
                if not (os.path.exists(cam) and os.path.getsize(cam) > 500):
                    if nome in SFX:
                        dur, fn, vol = SFX[nome]
                        s = Sintetizador(dur, SR_SFX)
                    else:
                        dur, fn, vol = MUSICAS[nome]
                        s = Sintetizador(dur, SR_MUSICA)
                    fn(s)
                    s.salvar(cam + ".tmp", vol, 0.01 if nome in SFX else 0.25)
                    os.replace(cam + ".tmp", cam)
                self.prontos.add(nome)
            except Exception:
                continue

    def _snd(self, n):
        if n in self.sons:
            return self.sons[n]
        s = None
        try:
            if n in self.extra:
                s = pygame.mixer.Sound(self.extra[n])
            elif n in SONS_REAIS:
                s = pygame.mixer.Sound(file=io.BytesIO(base64.b64decode("".join(SONS_REAIS[n]))))
            elif n in self.prontos:
                s = pygame.mixer.Sound(self._arq(n))
        except Exception:
            s = None
        if s is not None:
            self.sons[n] = s
        return s

    def sfx(self, n):
        if not (self.ok and self.ligado):
            return
        if n == "passo" and self.molhado:
            n = "passo_molhado"
        if n in VARIANTES:
            n = random.choice(VARIANTES[n])
        s = self._snd(n)
        if s:
            s.play()

    def ambiente(self, n, volume=1.0):
        """Som de fundo contínuo (chuva) num canal só dele; None desliga."""
        if not self.ok:
            return
        if not self.ligado:
            n = None
        if n != self.amb_atual:
            self.canal_amb.fadeout(600)
            self.amb_atual = None
            if n:
                s = self._snd(n)
                if s:
                    self.canal_amb.play(s, loops=-1, fade_ms=900)
                    self.amb_atual = n
        if self.amb_atual:
            self.canal_amb.set_volume(volume)

    def musica(self, n):
        self.desejada = n
        if not (self.ok and self.ligado) or n == self.atual:
            return
        s = self._snd(n)
        if not s:
            return
        if self.canal:
            self.canal.fadeout(700)
        self.canal = s.play(loops=-1, fade_ms=1200)
        self.atual = n

    def atualizar(self):
        if self.ok and self.ligado and self.desejada and self.desejada != self.atual:
            self.musica(self.desejada)

    def alternar(self):
        self.ligado = not self.ligado
        if not self.ligado:
            if self.ok:
                pygame.mixer.stop()
            self.atual = None
            self.canal = None
            self.amb_atual = None
        return self.ligado

    def parar(self):
        try:
            pygame.mixer.stop()
        except Exception:
            pass


def main():
    Jogo().executar()
