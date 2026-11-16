# Rhythm Striker: estudo de direção do trailer 2

Arquivo final: `trailer_rhythm_striker_2.mp4` (1280x720, 60 fps, até 60 s).
Tudo o que aparece é o jogo rodando de verdade. Não há vídeo gravado da tela: o renderizador roda as fases sem janela, com um "robô" apertando o botão no tempo das partituras, e grava cada quadro.

---

## 1. Diagnóstico do trailer 1

| O que o trailer 1 fazia | Problema |
|---|---|
| Abria com 6 s de texto sobre o bosque parado | O espectador decide nos 3 primeiros segundos, e eles não tinham ação. |
| Mostrava três blocos de 11 s, um por mundo | O ritmo era uniforme, sem escalada: o trailer não acelerava junto com o jogo. |
| Legendas longas numa faixa escura | A leitura competia com a jogabilidade. |
| Câmera fixa (a câmera do próprio jogo) | Não havia nenhuma ênfase nos acertos, nos drops ou nas falhas. |
| Não tinha conflito | Leo nunca errava, então não havia nada em jogo. |
| Terminava na cauda silenciosa da música | O final morria em vez de bater. |

## 2. Conceito

**"O mundo acelera com a música."** O próprio jogo já sobe de 84 para 110 e depois para 150 BPM, de mundo em mundo. O trailer copia essa curva: cada bloco é mais curto e mais rápido que o anterior, até uma montagem de cortes que se atropelam, um tropeço, e o drop final.

Estrutura clássica de trailer em cinco tempos:

1. **Gancho** (cold open). Um pedaço do clímax, sem explicação.
2. **Premissa e título.** Quem é Leo e o que aconteceu, em duas frases.
3. **Escalada.** Os três mundos, cada um mais rápido.
4. **Crise.** O erro custa caro: congelamento e silêncio.
5. **Clímax e assinatura.** O drop da Cidadela, a nota S e o logo.

## 3. Regras de direção

1. **Cortar só no tempo forte.** Todo corte cai no início de um compasso (ou de meio compasso, ou de um tempo, quando a montagem aperta) da música que está tocando. A imagem e o som nunca saem do pulso.
2. **Cada mundo leva a sua música.** O Bosque toca "Cruising", as Ilhas tocam "Castle" e a Cidadela toca "Ark". Os pulos de Leo caem nas batidas porque a fase *é* a música.
3. **Edição de áudio alinhada ao compasso.** Quando a cena e a música precisam de trechos diferentes da mesma faixa (no final, por exemplo), o som é trocado por outro compasso inteiro da mesma faixa. Como a grade é a mesma, os pulos continuam em cima da batida.
4. **Texto curto e cinético.** No máximo cinco palavras por cartela, entrando com um "pop" na batida e saindo antes da próxima. Sem faixa escura por cima do jogo.
5. **Câmera de trailer por cima da câmera do jogo:**
   - *punch-in*: um zoom rápido de 1,0x para 1,12x centrado em Leo nos acertos PERFEITO e nos drops;
   - *tranco*: o tremor do próprio jogo (`cam.sacudir`) e mais um tremor da imagem inteira nos impactos;
   - *flash* branco de 3 a 5 quadros na entrada de cada drop;
   - *letterbox* (faixas pretas, formato 2,39:1) no gancho e na premissa: é "cinema" até o título, e depois as faixas se abrem e vira "jogo".
6. **Glitch como transição.** A arte do jogo já usa o glitch, nos cacos e na história de Leo sendo puxado para dentro da tela. Os cortes entre mundos usam uma separação RGB com fatias deslocadas, de 4 a 6 quadros.
7. **Som de trailer sintetizado** (numpy, nenhum arquivo de terceiros):
   - *riser* (ruído que sobe com uma senoide em glissando) antes de cada drop;
   - *boom* (senoide caindo de 110 para 38 Hz, com estalo) no título, no drop final e no logo;
   - *whoosh* nos cortes da montagem;
   - *tape stop* (a música desacelera até parar) no erro;
   - batida de coração no cartão escuro da crise;
   - *ticks* de máquina de escrever na premissa.
8. **Silêncio é contraste.** Dois cortes secos para o preto: depois do gancho e depois do erro. O drop seguinte bate mais forte porque veio do nada.

## 4. Mapa da música (energia medida por compasso)

| Faixa | BPM | Compasso | Momentos usados (em batidas da fase) |
|---|---|---|---|
| Cruising (Bosque) | 84,105 | 2,85 s | 8–12: introdução sob o logo · 12: o grave entra · 140: A' · 196–204: o final da faixa |
| Castle (Ilhas) | 110 | 2,18 s | 28–32: subida · **32: drop 1** · 160: drop 2 |
| Ark (Cidadela) | 150 | 1,60 s | 56–64: construção · **64: drop 1** · 100: A cheio · **224: drop final** · 320: a última pancada |

## 5. Roteiro de planos

`t` é o tempo do vídeo, já conferido no render final (o renderizador calcula cada corte em quadros a partir dos compassos). Duração final: **59,3 s**.

