# Requisitos do trabalho × jogo

Como *Tudo em seu Lugar* atende ao enunciado do **Projeto DETETIVE (RA2)** e à
**rubrica de avaliação por pares** do jogo.

## Enunciado: requisitos do jogo em Python

| Requisito | Onde está no jogo |
|---|---|
| Mesmo tema e história dos slides | Personagens, locais, itens e acontecimentos seguem o caso da equipe; o caderno mostra as proposições A–AM dos slides. |
| Aleatoriedade | A cada partida são sorteados nomes, idades, profissões e álibis das 4 suspeitas ruivas, os traços da assassina nas câmeras, o lugar das pistas, as pistas falsas e os eventos. O *código do caso* repete uma partida. |
| Pontuação com ganhos e perdas | Pistas, conversas e acertos dão pontos; dicas, acusações erradas, acusar sem provas e errar o motivo tiram. |
| Decisões do jogador | Arriscar a acusação a qualquer momento (X), pedir dica (H), liberar ou acusar cada suspeita, escolher o motivo, escolher a ordem de investigação. |
| Tela final explícita | Vitória ou derrota, com pontuação, título, proposições descobertas, horas restantes, dicas usadas, acusações erradas, tempo de jogo e código do caso. |

## Rubrica de avaliação por pares

| Critério (peso) | Como o jogo atende |
|---|---|
| **Coerência com o tema (1,5)** | História em 7 capítulos fiel ao caso dos slides; fichas de cada item e local com quem usou, quando e para quê. |
| **Randomização (2,0)** | Sorteios por partida (ver acima), preservando a coerência entre culpada, vítima, pistas e desfecho. A tela final informa o que foi sorteado. |
| **Sistema de dicas (1,5)** | Dicas em dois níveis para cada tarefa pendente: uma pergunta para fazer pensar e, se pedir de novo, o caminho exato. Nunca revelam a culpada. |
| **Interatividade (2,0)** | Decisões com consequência em pontos, tempo e credibilidade; quadro de suspeitas com descarte; acusação com o perfil da assassina ao lado de cada suspeita (✓ bate / ✗ não bate). |
| **Criatividade (1,0)** | O jogador monta hipóteses comparando traços e álibis; caderno liga a investigação às proposições e às regras de inferência. |
| **Funcionamento (1,0)** | Um único arquivo `.py`; instala o pygame sozinho se faltar; testado automaticamente do início ao fim em várias resoluções. |
| **Pontuação (1,0)** | Placar, avisos a cada ação, credibilidade, tela final com estatísticas e recordes salvos. |
