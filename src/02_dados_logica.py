# =========================================================================
# 1) DADOS DO CASO  (tudo que vem dos slides fica aqui — fácil de atualizar)
# =========================================================================

TITULO = "TUDO EM SEU LUGAR"
SUBTITULO = "Projeto Detetive — Resolução de Problemas com Lógica Matemática"
EQUIPE = ("Eduardo Yonegura Hashimoto · Guilherme Sakagami Spitzner · "
          "João Pedro Pires Antunes · Letícia Beatriz Silva de Morais")

CREDIBILIDADE_INICIAL = 3

# --- Proposições atômicas (slides 13–16) ---------------------------------
PROPOSICOES = {
    "A": "O professor Augusto Nakamura foi encontrado morto.",
    "B": "O professor Augusto Nakamura estava no banheiro da festa.",
    "C": "O crime ocorreu em 3 de fevereiro de 2026.",
    "D": "O crime ocorreu durante o baile de formatura de Arquitetura da Tulane University.",
    "E": "Sofia Mori Nakamura é sobrinha do professor Augusto Nakamura.",
    "F": "Sofia Mori Nakamura contratou a detetive Helena Cortez.",
    "G": "Helena Cortez investigou o caso.",
    "H": "Helena Cortez foi aluna de Arquitetura na Tulane University em 2020.",
    "I": "Helena Cortez mudou para perícia criminal em 2021.",
    "J": "Helena Cortez teve aulas com o professor Augusto Nakamura.",
    "K": "O professor Augusto Nakamura era conhecido por Helena Cortez.",
    "L": "O professor Augusto Nakamura foi esfaqueado no coração.",
    "M": "O corpo do professor Augusto Nakamura foi trancado no banheiro até o fim da festa.",
    "N": "Imagens de segurança das redondezas dos banheiros da Tulane University de 6 anos atrás mostraram o professor Nakamura chantageando alunas.",
    "O": "O professor Nakamura arrastava alunas para as redondezas dos banheiros.",
    "P": "Beatriz Valença era aluna de Arquitetura.",
    "Q": "Beatriz Valença era amiga de Sofia Mori Nakamura.",
    "R": "Beatriz Valença tinha uma passagem marcada para intercâmbio na Itália.",
    "S": "Beatriz Valença ficaria na Itália por alguns meses.",
    "T": "Beatriz Valença foi assassinada pelo professor Nakamura em 1 de maio de 2020.",
    "U": "O corpo de Beatriz Valença foi enterrado no campus da universidade.",
    "V": "O professor Nakamura permaneceu com o celular de Beatriz Valença.",
    "W": "O professor Nakamura encobriu o desaparecimento de Beatriz Valença.",
    "X": "Uma aluna ruiva apareceu nas imagens de segurança como testemunha do crime de 2020.",
    "Y": "A testemunha ruiva foi ameaçada pelo professor Nakamura.",
    "Z": "A polícia analisou os registros de alunos de 2020.",
    "AA": "A polícia encontrou cinco alunas compatíveis com a testemunha ruiva.",
    "AB": "As quatro primeiras alunas interrogadas tinham relação com o crime.",
    "AC": "Helena Cortez era a quinta aluna dos registros.",
    "AD": "Helena Cortez sofria de Amnésia Dissociativa.",
    "AE": "Helena Cortez presenciou o assassinato de Beatriz Valença em 2020.",
    "AF": "O policial Rodrigo levou Helena Cortez à casa de Augusto Nakamura.",
    "AG": "O cachorro Max reconheceu Helena Cortez na casa de Augusto Nakamura.",
    "AH": "O cachorro Max latiu incansavelmente para Helena Cortez.",
    "AI": "As câmeras de segurança do baile mostraram que a assassina era compatível com as características de Helena.",
    "AJ": "A assassina do professor Nakamura era Helena Cortez.",
    "AK": "Helena Cortez cometeu o assassinato para se vingar da morte de Beatriz Valença.",
    "AL": "O caso foi solucionado.",
    "AM": "Helena Cortez foi absolvida devido à sua condição de saúde mental.",
}
# Proposições que o jogo registra como NEGADAS (aparecem com ¬ no caderno)
NEGADAS = {"AB"}

CONCLUSAO_SIMBOLICA = "AJ ∧ AL ∧ AM"
CONCLUSAO_TEXTO = ("A assassina do professor Augusto Nakamura era Helena Cortez, "
                   "o caso foi solucionado e Helena Cortez foi absolvida devido "
                   "à sua condição de saúde mental.")

REGRAS = ["Modus Ponens", "Modus Tollens", "Simplificação", "Conjunção",
          "Adição", "Silogismo Hipotético", "Silogismo Disjuntivo",
          "Dilema Construtivo", "Contraposição", "Bicondicional"]

REGRAS_EXPLICADAS = {
    "Modus Ponens": "p → q , p  ∴  q",
    "Modus Tollens": "p → q , ¬q  ∴  ¬p",
    "Simplificação": "p ∧ q  ∴  p",
    "Conjunção": "p , q  ∴  p ∧ q",
    "Adição": "p  ∴  p ∨ q",
    "Silogismo Hipotético": "p → q , q → r  ∴  p → r",
    "Silogismo Disjuntivo": "p ∨ q , ¬p  ∴  q",
    "Dilema Construtivo": "p → q , r → s , p ∨ r  ∴  q ∨ s",
    "Contraposição": "p → q  ≡  ¬q → ¬p",
    "Bicondicional": "p ↔ q  ≡  (p → q) ∧ (q → p)",
}

