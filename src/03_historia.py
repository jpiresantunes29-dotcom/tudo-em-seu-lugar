
# =========================================================================
# 1b) MODO HISTÓRIA — capítulos, salas, pistas e sorteios
# =========================================================================

# ---- Linha do tempo do caso -------------------------------------------
# Crime: ter 03/02/2026 às 22:45 (durante o baile). Corpo achado às 23:58.
# A promotoria dá 48 horas a partir do crime: o prazo é qui 05/02/2026, 22:45.
# O relógio da cena anda com cada ação; as "horas" do HUD são o que falta até o prazo.
PRAZO = datetime.datetime(2026, 2, 5, 22, 45)
INICIO_INVESTIGACAO = datetime.datetime(2026, 2, 4, 0, 6)
HORAS_INICIAIS = int((PRAZO - INICIO_INVESTIGACAO).total_seconds() // 3600)   # 46h
CUSTO_MIN = {"examinar": 30, "interrogar": 45, "conversar": 10, "viajar": 45, "chuva": 30,
             "entrevista": 60, "imprensa": 60}
# Marcos da história: o relógio nunca volta, só pula para frente nestes momentos
MARCOS = {
    "prologo": datetime.datetime(2026, 2, 3, 23, 40),
    "porta": datetime.datetime(2026, 2, 3, 23, 58),
    "ligacao": datetime.datetime(2026, 2, 4, 0, 6),
    "convocacao": datetime.datetime(2026, 2, 4, 10, 0),   # cap. 4: alunas convocadas pela manhã
    "noite_casa": datetime.datetime(2026, 2, 4, 19, 30),  # cap. 5: Rodrigo leva Helena à casa
}


def fmt_min(m):
    return f"{m} min" if m < 60 else (f"{m // 60}h" + (f"{m % 60:02d}" if m % 60 else ""))

CAPITULOS = {
    0: "Prólogo — O baile",
    1: "Capítulo 1 — O chamado",
    2: "Capítulo 2 — A cena do crime",
    3: "Capítulo 3 — O passado da Tulane",
    4: "Capítulo 4 — A quinta aluna",
    5: "Capítulo 5 — A casa do professor",
    6: "Capítulo 6 — Tudo em seu lugar",
}

# Pistas obrigatórias de cada capítulo (para avançar a história)
OBJETIVOS = {
    1: ["telefone"],
    2: ["corpo", "faca", "cam_baile", "sofia", "olivia"],
    3: ["cam_univ", "terra", "livro"],
    4: ["interrogatorios", "entrevista"],
    5: ["celular", "max"],
    6: ["comparacao", "acusacao"],
}

NOMES_SALAS = {
    "escritorio": "Escritório de Helena",
    "salao": "Salão do Baile de Formatura",
    "banheiro_baile": "Banheiro do Baile",
    "tulane": "Tulane University",
    "banheiro_tulane": "Banheiro da Tulane University",
    "interrogatorio": "Sala de Interrogatório",
    "casa": "Casa de Augusto Nakamura",
}
# Quando cada local do mapa da cidade fica disponível
LIBERA_SALA = {"escritorio": 1, "salao": 1, "tulane": 3, "banheiro_tulane": 3,
               "interrogatorio": 4, "casa": 5}
SALAS_MAPA = ["escritorio", "salao", "tulane", "banheiro_tulane", "interrogatorio", "casa"]

# Os três pontos de investigação de cada local (mesmos nomes dos slides)
PONTOS_SALA = {
    "salao": ["Mesas do banquete", "Palco e cabine do DJ", "Lixeiras perto da saída"],
    "banheiro_baile": ["Corpo do professor", "Pias e espelhos", "Câmera do corredor"],
    "tulane": ["Arquivo de registros", "Mural de intercâmbio", "Jardim e área de terra"],
    "banheiro_tulane": ["Câmera externa", "Vegetação nos fundos", "Corredor de serviço"],
    "interrogatorio": ["Computador do caso", "Quadro de evidências", "Arquivo da delegacia"],
    "casa": ["Escritório do professor", "Quintal do Max", "Quarto"],
}

# Onde cada pista pode aparecer (sorteado por partida, sempre no capítulo certo)
PISTAS = {
    "corpo":      [("banheiro_baile", 0)],
    "faca":       [("banheiro_baile", 1)],          # a arma fica na cena do crime
    "cam_baile":  [("banheiro_baile", 2)],
    "cam_univ":   [("banheiro_tulane", 0), ("banheiro_tulane", 2)],
    "terra":      [("banheiro_tulane", 1), ("tulane", 2)],
    "livro":      [("tulane", 0), ("tulane", 1)],
    "celular":    [("casa", 0), ("casa", 2)],
    "max":        [("casa", 1)],
    "computador": [("interrogatorio", 0)],
}
PISTAS_PRINCIPAIS = list(PISTAS.keys())

PISTAS_FALSAS = [
    ("Luvas de látex", "Um par de luvas descartado. Etiqueta do buffet: eram dos garçons.",
     [("salao", 2), ("salao", 0), ("banheiro_baile", 1)]),
    ("Taça quebrada", "Uma taça de champanhe quebrada. Só um brinde mais animado.",
     [("salao", 0), ("salao", 1), ("banheiro_baile", 1)]),
    ("Convite nunca entregue", "Um convite da formatura esquecido numa mesa. Nada de especial.",
     [("salao", 1), ("casa", 0), ("casa", 2), ("tulane", 1)]),
    ("Broche da turma", "Um broche \"Arquitetura 2026\". Dezenas de alunos usavam um igual.",
     [("salao", 1), ("salao", 2), ("tulane", 2)]),
    ("Recibo do buffet", "Recibo do jantar, pago pela coordenação. Nada suspeito.",
     [("salao", 2), ("interrogatorio", 1), ("interrogatorio", 2)]),
    ("Folheto de intercâmbio", "Um folheto antigo de intercâmbio para a Itália, esquecido. Nada que ligue ao crime.",
     [("tulane", 1), ("tulane", 0), ("interrogatorio", 1)]),
    ("Bitucas de cigarro", "Bitucas antigas. O corredor era usado pelos funcionários da limpeza.",
     [("banheiro_tulane", 0), ("banheiro_tulane", 2), ("banheiro_tulane", 1)]),
    ("Relatório da 1ª perícia", "O relatório da polícia que ninguém conseguiu decifrar. Muitas perguntas, nenhuma resposta.",
     [("interrogatorio", 1), ("interrogatorio", 2)]),
]

VAZIOS = [
    "Você procura com cuidado, mas não encontra nada útil.",
    "Nada fora do lugar aqui. Tudo em seu lugar… por enquanto.",
    "Só poeira e silêncio. Uma hora a menos.",
    "Nada que mude o caso.",
]

EVENTOS = [
    ("imprensa", "Repórteres cercam você. Perde 1 hora despistando as câmeras de TV.", -1, 0),
    ("cafe", "Rodrigo resolve a papelada por você: a próxima viagem não gasta tempo.", 0, 0),
    ("chuva", "Chuva forte em Nova Orleans: a próxima viagem levará 30 minutos a mais.", 0, 0),
    ("acesso", "Olívia libera seu acesso total: o próximo exame não gasta horas.", 0, 0),
    ("anonimo", "Ligação anônima: \"O professor não era quem parecia.\" (+10 pontos)", 0, 10),
]

PONTOS = {
    "pista": 50, "conversa": 15, "falsa": 5, "dica": -30,
    "acusacao_errada": -150, "sem_provas": -60, "motivo_errado": -60,
    "acerto": 300, "por_hora": 10,
    "liberar_certo": 20,
}


class Caso:
    """Sorteia e guarda o estado de uma partida do modo história."""

    def __init__(self, codigo=None):
        self.codigo = codigo if codigo is not None else random.randint(1000, 9999)
        rng = random.Random(self.codigo)
        self.rng = rng
        self.helena = {k: rng.choice(v[1]) for k, v in TRACOS.items()}
        cams = rng.sample(["altura", "acessorio", "calcado"], 3)
        self.revela_cam_baile = cams[:2]
        self.revela_computador = cams[2]
        nomes = rng.sample(NOMES_RUIVAS, 4)
        alibis = rng.sample(ALIBIS, 4)
        cores_cabelo = rng.sample(["#c0612f", "#a8432a", "#d07445", "#9e4a28", "#b5542b"], 4)
        cores_roupa = rng.sample(["#4b5d3a", "#5a3d5c", "#3d4f6b", "#6b4a32", "#2f5a5a", "#5c2f35"], 4)
        self.alunas = []
        for i, nome in enumerate(nomes):
            tr = {k: rng.choice(v[1]) for k, v in TRACOS.items()}
            modo = "alibi" if rng.random() < 0.35 else "traco"
            cat = None
            if modo == "traco":
                cat = rng.choice(list(TRACOS.keys()))
                tr[cat] = rng.choice([x for x in TRACOS[cat][1] if x != self.helena[cat]])
            self.alunas.append({
                "id": f"aluna{i+1}", "nome": nome, "idade": rng.randint(23, 26), "tracos": tr,
                "modo": modo, "traco_diferente": cat, "alibi": alibis[i],
                "ocupacao": rng.choice(OCUPACOES), "interrogada": False,
                "cabelo": cores_cabelo[i], "roupa": cores_roupa[i],
            })
        self.sofia_alibi = rng.choice([
            "às 22:45 dançava com a turma no meio do salão, na frente de todo mundo",
            "às 22:45 organizava a foto oficial da turma com o fotógrafo",
        ])
        self.mapa = {}
        for pid in PISTAS_PRINCIPAIS:
            livres = [p for p in PISTAS[pid] if p not in self.mapa]
            self.mapa[rng.choice(livres)] = ("pista", pid)
        falsas = PISTAS_FALSAS[:]
        rng.shuffle(falsas)
        for titulo, texto, onde in falsas:
            livres = [p for p in onde if p not in self.mapa]
            if livres:
                self.mapa[rng.choice(livres)] = ("falsa", (titulo, texto))

        self.cap = 0
        self.sala = "salao"
        self.viagem_gratis = False
        self.pontos = 0
        self.credibilidade = CREDIBILIDADE_INICIAL
        self.props = []
        self.feitos = set()        # pistas e conversas obrigatórias concluídas
        self.pistas = set()
        self.examinados = set()
        self.conversas = set()
        self.tracos_conhecidos = set()
        self.descartes = set()
        self.dicas = 0
        self.erros = 0
        self.acoes = 0
        self.chuva = False
        self.exame_gratis = False
        self.inicio = time.time()
        self.evento_som = None
        self.relogio = MARCOS["prologo"]   # data e hora da cena

    def ganhar(self, *letras):
        novas = [l for l in letras if l not in self.props]
        self.props.extend(novas)
        return novas

    def aluna(self, aid):
        return next(a for a in self.alunas if a["id"] == aid)

    # "horas" = tempo que falta até o prazo da promotoria (derivado do relógio da cena)
    @property
    def horas(self):
        return max(0, int((PRAZO - self.relogio).total_seconds() // 3600))

    @horas.setter
    def horas(self, h):
        self.relogio = PRAZO - datetime.timedelta(hours=h)

    def gastar(self, minutos):
        """Avança o relógio da cena (cada ação leva um tempo realista)."""
        self.acoes += 1
        self.relogio += datetime.timedelta(minutes=minutos)

    def marco(self, nome):
        """Pula o relógio para um momento da história (nunca volta no tempo)."""
        if self.relogio < MARCOS[nome]:
            self.relogio = MARCOS[nome]

    def sortear_evento(self):
        if self.rng.random() < 0.15:
            nome, txt, dh, dp = self.rng.choice(EVENTOS)
            self.evento_som = nome
            self.pontos += dp
            if nome == "imprensa":
                self.relogio += datetime.timedelta(minutes=CUSTO_MIN["imprensa"])
            if nome == "cafe":
                self.viagem_gratis = True
            if nome == "chuva":
                self.chuva = True
                self.chuva_ate = self.relogio + datetime.timedelta(hours=3)
            if nome == "acesso":
                self.exame_gratis = True
            return txt
        return None

    def chovendo(self):
        """Chove na madrugada da Tulane (cap. 3) e por 3 horas depois do evento de chuva forte."""
        ate = getattr(self, "chuva_ate", None)
        return self.cap == 3 or (ate is not None and self.relogio < ate)

    def todas_interrogadas(self):
        return all(a["interrogada"] for a in self.alunas)

    def provas_suficientes(self):
        return "AE" in self.props and ("AG" in self.props or "AI" in self.props)

    def capitulo_completo(self):
        return all(x in self.feitos for x in OBJETIVOS.get(self.cap, []))

    def sala_liberada(self, sala):
        if sala == "salao" and "telefone" not in self.feitos:
            return False
        return self.cap >= LIBERA_SALA.get(sala, 99)


# =========================================================================
# 1c) FICHAS DOS ITENS E LOCAIS (o que o enunciado pede nos slides:
#     itens — quem usa, quando, para quê; locais — quem esteve onde e quando)
# =========================================================================
# item: (nome, quem usou, quando, para quê, pista que o revela)
FICHAS_ITENS = {
    "faca": ("Faca do assassinato",
             lambda c: "Helena Cortez." if "acusacao" in c.feitos else
             "A assassina — uma mulher ruiva, ainda sem nome.",
             "Ter, 03/02/2026, às 22:45, no banheiro do baile.",
             "Golpear o professor Nakamura no coração. Depois foi jogada atrás das pias.", "faca"),
    "celular": ("Celular de Beatriz",
                lambda c: "Beatriz, até 01/05/2020. Depois, o professor Nakamura.",
                "De maio de 2020 até a morte do professor.",
                "Mandar mensagens fingindo que Beatriz ainda estava viva e encobrir o desaparecimento.", "celular"),
    "livro": ("Livro de registros de 2020",
              lambda c: "Os policiais Olívia e Rodrigo e a detetive Helena.",
              "Madrugada de qua, 04/02/2026, no arquivo da Tulane.",
              "Encontrar as cinco alunas ruivas compatíveis com a testemunha de 2020.", "livro"),
    "cam_univ": ("Câmeras dos banheiros da Universidade",
                 lambda c: "Segurança da Tulane; as imagens foram analisadas por Olívia e Rodrigo, com Helena.",
                 "Gravações de anos antes, incluindo sex, 01/05/2020.",
                 "Mostrar Nakamura chantageando alunas, o assassinato de Beatriz e a testemunha ruiva.", "cam_univ"),
    "cam_baile": ("Câmeras do banheiro do Baile",
                  lambda c: "Segurança do salão; analisadas por Helena e Rodrigo.",
                  "Ter, 03/02/2026, das 22:41 às 22:47.",
                  "Mostrar a mulher ruiva que entrou depois do professor e saiu sozinha.", "cam_baile"),
    "computador": ("Computador do caso",
                   lambda c: "Policial Rodrigo e policial Olívia.",
                   "Na Sala de Interrogatório, em 04/02/2026.",
                   lambda c: ("Comparar as gravações: a assassina é compatível com Helena Cortez."
                              if "comparacao" in c.feitos else
                              "Ampliar as gravações do baile e revelar detalhes da assassina."), "computador"),
}

# local: lista de (quem esteve onde e quando, condição para aparecer)
FICHAS_LOCAIS = {
    "salao": [("Ter, 03/02/2026, das 20h à meia-noite: formandos de Arquitetura, Sofia e o "
               "professor Nakamura.", None),
              ("O professor saiu do salão pouco antes das 22:41, rumo ao banheiro.", "cam_baile"),
              ("Às 22:45, Sofia estava diante de testemunhas (álibi confirmado).", "sofia"),
              ("De madrugada: Helena chega, chamada por Sofia.", "telefone")],
    "banheiro_baile": [("22:41: o professor entra; logo depois, uma mulher ruiva.", "cam_baile"),
                       ("22:45: o crime. 22:47: a mulher ruiva sai sozinha e tranca a porta.", "cam_baile"),
                       ("23:58: os alunos forçam a porta e encontram o corpo.", None),
                       ("23:59: os policiais Olívia e Rodrigo isolam a cena. De madrugada, Helena investiga.", "olivia")],
    "tulane": [("2020: Beatriz Valença, Helena Cortez e o professor Nakamura estavam no curso de "
                "Arquitetura.", "livro"),
               ("Madrugada de qua, 04/02/2026: Helena, Olívia e Rodrigo investigam o arquivo e o campus.", None),
               ("Arquivo: registros dos alunos de 2020, analisados pela polícia.", "livro"),
               ("Maio de 2020: o corpo de Beatriz foi enterrado no campus.", "terra")],
    "banheiro_tulane": [("Anos antes de 2026: o professor chantageava e arrastava alunas para cá.", "cam_univ"),
                        ("Sex, 01/05/2020: o professor, Beatriz (assassinada) e uma testemunha ruiva.", "cam_univ"),
                        ("A testemunha ruiva era Helena Cortez.", "entrevista")],
    "interrogatorio": [("Qua, 04/02/2026, de manhã: Olívia e Rodrigo interrogam as quatro alunas ruivas.", "c4"),
                       ("Em seguida, a entrevista da quinta aluna: Helena Cortez.", "entrevista"),
                       ("Rodrigo compara as gravações no computador do caso.", "comparacao")],
    "casa": [("Moravam ali o professor Nakamura e o cachorro Max.", None),
             ("Qua, 04/02/2026, à noite: Rodrigo leva Helena até a casa.", "AF"),
             ("Antes do crime, Helena tinha estado ali muitas vezes — Max a reconhece.", "max")],
}
LOCAIS_SLIDES = ["salao", "banheiro_baile", "tulane", "banheiro_tulane", "interrogatorio", "casa"]