| # | t (s) | Duração | Imagem | Som | Texto | Câmera / efeito |
|---|---|---|---|---|---|---|
| 0 | 0,0 | 0,8 | Preto | *riser* curto | | letterbox |
| 1 | 0,8 | 2 compassos | **Cidadela, drop final (batida 224)** | Ark a partir da batida 224 | | flash e tranco no 1º quadro, *push-in* lento de 1,0x para 1,08x, letterbox |
| 2 | 4,0 | 3,4 | Preto com chuvisco e glitch | *boom* no corte, música cortada seco, *ticks*, *glitch* | "LEO JOGAVA DE MADRUGADA..." e depois "...ATE A TELA O PUXAR." | o texto treme e se parte em RGB na segunda frase |
| 3 | 7,4 | 4 batidas | **Logo** sobre o Bosque | *boom* e flash; Cruising, introdução (8–12) | "UM BOTAO. NO RITMO." | as faixas do letterbox se abrem |
| 4 | 10,3 | 2 compassos | **Bosque**, batidas 12–20 | Cruising, o grave entrando | "PULE" / "NA BATIDA" (um por compasso) | *punch-in* no 1º PERFEITO |
| 5 | 16,0 | 4 compassos | **Ilhas**, batidas 28–44 | Castle, 1 compasso de subida e o drop | "110 BPM" no drop, depois "O MUNDO ACELERA" | glitch na entrada, flash e tranco na batida 32 |
| 6 | 24,7 | 1 → ½ → ¼ de compasso | **Montagem**: Bosque A', Ilhas drop 2, Cidadela A, depois Ilhas, Cidadela, Ilhas, Cidadela em cortes cada vez menores | cada corte com a sua faixa no tempo, *whoosh* nas emendas | | glitch em cada corte; os planos encurtam: aceleração pura |
| 7 | 34,2 | 1 compasso + congelamento + cartão | **Cidadela: Leo erra** e bate num caco | Ark, depois *tape stop* no impacto, depois silêncio e o coração | "ERROU A BATIDA?" sobre o quadro congelado; no preto, "O RITMO NAO PERDOA." | o quadro congela, perde a cor e dá um zoom; flash vermelho |
| 8 | 39,0 | 2 + 3 compassos | **Cidadela**, construção (56–64) e o **drop 1 (64)** | Ark com o *riser* por cima, *boom* no drop | "CIDADELA DO ECLIPSE" na construção e "150 BPM" no drop | flash, tranco, *punch-ins* nos tempos fortes |
| 9 | 47,0 | até o carimbo | **Final da Cidadela**: FASE COMPLETA e o **carimbo S** | Ark a partir da batida 320: o corte cai na última pancada da faixa, e a cauda segue sob a vitória | | sem efeito: deixar a vitória respirar |
| 10 | 54,1 | 5,2 | **Logo** e créditos | *boom*; Cruising 196–204, o final da faixa (o Bosque fecha o que abriu) | "3 MUNDOS. 3 MUSICAS. 1 BOTAO." e os créditos | escurece até o preto no fim |

## 6. Por que essa ordem funciona

- **O gancho vem do fim.** O espectador vê primeiro o momento mais intenso do jogo, sem contexto. A pergunta ("o que é isso?") é respondida pela premissa, e o mesmo mundo só volta no clímax, quando ele já entende o que está em jogo.
- **A escalada é física.** Os planos duram 5,7 s no Bosque, 8,7 s nas Ilhas (que crescem até o drop), depois 2,9 / 2,2 / 1,6 / 1,1 / 0,8 / 0,5 / 0,4 s na montagem. O BPM sobe junto: 84 → 110 → 150.
- **A crise quebra a curva no ponto mais rápido.** Depois da montagem mais apertada vem o tropeço, o congelamento e o silêncio. O contraste máximo prepara o drop.
- **O final rima com o começo.** A Cidadela que abriu o trailer agora é vencida (nota S), e o Bosque, onde tudo começou, fecha o trailer com o fim da própria faixa.

## 7. Créditos obrigatórios na tela final

- Músicas: Dosi & Aisake ("Cruising"), Clarx & Harddope ("Castle"), Ship Wrek & Zookeepers ("Ark")
- *Music provided by NoCopyrightSounds* (ncs.io)
- Feito com Power PPlay 2.0 (IC-UFF)
- Personagem: Ozzbit Games, "male_hero" (gratuito)

## 8. Verificação depois de renderizar

- [x] Duração ≤ 60 s: 59,3 s.
- [x] Folha de contato com um quadro por plano: cada plano mostra o que o roteiro diz.
- [x] Nenhum trecho mudo fora do planejado: só 0,5 s no cartão da crise (plano 7); o plano 2 ganhou um zumbido de CRT por baixo.
- [x] Pico de áudio ≤ −1 dBFS: −1,5 dBFS de pico verdadeiro, −14,2 LUFS integrado (o alvo das plataformas de vídeo).
- [x] Os pulos caem na batida em todos os mundos (conferir na montagem, onde as emendas são mais rápidas).