# --- Personagens (slides 4–7) — a descrição traz as habilidades -----------
PERSONAGENS = {
    "helena": ("Detetive Helena Cortez",
               "Ruiva de 23 anos. Trancou Arquitetura em 2020 e iniciou perícia "
               "criminal em 2021. Corajosa, determinada e detalhista. É você."),
    "nakamura": ("Prof. Augusto Nakamura",
                 "Coordenador de Arquitetura da Tulane. Agressivo e ameaçador; "
                 "assediava e chantageava alunas em segredo. Dono do cachorro Max."),
    "sofia": ("Sofia Mori Nakamura",
              "Estudante de Arquitetura, sobrinha do professor e amiga de Beatriz. "
              "Determinada, contratou você por conhecê-la da faculdade."),
    "beatriz": ("Beatriz Valença",
                "Estudante de Arquitetura e amiga de Sofia. Todos achavam que ela "
                "estava em intercâmbio na Itália desde 1º de maio de 2020."),
    "olivia": ("Policial Olívia",
               "Interroga as estudantes ruivas e faz a pergunta decisiva. "
               "Atenta a cada reação de quem está na sua frente."),
    "rodrigo": ("Policial Rodrigo",
                "Parceiro de Olívia. Leva Helena à casa do professor esperando "
                "despertar memórias. Bom com as gravações das câmeras."),
    "max": ("Cachorro Max",
            "Cão do professor. Fareja e late para quem já esteve na casa — "
            "reconhece cheiros que as pessoas esqueceram."),
    "ruivas": ("As alunas ruivas de 2020",
               "Estudantes encontradas nos registros de 2020, convocadas para "
               "interrogatório por serem compatíveis com a testemunha ruiva."),
}


# --- Elementos sorteados a cada partida ------------------------------------
NOMES_RUIVAS = ["Clara Monteiro", "Ashley Brooks", "Marina Duarte", "Emily Carter",
                "Giovanna Reis", "Megan O'Connor", "Laura Fontaine", "Isabela Prado",
                "Chloe Bennett", "Valentina Rocha", "Rachel Moore", "Lívia Castanho",
                "Hannah Whitaker", "Natália Brandão", "Paige Sullivan", "Bianca Lacerda"]

TRACOS = {
    "altura": ("Altura", ["1,60 m", "1,65 m", "1,70 m", "1,75 m"]),
    "mao": ("Mão dominante", ["canhota", "destra"]),
    "acessorio": ("Acessório", ["relógio dourado", "pulseira de couro", "anel de prata", "brinco de argola"]),
    "calcado": ("Calçado", ["bota preta", "tênis branco", "sapatilha vermelha", "salto preto"]),
}

ALIBIS = [
    "às 22:45 estava no palco recebendo a homenagem da turma — aparece em todas as fotos oficiais",
    "às 22:45 estava na pista de dança; o vídeo do DJ mostra ela sem sair de lá",
    "às 22:45 estava no estacionamento ajudando um amigo passando mal — a câmera da entrada confirma",
    "às 22:45 estava na mesa de doces conversando com três professores, que confirmam",
    "às 22:45 estava em uma chamada de vídeo com a família, registrada no celular",
]

OCUPACOES = ["hoje é arquiteta em Baton Rouge", "faz mestrado em urbanismo",
             "trabalha em um escritório de restauro", "mudou para design de interiores",
             "é professora de desenho técnico", "trabalha com paisagismo"]

MOTIVOS = [
    ("vinganca", "Vingança pela morte de Beatriz Valença"),
    ("heranca", "Herança da família Nakamura"),
    ("nota", "Reprovação no Trabalho de Conclusão"),
    ("ciume", "Ciúmes de um relacionamento"),
]


# Design system "Nova Orleans Noturna" — extraído das ilustrações dos personagens:
# noite azul-petróleo, luz âmbar de luminária, azul de distintivo/viatura,
# cobre do cabelo de Helena e papel envelhecido dos arquivos do caso.
COR = {
    "bg": "#0e1417",        # noite (fundo dominante das ilustrações)
    "barra": "#0a0f12",     # HUD e navegação
    "card": "#172026",      # superfície
    "card2": "#1f2b33",     # superfície elevada / hover
    "linha": "#2e4a5b",     # contorno azul-petróleo
    "texto": "#e9e4d8",
    "fraco": "#8fa0a8",     # cinza-azulado
    "ambar": "#d8a76b",     # luz de luminária — ação principal
    "ambar2": "#e9c08a",
    "azul": "#3578c8",      # distintivo / viatura — informação
    "azul2": "#58a5e0",
    "azulfundo": "#13263a",
    "cobre": "#b85a30",     # cabelo de Helena — perigo / acusação
    "cobre2": "#d07445",
    "cobrefundo": "#2a1810",
    "papel": "#e4d7ba",     # documentos e pistas
    "papel2": "#d2c29e",
    "tinta": "#182026",
    "verde": "#7db28a",
}

