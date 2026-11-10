# Game Design Document — Rhythm Striker

*Versão atualizada com o estado atual do jogo (novembro de 2026).*

## 1. Nome do Projeto

**Rhythm Striker** — jogo de plataforma rítmico 2D para PC, desenvolvido em Python
sobre a biblioteca **Power PPlay 2.0** (IC-UFF) e o **pygame-ce**, por uma equipe de
2 pessoas. Single-player, com **3 fases** e cerca de **7 minutos** de
jogo (de 2min10s a 2min30s por fase).

Para rodar:

```
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python main.py
```

## 2. High Concept

Rhythm Striker é um jogo de plataforma 2D de rolagem lateral em que o jogador foi
teleportado para uma dimensão feita de som e só consegue avançar se pular na batida das
músicas. O Léo corre sozinho para a direita, na velocidade da música, e o jogador só
decide **quando** pular. A fase é escrita como uma partitura: cada obstáculo fica onde
um pulo na batida certa passa por cima dele.

O diferencial é que, diferente de jogos em que um erro manda o jogador de volta para o
começo, aqui há **três corações**, e errar o tempo de um pulo custa apenas pontos. Ao
fim de cada fase, o jogador recebe uma **nota (S, A, B ou C)** e sabe se jogou bem ou mal.

## 3. Gameplay e Enredo

### Enredo

Léo joga videogame de madrugada e é teleportado da sua casa no exato momento em que
aperta o botão de START. Ele é sugado para dentro da tela e cai em **Rhythm Kingdom**,
uma dimensão alternativa que abriga os sons mais sinistros e viciantes do universo, que
não são reconhecidos como música, e onde quem se move fora do compasso vira ruído e
desaparece. Para voltar para casa, ele precisa atravessar três mundos pulando em cima
da batida. O elenco é mínimo: o Léo e o mundo que ele precisa superar para ver sua
família novamente.

### Controles

| Tecla | Ação |
|---|---|
| ESPAÇO / SETA CIMA / W / clique | a única ação do jogo: o pulo |
| ESC | pausa (ao continuar, há uma contagem de 3 batidas antes de a música voltar) |
| R | recomeça a fase |
| F11 | alterna entre tela cheia e janela |
| Setas + ENTER | navegam pelos menus (o mouse também funciona) |

A fase abre parada, com o Léo de pé na largada, e só começa (música e física juntas)
quando o jogador aperta ESPAÇO. Esse primeiro toque não conta como pulo.

### O pulo

O tempo que o botão fica apertado decide a **altura** do pulo: um toque rápido dá um
pulo baixo, e segurar até o alto do arco dá o pulo inteiro. Os dois pousam no mesmo
lugar, na batida seguinte, e os dois passam por todos os obstáculos: nenhum obstáculo
exige o botão segurado. Segurando além do pouso, o Léo pula de novo a cada pouso.

O pulo é travado no ritmo: um toque dado com o Léo ainda no ar fica guardado (até 0,7
batida antes do pouso) e o pulo sai no pouso, sem atrasar os pulos seguintes. Há
também uma pequena tolerância (40 ms) para pular depois de sair da beirada.

### Julgamento e pontuação

Cada ação exigida pela partitura é julgada pela distância entre o toque e a batida:

| Julgamento | Janela | Pontos |
|---|---|---|
| **PERFEITO!** | até 0,10 batida | 50 |
| **BOM!** | até 0,20 batida | 25 |
| **ERROU...** | a janela passou sem toque | 0 |

As janelas são medidas em fração da batida, então ficam mais curtas nas músicas mais
rápidas. Elas são propositalmente largas por causa da latência de áudio do Pygame: a
maior janela BOM ainda é uma em que o pulo passa por cima de todos os obstáculos.
Acertos seguidos formam uma **sequência (combo)**. Tocar fora da partitura não pune.

### Vidas e derrota

- **Errar o tempo custa apenas pontos**, nunca um coração.
- Um coração se perde **batendo em alguma coisa**: num caco (espinho de ruído), num
  bloco solto (que se quebra com a batida) ou na parede de um degrau. Depois de uma
  batida, o Léo fica 1,5 batida invulnerável, piscando.
- **Cair num fosso é o fim na hora.**
- Com os três corações perdidos vem o **fim de jogo**: o Léo se desfaz em ruído.
- Chegando ao fim da música, a fase está completa e a tela de resultado mostra a nota.

### Obstáculos

As fases são montadas por um construtor rítmico que traduz uma partitura de batidas em
geometria. O vocabulário de cada passo da partitura é:

