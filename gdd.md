Game Design Document — Rhythm Striker
1. Nome do Projeto
Rhythm Striker — jogo de plataforma rítmico 2D para PC, desenvolvido em Python com
Pygame por uma equipe de 2 pessoas, em 12 semanas. Single-player, com 5 fases e cerca
de 12 minutos de jogo.
2. High Concept
Rhythm Striker é um jogo de plataforma 2D de rolagem lateral em que o jogador foi
teleportado para uma dimensão feita de som e só consegue avançar se pular na batida das
músicas. O cenário irá se mover ao longo da música, e o jogador deve pular de acordo com
o ritmo da música. O diferencial seria que, diferente de jogos tradicionais em que o jogador
tem apenas uma tentativa para completar completamente as fases, o jogador terá um
sistema de vidas, e de acordo com o timing de seus pulos, ele pode acumular pontuações e
entender se performou bem ou mal ao completar a fase.
3. Gameplay e Enredo
Léo joga videogame de madrugada quando ele é teleportado da sua casa no exato
momento em que ele aperta o botão de START. Ele é sugado para dentro da tela e cai em
Rhythm Kingdom, uma dimensão alternativa onde abriga os sons mais sinistros e viciantes
do universo, não sendo reconhecidos como música, onde quem se move fora do compasso
vira ruído e desaparece.
O jogo terá um foco absoluto, o jogador pular (Espaço) nos momentos certos, dentro da
janela da batida. Acertar dentro do tempo ideal vale o Perfeito! e 50 pontos; até um pouco
antes ou depois, vale Bom! e 25 pontos; fora disso é Erro!, que custa um dos corações e o
jogador não ganha nenhuma pontuação. As janelas são propositalmente largas porque a
latência de áudio do Pygame não permite ser rigoroso.
São 3 fases, cada uma construída sobre uma música: A inicial, com batidas leves, para o
jogador se habituar na jogabilidade, cerca de 90/100 BPM. A intermediária, mais
desafiadora, testando as habilidades ganhas desde sua primeira interação com o mundo,
com cerca de 105/110 BPM, e a fase Final, onde o jogador é testado ao seu limite, com um
número de batidas por minuto acima do normal, para que Léo consiga, de uma vez por
todas, voltar para sua casa. Cada fase é montada sobre uma grade rítmica em que a
estrutura possua sua introdução, parte A, parte B e repetição variada da parte A — o
reaproveitamento é intencional e dobra a duração da fase. O elenco é mínimo: Léo, e o
mundo que ele precisa superar para ver sua família novamente.
4. Interface de Usuário
O HUD é mínimo, porque em jogo de ritmo o olhar fica à frente do personagem. No canto
superior esquerdo ficam a relação da vida do personagem, sua quantidade; no superior
direito, a sua pontuação. No centro da tela aparece o julgamento da última ação (Perfeito!,
Bom! ou Errou…), junto com a pontuação ganha, sumindo em alguns segundos. No rodapé
fica a progressão do personagem no mapa, se ele está começando, terminando ou no
processo, sendo indicado juntamente com uma porcentagem.
O jogo tem cinco telas no total: menu, seleção de fase, gameplay e resultado (mais um
game over). A tela de resultado mostra a nota da fase (S acima de 95% de precisão, A
acima de 85%, B acima de 70%, C abaixo), de acordo com a pontuação total. Tudo é
desenhado com retângulos, círculos e uma única fonte, sem animações de menu.
5. Áudio e Música
As trilhas serão selecionadas de acordo com o a fase do jogo, sendo cada uma única,
sendo que cada faixa será selecionada dentro daqueles que possuem suas licenças livres,
sem direitos autorais, com o critério de serem dinâmicas, com BPM constante e previsível,
bem marcadas e com duração de um minuto e meio a 2 minutos e meio. O jogo deve cobrir
no mínimo 3 músicas, uma fácil, uma média e uma difícil, focadas no gênero eletrônico. O
jogo também haverá efeitos sonoros próprios para cada tipo de acerto, como o acerto
perfeito, o erro e os pulos.
6. Arte Conceito e Referências
A direção de arte é de formas geométricas simples com contorno luminoso sobre fundo
escuro — escolha tanto estética quanto prática, por ser a única que dois estudantes
conseguem produzir com qualidade consistente no prazo. A regra de leitura nunca é
quebrada: plataforma segura é sempre ciano e retangular, perigo é sempre magenta e
pontiagudo, o jogador é branco com brilho, o fundo é roxo escuro e o cenário decorativo é
desaturado. Como forma e cor comunicam a mesma informação, o jogo já fica legível para
daltónicos sem custo extra. O total de assets é de cerca de vinte imagens pequenas: quatro
sprites de Léo, dois do Eco, três da Estática, um do Metrônomo, três variações de
plataforma, cinco fundos e os ícones de HUD.
As referências principais são Geometry Dash, pela fase como corrida sincronizada e pela
leitura visual do cenário em alta velocidade e pela indicação do progresso em porcentagem
e Rhythm Heaven, por ensinar ritmo através de antecipação em vez de tutorial em texto.
7. Ideias Adicionais e Observações
O desenvolvimento do nosso jogo será focado em entregar a base de forma sólida e
jogável, de modo que a gameplay seja satisfatória pelo número de mapas e seu
aproveitamento, sendo uma das nossas possíveis dificuldades o desenvolvimento de
cenários do jogo propriamente dito. Mas caso seja possivel, pensamos em adicionar novos
detalhes, como animações adicionais, melhorias de design, e ajustes dentro de features,
como o pulo duplo.