| Passo | O que aparece | Exige pulo? |
|---|---|---|
| caco | espinho de ruído (1, 2 ou 3 pontas) no meio do arco | sim |
| torre | bloco solto de 1 tile no caminho | sim |
| vão | fosso no meio do arco | sim |
| ilha | fosso cuja outra margem fica mais alta ou mais baixa | sim |
| sobe | degrau de 1 tile para cima | sim |
| desce | degrau para baixo | não |
| pausa | chão plano | não |

Nas Ilhas Suspensas há também **portais de velocidade**: o portal dourado acelera a
corrida no drop da música e o azul a devolve à velocidade normal.

### As três fases

Cada fase é construída sobre uma música, com a estrutura **introdução, parte A,
parte B e repetição variada da parte A (A')**. O mundo acelera junto com a música, e o
pulo dura sempre uma batida.

| # | Fase | Dificuldade | BPM | Ações | Duração | Música |
|---|---|---|---|---|---|---|
| 1 | Bosque dos Ecos | Fácil | 84 | 73 | 2min30s | "Cruising", Dosi & Aisake |
| 2 | Ilhas Suspensas | Normal | 110 | 205 | 2min18s | "Castle", Clarx & Harddope |
| 3 | Cidadela do Eclipse | Difícil | 150 | 225 | 2min11s | "Ark", Ship Wrek & Zookeepers |

- **Bosque dos Ecos** é a fase que ensina: tudo se passa só com toques rápidos (o pulo
  é sempre o inteiro e segurar o botão não faz nada) e **guias** mostram onde pular. É a
  única fase com guias: dali em diante o cenário e a música dizem a hora.
- **Ilhas Suspensas** é uma corrida de pedra em pedra entre ilhas flutuantes, com os
  portais de velocidade e ritmos pontuados.
- **Cidadela do Eclipse** é a fase final, com muralhas, ameias, escadas, fossos em fila e
  a torre de menagem, até o portal que leva o Léo de volta para casa.

Todas as fases são validadas por um robô (`ferramentas/validar_fases.py`) que joga com a
física real do jogo, com toques perfeitos, sempre adiantados, sempre atrasados e
sorteados dentro da janela BOM, e confirma que nenhum deles leva dano.

## 4. Interface de Usuário

O HUD é mínimo, porque em jogo de ritmo o olhar fica à frente do personagem:

- **Canto superior esquerdo:** os três corações (o último cheio pulsa na batida) e o
  nome da fase.
- **Canto superior direito:** a pontuação e, a partir de 3 acertos seguidos, o combo.
- **Centro:** o julgamento da última ação (PERFEITO!, BOM! ou ERROU...) e os pontos
  ganhos, que entram ampliados e somem em menos de um segundo.
- **Rodapé:** a progressão no mapa, numa barra com o rostinho do Léo andando por ela
  e a porcentagem ao lado.

Enquanto a fase espera a largada, o nome da fase, a dificuldade e os créditos da música
aparecem no alto da tela e somem quando a música entra.

O jogo tem as seguintes telas:

1. **Menu principal:** logo, JOGAR e SAIR.
2. **Seleção de fase:** três cartas, cada uma na moldura do seu mundo, com uma amostra
   do cenário, o emblema da fase, a dificuldade, a medalha da melhor nota, o melhor
   progresso, o recorde de pontos e a música. O fundo da tela muda para o mundo da
   carta escolhida.
3. **Gameplay**, com o menu de **pausa** (continuar, recomeçar, menu de fases).
4. **Resultado:** nota, precisão, pontuação, aviso de novo recorde, quantidade de
   PERFEITO, BOM e ERROU e a maior sequência, com os botões jogar de novo, próxima fase
   e menu de fases.
5. **Fim de jogo:** fase, progresso alcançado e pontuação, com tentar de novo, menu de
   fases e menu principal.

A nota vem da **precisão**, que é a pontuação dividida pela pontuação máxima da fase:
**S** a partir de 95%, **A** a partir de 85%, **B** a partir de 70% e **C** abaixo disso.

Os recordes de cada fase (melhor progresso, maior pontuação, melhor nota e se foi
completada) ficam salvos em `savegame.json`, e um recorde nunca piora.

Os menus não têm animação própria. A troca entre telas é suave: a tela escurece, troca
e clareia de novo. Os textos usam uma única fonte pixelada, a **Silkscreen** (licença
SIL OFL), sem suavização. Painéis, botões, molduras, corações, letreiros de julgamento,
medalhas de nota e o logo são imagens em pixel art. O jogo é desenhado em 1280x720,
abre em tela cheia e é ampliado sem suavizar para qualquer monitor.

## 5. Áudio e Música

Cada fase tem uma trilha única, todas da **NCS (NoCopyrightSounds)**, de licença livre,
escolhidas por serem dinâmicas, eletrônicas e com BPM constante e bem marcado:

| Fase | Faixa | Artista | BPM |
|---|---|---|---|
| Bosque dos Ecos | Cruising | Dosi & Aisake | 84,105 (lo-fi, a mais calma) |
| Ilhas Suspensas | Castle | Clarx & Harddope | 110 |
| Cidadela do Eclipse | Ark | Ship Wrek & Zookeepers | 150 (sombria e épica) |

A fase entra num compasso escolhido de cada faixa para que as partes da música (o drop,
a quebra) coincidam com as partes da fase. Os créditos aparecem na largada, na tela de
seleção e na tela de resultado.

Há **efeitos sonoros** próprios para o pulo, o acerto PERFEITO, o acerto BOM, o erro, o
bloco quebrando, a vitória, a morte, o clique e a navegação nos menus. Na pausa, a
contagem de volta toca um tique a cada número.

## 6. Arte Conceito e Referências

A direção de arte é **pixel art** sobre fundos escuros e coloridos. Cada mundo tem a sua
paleta própria, e as peças de jogo são tingidas com ela. A regra de leitura continua:
o que machuca é pontiagudo e na cor de perigo do mundo, o chão seguro é sólido e
contínuo, e o cenário de fundo fica afastado e menos contrastado.

- **Personagem:** o Léo vem da folha de sprites gratuita *Male Hero* da **Ozzbit Games**
  (parado, corrida e pulo). Também existe um Léo desenhado para o jogo
  (`assets/art/personagens/`), que pode ser ligado em `jogo/config.py`.
- **Cenário:** um céu em degradê com sol, lua ou eclipse, estrelas e duas camadas de
  morros, árvores, ilhas ou torres em parallax. Ele é desenhado em 320x180 e ampliado
  4x para ficar pixelado.

  | Mundo | Fundo | Chão |
  |---|---|---|
  | Bosque | lua cheia e estrelas | caminho de lajes com musgo sobre terra, com árvores e moitas |
  | Ilhas | sol baixo e nuvens | ilhas de pedra flutuando, com linha de cristal no topo e ruínas de colunas |
  | Cidadela | sol eclipsado com coroa de luz | alvenaria, com colunas |

- **Peças de jogo:** cacos de 1, 2 e 3 pontas, bloco, portal e colunas em PNG. O que
  ainda não tem imagem continua desenhado por código.
- **Efeitos:** poeira no pulo e no pouso, faíscas a cada acerto, o ar de cada mundo
  (vaga-lumes no bosque, poeira de luz nas ilhas, fagulhas no eclipse), vento depois do
  portal rápido, tremor de câmera nas batidas e a morte do Léo, que se desfaz em ruído.

São cerca de **90 imagens** (`ferramentas/conferir_arte.py` lista 92 prontas e 7 ainda
desenhadas por código), organizadas em `assets/art/` (veja `assets/art/LEIAME.md`).
`ferramentas/importar_arte.py` recorta, reduz e recolore a arte crua.

As referências principais são **Geometry Dash**, pela fase como corrida sincronizada,
pela leitura visual do cenário em alta velocidade e pelo progresso em porcentagem, e
**Rhythm Heaven**, por ensinar ritmo através de antecipação em vez de tutorial em texto
(as guias só existem na primeira fase).

## 7. Mudanças em relação ao GDD original

| Item | Planejado | Como está |
|---|---|---|
| Fases | 5 fases, cerca de 12 minutos | 3 fases, cerca de 7 minutos |
| BPM | ~90-100, ~105-110 e "acima do normal" | 84, 110 e 150 |
| Errar o tempo | custava um coração | custa só os pontos; o coração se perde ao bater num obstáculo |
| Fosso | — | morte imediata |
| Pulo | pulo simples (com pulo duplo como extra) | pulo de altura variável (toque = baixo, segurado = inteiro) |
| Personagens | Léo, Eco, Estática e Metrônomo | só o Léo; os obstáculos são cacos, blocos, fossos e degraus |
| Ponte de eco | — | testada e removida (as imagens ficaram guardadas) |
| Portais de velocidade | — | adicionados nas Ilhas Suspensas |
| Telas | menu, seleção, gameplay, resultado e game over | as mesmas, mais o menu de pausa com contagem |
| Visual | formas geométricas com contorno luminoso, ciano/magenta fixos, ~20 imagens, tudo com retângulos e círculos | pixel art com uma paleta por mundo e cerca de 90 imagens |
| Efeitos sonoros | acerto perfeito, erro e pulo | os mesmos, mais acerto bom, quebra, vitória, morte e menus |
| Tutorial | ensinar por antecipação | guias visuais só na primeira fase |
| Recordes | — | salvos em `savegame.json` |
| Tecnologia | Python e Pygame | Python, pygame-ce e Power PPlay 2.0 |
